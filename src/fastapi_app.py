from fastapi import FastAPI, Query
from typing import List, Optional
from config import Config
from utils.scrapper_wikipedia import ScrapperWikipedia
from utils.chunking_models import ChunkingModel
from utils.index import Index
from utils.typedefs import ArticleInfo, Article, ArticleChunk, QueryScoresVectors, SearchResult, SearchResultsGroupedByDoc

app = FastAPI()

config = Config()

# Define API endpoints

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

@app.post("/index/fit", response_model=Index)
def index_fit(docs: List[ArticleChunk]):
    """Fit an index with the provided article chunks."""
    return config.index.fit(docs=docs)

@app.get("/index/search", response_model=List[SearchResult])
def index_search(
    query: str = Query(..., description="Search query"),
    num_results: int = Query(config.SEARCH_RESULTS_LIMIT, description="Number of results to return")
):
    """Search the index with a given query."""
    return config.index.search(query, boost_dict={}, num_results=num_results)

@app.get("/index/search_grouped_by_doc", response_model=List[SearchResultsGroupedByDoc])
def index_search_grouped_by_doc(
    query: str = Query(..., description="Search query"),
    num_results: int = Query(config.SEARCH_RESULTS_LIMIT, description="Number of results to return")
):
    """Search the index and group results by document."""
    return config.index.search_by_doc(query=query, boost_dict={}, num_results=num_results)

@app.post("/index/refined_search", response_model=List[SearchResultsGroupedByDoc])
def index_refined_search(
    search_results: List[SearchResultsGroupedByDoc],
    positive: List[str],
    negative: List[str]
):
    """Refine the search results based on positive and negative feedback."""
    return config.index.refine_search(
        search_results=search_results,
        positive=positive,
        negative=negative,
        alpha=config.SEARCH_REFINED_ALPHA,
        beta=config.SEARCH_REFINED_BETA,
        gamma=config.SEARCH_REFINED_GAMMA
    )

@app.get("/user/query_results", response_model=List[SearchResultsGroupedByDoc])
def user_get_query_results(
    query: str = Query(..., description="Search query"),
    top_k: int = Query(config.SEARCH_RESULTS_LIMIT, description="Number of results to return"),
    scrapping_total_limit: int = Query(config.SCRAPING_RESULTS_LIMIT, description="Limit for scraping articles")
):
    """Get refined query results by scraping articles, chunking them, and performing a search."""
    docs = config.wiki_search.get_last_pt_articles(total_limit=scrapping_total_limit)
    docs_chunks = config.wiki_search.get_articles_chunks(articles=docs, chunking_model=config.chunking_model)
    index = config.index.fit(docs=docs_chunks)
    search_docs = config.index.search_by_doc(query=query, boost_dict={}, num_results=top_k)
    return search_docs
