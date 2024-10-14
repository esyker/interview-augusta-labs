from fastapi import FastAPI, Query
from fastapi.responses import RedirectResponse
from fastapi import HTTPException, status
from typing import List, Optional
from config import Config
from utils.scrapper_wikipedia import ScrapperWikipedia
from utils.chunking_models import ChunkingModel
from utils.index import Index
from utils.typedefs import ArticleInfo, Article, ArticleChunk, QueryScoresVectors, SearchResult, SearchResultsGroupedByDoc, DisplaySearchResult

app = FastAPI()

config = Config()

# Define API endpoints
@app.get("/")
def redirect_to_docs():
    return RedirectResponse(url="/docs")

@app.get("/wikipedia/list_last_pt_articles", response_model=List[ArticleInfo])
def wikipedia_list_last_pt_articles(total_limit: int = Query(config.SCRAPING_RESULTS_LIMIT, description="Limit the number of results")):
    """Fetches the last Portuguese articles from Wikipedia."""
    return config.wiki_search.list_last_pt_articles(total_limit=total_limit)

@app.get("/wikipedia/get_last_pt_articles", response_model=List[Article])
def wikipedia_get_last_pt_articles(
    total_limit: int = Query(config.SCRAPING_RESULTS_LIMIT, description="Total articles to scrape"),
    requests_per_second: int = Query(config.SCRAPING_REQUESTS_PER_SECOND, description="Requests per second for scraping"),
    processing_type: str = Query(config.SCRAPING_TYPE, description="Type of processing to use"),
    verbose: bool = Query(config.VERBOSE, description="Enable verbose logging")
):
    """Fetches and scrapes the last Portuguese articles from Wikipedia."""
    return config.wiki_search.get_last_pt_articles(
        total_limit=total_limit,
        requests_per_second=requests_per_second,
        processing_type=processing_type,
        verbose=verbose
    )

@app.post("/wikipedia/article_chunks", response_model=List[ArticleChunk])
def wikipedia_get_article_chunks(articles: List[Article]):
    """Get article chunks from the provided list of articles."""
    return config.wiki_search.get_articles_chunks(articles=articles, chunking_model=config.chunking_model)

@app.get("/user/articles_chunks", response_model=List[ArticleChunk])
def user_articles_chunks(
    scrapping_total_limit: int = Query(config.SCRAPING_RESULTS_LIMIT, description="Total articles to scrape")
):
    """Fetches and scrapes articles and returns their chunks based on the user's query."""
    # Fetch the last Portuguese articles from Wikipedia
    docs = config.wiki_search.get_last_pt_articles(total_limit=scrapping_total_limit)
    
    # Get article chunks from the scraped articles
    docs_chunks = config.wiki_search.get_articles_chunks(articles=docs, chunking_model=config.chunking_model)
    
    return docs_chunks

def convert_search_results_to_display(response_model=List[SearchResultsGroupedByDoc])  -> List[DisplaySearchResult]:
    return [DisplaySearchResult(tldr = config.openai_model.get_tldr(user_query = _search_result.query,
                                    article_text = "\n".join(_section.text for _section in _search_result.article.sections)),
                                summary=_search_result.article.summary, 
                                url = _search_result.max_similarity_chunk.chunk.article_section.url,
                                weighted_similarity=_search_result.weighted_similarity) for _search_result in response_model]

@app.get("/user/query_refined", response_model=List[DisplaySearchResult])
def user_query_refined(
    top_k : int = Query(config.SEARCH_RESULTS_LIMIT, description="Number of search results to return"),
    positive: List[str] = Query([], description="List of positive terms to refine search"),
    negative: List[str] = Query([], description="List of negative terms to refine search")
):
    # Check if there is a previous search result
    if not config.last_search_result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Application error: No previous search found!"
        )
    
    
    search_docs = config.index.refine_search(
        search_results=config.last_search_result,
        positive=positive,
        negative=negative,
        top_k= top_k,
        alpha=config.SEARCH_REFINED_ALPHA,
        beta=config.SEARCH_REFINED_BETA,
        gamma=config.SEARCH_REFINED_GAMMA
    )
    config.last_search_result = search_docs
    return convert_search_results_to_display(search_docs)

@app.get("/user/query_results", response_model=List[DisplaySearchResult])
def user_query_results(
    query: str,
    top_k: int = Query(config.SEARCH_RESULTS_LIMIT, description="Number of search results to return"),
    scrapping_total_limit: int = Query(config.SCRAPING_RESULTS_LIMIT, description="Total articles to scrape"),
    reuse_index: bool = Query(True, description="Whether to reuse the existing index or rebuild it")
):
    """Fetches articles, chunks them, fits the index, and returns search results based on the user's query."""
    #Check if the index should be rebuilt
    if not reuse_index or len(config.index.docs)==0:
        # Fetch the last Portuguese articles from Wikipedia
        docs = config.wiki_search.get_last_pt_articles(total_limit=scrapping_total_limit,
                                                    requests_per_second=config.SCRAPING_REQUESTS_PER_SECOND,
                                                    processing_type=config.SCRAPING_TYPE,
                                                    verbose=config.VERBOSE)
        
        # Get article chunks from the scraped articles
        docs_chunks = config.wiki_search.get_articles_chunks(articles=docs, chunking_model=config.chunking_model)
        
        # Fit the index with the document chunks
        index = config.index.fit(docs=docs_chunks)
    # Perform the search using the provided query
    search_docs = config.index.search_by_doc(query=query, boost_dict={}, num_results=top_k)
    config.last_search_result = search_docs
    return convert_search_results_to_display(search_docs)






