from pathlib import Path
from ..core.fred_client import FREDClient
from ..services.series_matcher import SeriesMatcher
from ..config.settings import DATA_DIR
import logging
import re

logger = logging.getLogger(__name__)

class DataFetcher:
    def __init__(self):
        self.series_matcher = SeriesMatcher()
        DATA_DIR.mkdir(exist_ok=True)
    
    def get_series(self, query: str, save=True):
        """Get economic data series based on natural language query"""
        try:
            # Match query to FRED series ID
            series_id = self.series_matcher.match_series(query)
            logger.info(f"Matched query '{query}' to series ID '{series_id}'")
            
            # Get data using FRED client
            data = self.series_matcher.fred.get_series(series_id)
            
            if save:
                # Create standardized filename
                clean_query = re.sub(r'[^a-z0-9]+', '_', query.lower()).strip('_')
                filename = f"{clean_query}__series_id={series_id}.csv"
                filepath = DATA_DIR / filename
                
                # Save with metadata
                data.to_csv(filepath)
                logger.info(f"Saved data to {filepath}")
            
            return data
            
        except Exception as e:
            logger.error(f"Error fetching series for query '{query}': {str(e)}")
            raise 