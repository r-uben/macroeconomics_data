"""
LSEG Data Client

This module provides a client for interacting with LSEG (Refinitiv Eikon) data services.
"""

import json
import logging
import os
from typing import Dict, List, Optional, Union

import eikon
import pandas as pd

from macroeconomic_data.aws.secrets_manager import get_secret
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

class LSEGClient:
    """Client for fetching data from LSEG (Refinitiv Eikon)."""
    
    def __init__(self) -> None:
        """Initialize the LSEG client with API key from AWS Secrets Manager."""
        try:
            # Force silent operation
            logging.disable(logging.INFO)  # Disable all INFO messages
            logging.getLogger().setLevel(logging.WARNING)
            
            # Suppress all dependency logs
            for lib in ['pyeikon', 'httpx', 'botocore', 'urllib3']:
                logging.getLogger(lib).setLevel(logging.WARNING)
            
            # Check if Refinitiv Workspace is running
            if not os.path.exists("/Applications/Refinitiv Workspace.app"):
                raise RuntimeError(
                    "Refinitiv Workspace is not installed. "
                    "Please install it and ensure it's running."
                )
            
            # Get API key from secrets (silent operation)
            api_key = get_secret("EIKON_API_KEY")["api_key"]
            
            if not api_key:
                raise ValueError(
                    "No API key found in secret. "
                    "Make sure the secret contains the key 'EIKON_API_KEY'"
                )
            
            if not isinstance(api_key, str) or len(api_key) < 10:
                raise ValueError(
                    f"Invalid API key format. Expected a string of at least 10 characters. "
                    f"Got type {type(api_key)} with length {len(str(api_key))}"
                )
            
            eikon.set_app_key(api_key)  # Silent setup
            
            # Silent connection test
            eikon.get_timeout()  # No logging for connection test
            
        except Exception as e:
            logger.error(
                "Failed to initialize LSEG client. "
                "Please ensure:\n"
                "1. Refinitiv Workspace is installed and running\n"
                "2. The API key in AWS Secrets Manager is correct\n"
                "3. You're connected to the internet\n"
                f"Error: {str(e)}"
            )
            raise
        finally:
            logging.disable(logging.NOTSET)  # Restore logging
    
    def get_timeseries(
        self,
        rics: Union[str, List[str]],
        start_date: str,
        end_date: str,
        interval: str = "daily"
    ) -> Optional[pd.DataFrame]:
        """
        Fetch time series data for given RICs.
        
        Args:
            rics: Single RIC or list of RICs to fetch
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            interval: Data interval (daily, weekly, monthly)
            
        Returns:
            DataFrame with time series data or None if error occurs
        """
        try:
            data = eikon.get_timeseries(
                rics,
                fields=["CLOSE", "HIGH", "LOW", "OPEN", "VOLUME"],
                start_date=start_date,
                end_date=end_date,
                interval=interval
            )
            return data
        except Exception as e:
            logger.error(f"Failed to fetch time series data: {str(e)}")
            return None
    
    def get_data(
        self,
        rics: Union[str, List[str]],
        fields: List[str]
    ) -> Optional[pd.DataFrame]:
        """
        Fetch specific data fields for given RICs.
        
        Args:
            rics: Single RIC or list of RICs to fetch
            fields: List of field codes to retrieve
            
        Returns:
            DataFrame with requested fields or None if error occurs
        """
        try:
            data = eikon.get_data(rics, fields)
            return data[0] if isinstance(data, list) and len(data) > 0 else None
        except Exception as e:
            logger.error(f"Failed to fetch data fields: {str(e)}")
            return None 