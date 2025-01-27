"""
LSEG Data Fetcher

This script provides functionality to fetch data from LSEG (formerly Refinitiv Eikon).
"""

import argparse
import logging
from datetime import datetime, timedelta
from typing import List

from macroeconomic_data.lseg.core.client import LSEGClient
from macroeconomic_data.utils.logging import setup_logging

logger = logging.getLogger(__name__)

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Fetch data from LSEG (Refinitiv Eikon)")
    
    parser.add_argument(
        "rics",
        nargs="+",
        help="List of RIC (Reuters Instrument Codes) to fetch"
    )
    
    parser.add_argument(
        "--start-date",
        type=str,
        help="Start date in YYYY-MM-DD format (defaults to 30 days ago)",
        default=(datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    )
    
    parser.add_argument(
        "--end-date",
        type=str,
        help="End date in YYYY-MM-DD format (defaults to today)",
        default=datetime.now().strftime("%Y-%m-%d")
    )
    
    parser.add_argument(
        "--interval",
        type=str,
        choices=["daily", "weekly", "monthly"],
        default="daily",
        help="Data interval (default: daily)"
    )
    
    parser.add_argument(
        "--fields",
        nargs="+",
        help="Specific fields to fetch (if not provided, fetches time series data)",
        default=None
    )
    
    return parser.parse_args()

def main() -> None:
    """Main function to fetch LSEG data."""
    setup_logging()
    args = parse_args()
    
    try:
        client = LSEGClient()
        
        if args.fields:
            logger.info(f"Fetching fields {args.fields} for instruments {args.rics}")
            data = client.get_data(args.rics, args.fields)
        else:
            logger.info(
                f"Fetching time series data for {args.rics} "
                f"from {args.start_date} to {args.end_date} "
                f"with {args.interval} interval"
            )
            data = client.get_timeseries(
                args.rics,
                args.start_date,
                args.end_date,
                args.interval
            )
        
        if data is not None and not data.empty:
            logger.info("Successfully fetched data")
            logger.info("\nData Preview:")
            logger.info("\n%s", data.head())
            # TODO: Add data processing and storage logic
        else:
            logger.error("No data was retrieved")
            
    except Exception as e:
        logger.error(f"Failed to fetch LSEG data: {str(e)}")
        raise

if __name__ == "__main__":
    main() 