import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import time
from tqdm import tqdm
import wikipediaapi
import urllib.parse

class ScrapperWikipedia:
    def __init__(self):
        pass

    def list_last_pt_articles(self, total_limit: int = 500) -> List[Dict]:
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
                search_results.append({'link': f"https://pt.wikipedia.org{page['href']}", 'title' :page["title"], 
                                       'name':urllib.parse.unquote(page['href'].split("/wiki/")[1])})
        else:
            raise ValueError(f"Failed to retrieve data. Status code: {res.status_code}")
        return search_results

    def wikipediaapi_extract_section_content(self, section, sections_dict, parent_title=""):
        # If a parent title exists, append it to the section title with '-subsection'
        section_title = f"{parent_title}-subsection-{section.title}" if parent_title else section.title
        sections_dict[section_title] = {"section_text":section.text.strip()}

        # Recursively handle subsections
        for subsection in section.sections:
            self.wikipediaapi_extract_section_content(subsection, sections_dict, section_title)

    def parse_article(self, article: Dict, processing_type: str = 'default') -> Dict:
        """Fetches the article content from its link and adds the text to the article dict.
        
        Args:
            article (Dict): The article dictionary containing the link.
            processing_type (str): The type of processing to use for extracting text.
                                   Options: 'default' (parses HTML) or 'simple' (gets text directly).
            parse_text_processing_type (str): The type of text processing to apply after fetching the article.
                                               Options: 'default' (processes as HTML) or 'simple' (raw text).

        Returns:
            Dict: The updated article dictionary with the text added.
        """        
        if processing_type=="wikipediaapi":
            article_name = article.get("name")
            article_title = article.get("title")
            wiki_wiki = wikipediaapi.Wikipedia('ScrapperPT', 'pt')
            page_py = wiki_wiki.page(article_name)
            if page_py.exists():
                article["summary"] = page_py.summary
                article["sections"] = {}
                # Iterate over all sections in the page and recursively get their content
                article["sections"]["summary-"+article_title]={"section_text":article["summary"]}
                for section in page_py.sections:
                    self.wikipediaapi_extract_section_content(section, article["sections"])
                #add information to each chunk
                for section in list(article["sections"].keys()): 
                    # Check if "section_text" is empty and pop the entire section if so
                    if not article["sections"][section].get("section_text", "").strip():
                        article["sections"].pop(section)
                    else:    
                        # Add other info to the chunk
                        article["sections"][section].update({
                            key: value for key, value in article.items() if key != "sections"
                        })
            else:
                raise ValueError(f"Page {article_name} does not exist.")
        #Beautiful-Soup
        elif processing_type == 'beautiful-soup':
            article_url = article.get("link")
            res = requests.get(article_url)
            article["summary"] = ""
            if res.status_code == 200:
                soup = BeautifulSoup(res.content, 'html.parser')
                
                # Parse the content from the main body of the article
                content = soup.find('div', class_='mw-parser-output')
                if content:
                    paragraphs = content.find_all('p')
                    # Join all paragraph texts to form the full article text
                    article_text = '\n'.join([para.get_text(strip=False) for para in paragraphs])
                    article["sections"] = {"all_text":{"section_text":article_text, **{key: value for key, value in article.items() if key != "sections"}}}
                else:
                    raise ValueError(f"No content on webpage for article {article_url}")
            else:
                raise ValueError(f"Failed to fetch article content for article {article_url}")
        else:
            raise ValueError("Invalid processing type specified.")
        
        return article

    def get_last_pt_articles(self, total_limit: int = 10, requests_per_second: int = 4,
                            processing_type = "default", 
                            verbose=True) -> List[Dict]:
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