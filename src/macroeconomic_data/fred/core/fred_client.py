"""
Core FRED client implementation.
"""
import logging
import pandas as pd
from ...aws.secrets_manager import get_secret
from fredapi import Fred

logger = logging.getLogger(__name__)

class FREDClient:
    """Client for interacting with FRED API."""
    
    def __init__(self):
        """Initialize FRED client with API key from AWS Secrets Manager."""
        try:
            # Get API key and ensure it's a plain string
            api_key = get_secret('FRED_API_KEY', key='api_key')
            if isinstance(api_key, dict):
                api_key = api_key.get('api_key')
            self.client = Fred(api_key=api_key)
        except Exception as e:
            logger.error(f"Failed to initialize FRED client: {str(e)}")
            raise
    
    def get_series(self, series_id: str, start_date=None, end_date=None) -> pd.DataFrame:
        """Fetch and standardize data series from FRED"""
        # Get the raw series
        series = self.client.get_series(series_id, start_date, end_date)
        
        # Get series info
        info = self.client.get_series_info(series_id)
        
        # Convert to DataFrame
        df = series.to_frame(name='value')
        df.index.name = 'date'
        
        # Get frequency
        frequency = info.get('frequency_short', 'M')  # Default to monthly if not specified
        
        # Standardize the index to end-of-period dates
        if frequency == 'Q':
            # For quarterly data, resample to end of quarter
            df = df.resample('QE-DEC').last()
            # Ensure it's end of quarter (Q4)
            df.index = df.index + pd.offsets.QuarterEnd(0)
        elif frequency == 'M':
            # For monthly data, ensure it's end of month
            df = df.resample('ME').last()
            df.index = df.index + pd.offsets.MonthEnd(0)
        
        # Ensure index is datetime
        df.index = pd.to_datetime(df.index)
        
        # Sort index in ascending order
        df = df.sort_index()
        
        # Add metadata
        df.attrs['series_id'] = series_id
        df.attrs['title'] = info.get('title', '')
        df.attrs['frequency'] = frequency
        df.attrs['units'] = info.get('units', '')
        
        return df

    def get_series_info(self, series_id: str) -> dict:
        """Get metadata information about a FRED series."""
        return self.client.get_series_info(series_id)

    def search_series(self, search_text: str) -> pd.DataFrame:
        """Search for series in FRED"""
        return self.client.search(search_text) 