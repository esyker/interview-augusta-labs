from fastapi import FastAPI, HTTPException, Query
from typing import List, Dict, Optional
import wikipediaapi
import random
import time

app = FastAPI()

# Simulated database for articles and feedback
articles_db = {}
feedback_db = {}

# Wikipedia API initialization
wiki = wikipediaapi.Wikipedia('pt')

def fetch_latest_wikipedia_articles(limit=10000) -> List[Dict]:
    # Simulate fetching the latest 10,000 Portuguese articles from Wikipedia
    # The actual fetching can use scraping or an API wrapper for Wikipedia
    articles = [{"id": i, "title": f"Article {i}", "content": f"Content for article {i}"} for i in range(limit)]
    return articles

def generate_tldr(article_content: str, user_interests: str) -> str:
    # Simulated TLDR generator (should be replaced with an actual NLP-based summary)
    return article_content[:300] + "..."

def find_relevant_articles(user_interests: str) -> List[Dict]:
    # Fetch articles and simulate relevance matching
    latest_articles = fetch_latest_wikipedia_articles()
    relevant_articles = random.sample(latest_articles, 10)  # Simulated random relevance for demo purposes
    return relevant_articles

@app.post("/search/")
def search_articles(user_interests: str, feedback: Optional[Dict[int, str]] = None):
    start_time = time.time()

    # Find relevant articles
    relevant_articles = find_relevant_articles(user_interests)
    
    # Apply feedback loop (if any feedback exists)
    if feedback:
        # Simulate refining based on feedback
        refined_articles = [article for article in relevant_articles if feedback.get(article["id"]) == "thumbs_up"]
        if refined_articles:
            relevant_articles = refined_articles
    
    # Generate TLDR for each article
    results = []
    for article in relevant_articles:
        tldr = generate_tldr(article["content"], user_interests)
        results.append({
            "title": article["title"],
            "tldr": tldr,
            "url": f"https://pt.wikipedia.org/wiki/{article['title'].replace(' ', '_')}"
        })
    
    # Check if the process takes less than 1 minute
    elapsed_time = time.time() - start_time
    if elapsed_time > 60:
        raise HTTPException(status_code=408, detail="The request took too long to process")
    
    return {"results": results, "processing_time": elapsed_time}

@app.post("/feedback/")
def submit_feedback(article_id: int, feedback: str):
    # Simulate storing feedback (thumbs_up/thumbs_down)
    feedback_db[article_id] = feedback
    return {"message": "Feedback recorded"}

# Example GET endpoint to retrieve all feedback
@app.get("/feedback/")
def get_feedback():
    return feedback_db

