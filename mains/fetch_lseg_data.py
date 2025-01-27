"""
LSEG Data Fetcher

This script provides functionality to fetch data from LSEG (formerly Refinitiv Eikon).
"""

import argparse
import logging
from datetime import datetime, timedelta
from typing import List
from pathlib import Path
import os
import pandas as pd

from macroeconomic_data.lseg.core.client import LSEGClient
from macroeconomic_data.utils import setup_logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

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

def ensure_directory(path: str):
    """Ensure a directory exists."""
    Path(path).mkdir(parents=True, exist_ok=True)

def save_to_local(data: pd.DataFrame, identifier: str, description: str):
    """Save data to local lseg directory."""
    base_dir = "data/lseg"
    var_dir = os.path.join(base_dir, identifier)
    ensure_directory(var_dir)
    
    # Save data
    filename = os.path.join(var_dir, "data.csv")
    data.to_csv(filename, index=True)
    
    # Save metadata
    with open(os.path.join(var_dir, "metadata.txt"), "w") as f:
        f.write(f"Identifier: {identifier}\n")
        f.write(f"Description: {description}\n")
        f.write(f"Last updated: {pd.Timestamp.now()}\n")
        f.write(f"Date range: {data.index.min()} to {data.index.max()}\n")
        f.write(f"Columns: {', '.join(map(str, data.columns))}\n")

def main() -> None:
    """Main function to fetch LSEG data."""
    setup_logging()
    logging.getLogger().setLevel(logging.WARNING)  # Force WARNING level for all
    args = parse_args()
    
    try:
        client = LSEGClient()
        
        if args.fields:
            data = client.get_data(args.rics, args.fields)
            identifier = f"{'_'.join(args.rics)}_{'_'.join(args.fields)}"
            desc = f"Field data for {', '.join(args.rics)}"
        else:
            data = client.get_timeseries(
                args.rics,
                args.start_date,
                args.end_date,
                args.interval
            )
            identifier = f"{'_'.join(args.rics)}_{args.interval}"
            desc = f"{args.interval} time series for {', '.join(args.rics)}"
        
        if data is not None and not data.empty:
            save_to_local(data, identifier, desc)
        else:
            logger.error("No data was retrieved")
            
    except Exception as e:
        logger.error(f"Failed to fetch LSEG data: {str(e)}")
        raise

if __name__ == "__main__":
    main() 