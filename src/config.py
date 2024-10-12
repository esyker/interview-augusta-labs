import os
from dotenv import load_dotenv
from utils.scrapper_wikipedia import ScrapperWikipedia
from utils.chunking_models import ChunkingModel
from utils.index import Index
from utils.typedefs import ArticleChunk

class Config:
    def __init__(self, file_path: str = ".env"):
        # Load environment variables
        load_dotenv(dotenv_path=file_path)

        # Load required env-based config parameters without defaults
        self.SCRAPING_RESULTS_LIMIT = self._get_env_var("SCRAPING_RESULTS_LIMIT", int)
        self.SCRAPING_REQUESTS_PER_SECOND = self._get_env_var("SCRAPING_REQUESTS_PER_SECOND", int)
        self.SCRAPING_TYPE = self._get_env_var("SCRAPING_TYPE", str)
        self.CHUNK_SIZE = self._get_env_var("CHUNK_SIZE", int)
        self.CHUNK_OVERLAP = self._get_env_var("CHUNK_OVERLAP", int)
        self.VERBOSE = self._get_env_var("VERBOSE", bool)
        self.SEARCH_RESULTS_LIMIT = self._get_env_var("SEARCH_RESULTS_LIMIT", int)
        self.SEARCH_REFINED_ALPHA = self._get_env_var("SEARCH_REFINED_ALPHA", float)
        self.SEARCH_REFINED_BETA = self._get_env_var("SEARCH_REFINED_BETA", float)
        self.SEARCH_REFINED_GAMMA = self._get_env_var("SEARCH_REFINED_GAMMA", float)

        #Initialize other support variables for the app
        self.last_search_result = None
        
        # Initialize based on other properties
        self._wiki_search = ScrapperWikipedia()
        self._index = Index(text_fields=ArticleChunk.get_text_fields_names(), vectorizer_params={})
        self._chunking_model = ChunkingModel(chunk_size=self.CHUNK_SIZE, chunk_overlap=self.CHUNK_OVERLAP)

    @staticmethod
    def strtobool(val: str) -> bool:
        """
        Convert a string value to a boolean.
        """
        val = val.lower()
        if val in ('y', 'yes', 't', 'true', 'on', '1'):
            return True
        elif val in ('n', 'no', 'f', 'false', 'off', '0'):
            return False
        else:
            raise ValueError(f"Invalid truth value: {val}")
    
    def _get_env_var(self, var_name: str, var_type):
        """
        Helper function to get an environment variable and convert to the correct type.
        Raises an error if the variable is not found.
        """
        value = os.getenv(var_name)
        if value is None:
            raise EnvironmentError(f"Environment variable {var_name} is missing")
        
        # Handle boolean type with strtobool
        if var_type == bool:
            try:
                return self.strtobool(value)
            except ValueError:
                raise ValueError(f"Invalid truth value for {var_name}: {value}")
        return var_type(value)

    # Getters for the instantiated objects only
    @property
    def wiki_search(self) -> ScrapperWikipedia:
        return self._wiki_search

    @property
    def index(self) -> Index:
        return self._index

    @property
    def chunking_model(self) -> ChunkingModel:
        return self._chunking_model
