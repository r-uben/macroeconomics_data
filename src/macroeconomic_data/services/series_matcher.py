from ..core.llm_client import LLMClient
from ..core.fred_client import FREDClient
from ..config.settings import settings
from thefuzz import fuzz
import logging
import pandas as pd

logger = logging.getLogger(__name__)

class SeriesMatcher:
    def __init__(self):
        self.llm = LLMClient()
        self.fred = FREDClient()
        self.series_mapping = settings.FRED_SERIES_MAPPINGS
        self.series_cache = {}  # Cache for FRED series metadata
        
    def search_fred_series(self, query: str) -> pd.DataFrame:
        """Search FRED database for series matching the query"""
        try:
            # Use FRED's search functionality
            results = self.fred.client.search(query)
            
            if results is not None and not results.empty:
                # Clean and format results
                results = results[['id', 'title', 'frequency', 'units', 'seasonal_adjustment']]
                results = results.sort_values('popularity', ascending=False)
                logger.info(f"Found {len(results)} series matching '{query}'")
                return results
            
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Error searching FRED: {str(e)}")
            return pd.DataFrame()
    
    def match_series(self, query: str) -> str:
        """Match a natural language query to a FRED series ID"""
        try:
            # First, try direct mapping
            normalized_query = query.lower().strip()
            if normalized_query in self.series_mapping:
                logger.info(f"Direct match found for '{query}'")
                return self.series_mapping[normalized_query]
            
            # Search FRED database
            search_results = self.search_fred_series(query)
            
            if not search_results.empty:
                # Use LLM to choose the best match from search results
                prompt = f"""
                Given this economic data query: "{query}"
                Choose the most appropriate FRED series ID from these options:

                {search_results[['id', 'title', 'frequency', 'units']].to_string()}

                Return only the series ID, nothing else.
                """
                
                series_id = self.llm.get_completion(prompt).strip()
                if series_id in search_results['id'].values:
                    logger.info(f"LLM selected series '{series_id}' from FRED search results")
                    # Cache the mapping for future use
                    self.series_mapping[normalized_query] = series_id
                    return series_id
            
            # Fallback to fuzzy matching with default mappings
            return self._fuzzy_match(normalized_query)
            
        except Exception as e:
            logger.error(f"Error matching series for query '{query}': {str(e)}")
            return self._fuzzy_match(normalized_query)
    
    def _fuzzy_match(self, query: str) -> str:
        """Fallback fuzzy matching with default mappings"""
        best_match = None
        best_score = 0
        
        for key in self.series_mapping:
            score = fuzz.ratio(query, key)
            if score > best_score:
                best_score = score
                best_match = key
        
        if best_match and best_score > 60:  # threshold for acceptable match
            logger.info(f"Fuzzy matched '{query}' to '{best_match}'")
            return self.series_mapping[best_match]
        
        raise ValueError(f"Could not find matching series for '{query}'") 