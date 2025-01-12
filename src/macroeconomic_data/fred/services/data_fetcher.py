"""
Service for fetching data from FRED.
"""
import logging
from typing import Optional
import pandas as pd
from ..core.fred_client import FREDClient
from ...aws.bucket_manager import BucketManager

logger = logging.getLogger(__name__)

class DataFetcher:
    """Service for fetching and managing FRED data."""
    
    # Common FRED series IDs for frequently requested variables
    COMMON_SERIES = {
        'real gdp': 'GDPC1',
        'nominal gdp': 'GDP',
        'unemployment rate': 'UNRATE',
        'cpi': 'CPIAUCSL',
        'core cpi': 'CPILFESL',
        'industrial production': 'INDPRO',
        'federal funds rate': 'FEDFUNDS',
        'consumer price index': 'CPIAUCSL',
        'core inflation': 'CPILFESL',
    }
    
    def __init__(self):
        """Initialize the data fetcher."""
        self.client = FREDClient()
        self.bucket_manager = BucketManager(bucket_name="fred-data")
    
    def _find_series_id(self, query: str) -> str:
        """Find the appropriate FRED series ID for a query."""
        # Clean the query
        query = query.lower().strip()
        
        # Check if it's a common series
        if query in self.COMMON_SERIES:
            return self.COMMON_SERIES[query]
            
        # Check if any common series contains the query
        for key, series_id in self.COMMON_SERIES.items():
            if query in key:
                return series_id
        
        # If query is already a FRED series ID, use it
        if query.isupper() and not ' ' in query:
            return query
            
        # Search FRED database
        search_results = self.client.search_series(query)
        if not search_results.empty:
            return search_results.index[0]  # Use the first result
            
        raise ValueError(f"Could not find a matching FRED series for query: {query}")
    
    def get_series(self, query: str) -> pd.DataFrame:
        """Get time series data for a given query."""
        try:
            # Find the appropriate series ID
            series_id = self._find_series_id(query)
            
            # Fetch the data
            data = self.client.get_series(series_id)
            return data
            
        except Exception as e:
            logger.error(f"Error fetching data for query '{query}': {str(e)}")
            raise 