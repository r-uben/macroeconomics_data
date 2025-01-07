from fredapi import Fred
import pandas as pd
import json
from ..utils.aws import get_secret
from ..config.settings import settings
from pathlib import Path

class FREDClient:
    def __init__(self):
        try:
            # Get FRED API key
            secret_value = get_secret(settings.FED_SECRET_NAME)
            
            # Handle both JSON and plain text formats
            try:
                api_key = json.loads(secret_value)['api_key']
            except json.JSONDecodeError:
                api_key = secret_value  # Use as plain text if not JSON
                
            if not api_key or not isinstance(api_key, str):
                raise ValueError("Invalid FRED API key format")
                
            self.client = Fred(api_key=api_key)
            
        except Exception as e:
            print(f"\nAttempted to access secret: {settings.FED_SECRET_NAME}")
            print(f"Current AWS Region: {settings.AWS_REGION}")
            print(f"Error details: {str(e)}")
            raise ValueError(f"Failed to initialize FRED client") from e
    
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

    def search_series(self, search_text: str) -> pd.DataFrame:
        """Search for series in FRED"""
        return self.client.search(search_text) 