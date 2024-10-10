import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import time
from tqdm import tqdm
import wikipediaapi
import urllib.parse
from .typedefs import ArticleInfo, ArticleSection, Article, ArticleChunk
from .chunking_models import ChunkingModel

class ScrapperWikipedia:
    def __init__(self):
        pass

    def list_last_pt_articles(self, total_limit: int = 500) -> List[ArticleInfo]:
        """Lists the last articles."""
        search_results = []
        url = f"https://pt.wikipedia.org/w/index.php?title=Especial:P%C3%A1ginas_novas&limit={total_limit}"
        
        # Make a single request to get the list of new pages
        res = requests.get(url)
        
        if res.status_code == 200:
            # Parse the HTML content
            soup = BeautifulSoup(res.content, 'html.parser')
            
            page_links = soup.find_all("a", {"class": "mw-newpages-pagename"})
            search_results = []
            for page in page_links:
                search_results.append(ArticleInfo.from_dict({'url': f"https://pt.wikipedia.org{page['href']}", 'title' :page["title"], 
                                       'name':urllib.parse.unquote(page['href'].split("/wiki/")[1])}))
        else:
            raise ValueError(f"Failed to retrieve data. Status code: {res.status_code}")
        return search_results

    def wikipediaapi_extract_section_content(self, article_url : str, section : wikipediaapi.WikipediaPageSection,
                                             sections_dict : Dict[str, ArticleSection], parent_title : str="") -> None:
        # If a parent title exists, append it to the section title with '-subsection'
        section_id = f"{parent_title}-subsection-{section.title}" if parent_title else section.title
        if section_id in sections_dict:
            raise ValueError("Section ID {section_id} already exists!")

        sections_dict[section_id] = ArticleSection.from_dict({"id": section_id,
                                    "title": section.title,
                                     "text":section.text.strip(),
                                     "url":article_url+"#"+"_".join(section.title.split(" "))})

        # Recursively handle subsections
        for subsection in section.sections:
            self.wikipediaapi_extract_section_content(article_url, subsection, sections_dict, section_id)

    def parse_article(self, article: ArticleInfo, processing_type: str = 'wikipediaapi') -> Article:
        """Fetches the article content from its link and adds the text to the article dict."""

        #Use wikipedia api for parsing
        if processing_type=="wikipediaapi":
            article_name = article.get("name")
            article_title = article.get("title")
            article_url = article.get("url")
            wiki_wiki = wikipediaapi.Wikipedia('ScrapperPT', 'pt')
            page_py = wiki_wiki.page(article_name)
            if page_py.exists():
                article_summary = page_py.summary
                article_sections = {}
                #Create a section with the page summary
                article_sections[article_title+"-summary"]=ArticleSection.from_dict({"id":article_title+"-summary",
                                                               "title":article_title+"-summary",
                                                               "text":article_summary,
                                                               "url":article_url})
                # Iterate over all sections in the page and recursively get their content
                for section in page_py.sections:
                    self.wikipediaapi_extract_section_content(article_url, section, article_sections)
                parsed_article = Article(info = article, summary=article_summary, sections=article_sections)
            else:
                raise ValueError(f"Page {article_name} does not exist.")
        else:
            raise ValueError("Invalid processing type specified.")
        
        return parsed_article

    def get_last_pt_articles(self, total_limit: int = 10, requests_per_second: int = 4,
                            processing_type = "default", 
                            verbose=True) -> List[Article]:
        """Combines listing and parsing of the articles, applying a request rate limit.""" 
        articles = self.list_last_pt_articles(total_limit=total_limit)
        parsed_articles = []

        # Calculate the delay between requests to achieve the desired rate
        delay = 1 / requests_per_second  # Time to wait between requests

        # Use tqdm with total parameter for correct progress display
        for article in tqdm(articles, total=len(articles) if verbose else None):
            # Parse the article's content
            parsed_article = self.parse_article(article, processing_type = processing_type)
            parsed_articles.append(parsed_article)

            # Apply rate limiting: wait before processing the next article
            time.sleep(delay)

        return parsed_articles
    
    def get_articles_chunks(self, articles : List[Article], chunking_model : ChunkingModel) -> List[ArticleChunk]:
        articles_chunks = []
        for i in range(len(articles)):
            article = articles[i]
            article_id = article["info"]["name"]
            #add information to each chunk
            for section_idx, section_key in enumerate(list(article["sections"].keys())): 
                section = article["sections"][section_key]
                section_text = section.get("text", "").strip()
                # Check if "text" is empty and pass the entire section if so
                if not section_text:
                    continue
                else:
                    section_id = article["info"]["name"]+"#"+section["id"]
                    chunk_texts_list = [doc for doc in chunking_model.split_text(section_text)]
                    for chunk_idx, chunk_text in enumerate(chunk_texts_list):
                        chunk_id = section_id+"#"+str(chunk_idx)
                        articles_chunks.append(ArticleChunk(chunk_id= chunk_id, chunk_text=chunk_text,
                                                            n_tokens=len(chunk_text),
                                                            article_section=section, article=article))
        return articles_chunks