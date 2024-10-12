from collections import defaultdict
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from typing import List, Dict
from .typedefs import ArticleChunk, SearchResult, SearchResultsGroupedByDoc, Article, QueryScoresVectors
from scipy import sparse

class Index:
    """
    A simple search index using TF-IDF and cosine similarity for text fields and exact matching for keyword fields.

    Attributes:
        text_fields (list): List of text field names to index.
        vectorizers (dict): Dictionary of TfidfVectorizer instances for each text field.
        text_matrices (dict): Dictionary of TF-IDF matrices for each text field.
        docs (list): List of documents indexed.
    """

    def __init__(self, text_fields : List[str], vectorizer_params={}):
        """
        Initializes the Index with specified text and keyword fields.

        Args:
            text_fields (list): List of text field names to index.
            keyword_fields (list): List of keyword field names to index.
            vectorizer_params (dict): Optional parameters to pass to TfidfVectorizer.
        """
        self.text_fields = text_fields

        self.vectorizers = {field: TfidfVectorizer(**vectorizer_params) for field in text_fields}
        self.text_matrices = {}
        self.docs = []

    def fit(self, docs : List[ArticleChunk]):
        """
        Fits the index with the provided documents.

        Args:
            docs (list of dict): List of documents to index. Each document is a dictionary.
        """
        self.docs = docs

        for field in self.text_fields:
            texts = [doc.get(field, '') for doc in docs]
            self.text_matrices[field] = self.vectorizers[field].fit_transform(texts)

        return self

    def query_to_vecs_scores(self, query:str, boost_dict :dict = {}, num_results : int =10) -> QueryScoresVectors:
        query_vecs = {field: self.vectorizers[field].transform([query]) for field in self.text_fields}
        scores = np.zeros(len(self.docs))

        # Compute cosine similarity for each text field and apply boost
        for field, query_vec in query_vecs.items():
            sim = cosine_similarity(query_vec, self.text_matrices[field]).flatten()
            boost = boost_dict.get(field, 1)
            scores += sim * boost

        num_results = min(num_results, len(self.docs))
        # Use argpartition to get top num_results indices
        top_indices = np.argpartition(scores, -num_results)[-num_results:]
        top_indices = top_indices[np.argsort(-scores[top_indices])]
        return QueryScoresVectors(query = query, query_vecs=query_vecs, scores=scores, top_indices=top_indices)

    def search(self, query : str, boost_dict : dict ={}, num_results : int = 10) -> List[SearchResult]:
        """
        Searches the index with the given query, filters, and boost parameters.

        Args:
            query (str): The search query string.
            boost_dict (dict): Dictionary of boost scores for text fields. Keys are field names and values are the boost scores.
            num_results (int): The number of top results to return. Defaults to 10.

        Returns:
            list of dict: List of documents matching the search criteria, ranked by relevance.
        """

        # Filter out zero-score results
        query_scores_vectors = self.query_to_vecs_scores(query=query, boost_dict=boost_dict, num_results=num_results)
        scores, top_indices = query_scores_vectors.scores, query_scores_vectors.top_indices
        top_docs = [SearchResult(query = query, similarity = scores[i], chunk = self.docs[i]) for i in top_indices] #if scores[i] > 0]
        return top_docs
    
    def group_search_results_by_doc(self, top_search_results: List[SearchResult]) -> List[SearchResultsGroupedByDoc]:
        query = top_search_results[0].query
        # Step 2: Group results by document using article.info.name
        grouped_results = defaultdict(list)
        for _search_result in top_search_results:
            doc_name = _search_result["chunk"]['article']['info']['name']
            grouped_results[doc_name].append(_search_result)

        # Step 3: Calculate mean, max, and 1/min similarities for each document
        grouped_doc_search_results = []
        for doc_name, doc_search_results_list in grouped_results.items():
            similarities = [_search_result["similarity"] for _search_result in doc_search_results_list]
            
            mean_similarity = np.mean(similarities)
            max_similarity = np.max(similarities)
            min_similarity = np.min(similarities) if similarities else 1e-6  # Avoid division by zero

            # Step 4: Compute weighted similarity (0.9 * max + 0.1 * mean)
            weighted_similarity = 0.9 * max_similarity + 0.1 * mean_similarity

            # Step 5: Find the chunk with the highest similarity (max_similarity)
            max_similarity_chunk = doc_search_results_list[np.argmax(similarities)]

            # Use chunks[0].article for the article, since all chunks have the same article
            result = SearchResultsGroupedByDoc(query=query,
                                mean_similarity=mean_similarity,
                                max_similarity=max_similarity,
                                min_similarity=min_similarity,
                                weighted_similarity=weighted_similarity,
                                article=doc_search_results_list[0]['chunk']['article'],
                                max_similarity_chunk=max_similarity_chunk,
                                search_results_list=doc_search_results_list)
            grouped_doc_search_results.append(result)

        # Step 6: Sort by weighted_similarity in descending order
        grouped_doc_search_results.sort(key=lambda x: x.weighted_similarity, reverse=True)
        return grouped_doc_search_results

    def search_by_doc(self, query: str, boost_dict={}, num_results=10) -> List[SearchResultsGroupedByDoc]:
        """
        Groups search results by document and calculates mean, max, and 1/min similarities.
        Applies weights (0.9 for max_similarity and 0.1 for mean_similarity) to rank results.

        Args:
            index (Index): The index instance used for searching.
            query (str): The search query string.
            boost_dict (dict): Optional dictionary of boost scores for fields.
            num_results (int): The number of top results to return. Defaults to 10.

        Returns:
            List[SearchResult]: List of search results grouped by document and ranked by similarity.
        """
        # Step 1: Call the search function to get top ArticleChunks
        top_search_results = self.search(query = query, boost_dict = boost_dict, num_results=len(self.docs))
        grouped_doc_search_results = self.group_search_results_by_doc(top_search_results=top_search_results)
        return grouped_doc_search_results[:num_results]
    
    def refine_search(self, search_results: List[SearchResultsGroupedByDoc],
                      positive: List[str], negative: List[str], alpha=0.8, beta=0.2, gamma=0.1) -> List[SearchResultsGroupedByDoc]:
        """
        Refines the search by adjusting the query based on positive and negative feedback.

        Args:
            search_results (List[SearchResultsGroupedByDoc]): The initial search results.
            positive (List[str]): List of document names marked as relevant.
            negative (List[str]): List of document names marked as irrelevant.
            alpha (float): Weight for the original query vector. Default is 0.8.
            beta (float): Weight for the positive feedback vector. Default is 0.2.
            gamma (float): Weight for the negative feedback vector. Default is 0.1.
            
        Returns:
            List[SearchResultsGroupedByDoc]: Updated search results based on feedback.
        """
        # Extract the original query vector
        query = search_results[0].query
        original_query_vecs = {field: self.vectorizers[field].transform([query]) for field in self.text_fields}

        # Initialize positive and negative vectors for each text field
        positive_vecs = {field: sparse.csr_matrix(original_query_vecs[field].shape) for field in self.text_fields}
        negative_vecs = {field: sparse.csr_matrix(original_query_vecs[field].shape) for field in self.text_fields}

        # Accumulate vectors for positive and negative feedback
        for search_result in search_results:
            doc_name = search_result.article.info.name
            
            if doc_name in positive:
                for field in self.text_fields:
                    pos_vec = self.vectorizers[field].transform([search_result.max_similarity_chunk.chunk.chunk_text])
                    positive_vecs[field] += pos_vec
                
            elif doc_name in negative:
                for field in self.text_fields:
                    neg_vec = self.vectorizers[field].transform([search_result.max_similarity_chunk.chunk.chunk_text])
                    negative_vecs[field] += neg_vec

        #Calculate the new query vector by combining original, positive, and negative feedback
        refined_query_vecs = {}
        for field in self.text_fields:
            refined_query_vecs[field] = (
                alpha * original_query_vecs[field] +
                beta * positive_vecs[field] -
                gamma * negative_vecs[field]
            )

        #Re-run the search using the updated query vector
        scores = np.zeros(len(self.docs))
        
        for field, query_vec in refined_query_vecs.items():
            sim = cosine_similarity(query_vec, self.text_matrices[field]).flatten()
            scores += sim

        num_results = min(len(self.docs), len(scores))
        top_indices = np.argpartition(scores, -num_results)[-num_results:]
        top_indices = top_indices[np.argsort(-scores[top_indices])]

        # Return updated search results grouped by document
        top_docs = [SearchResult(query = query, similarity=scores[i], chunk=self.docs[i]) for i in top_indices]# if scores[i] > 0]
        return self.group_search_results_by_doc(top_search_results=top_docs)