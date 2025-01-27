"""
Examples of using the LSEG (Refinitiv Eikon) client to fetch market data.
"""

import logging
from datetime import datetime, timedelta

from macroeconomic_data.lseg.core.client import LSEGClient

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Run examples of LSEG client usage."""
    try:
        # Initialize the client
        client = LSEGClient()
        
        # Example 1: Fetch daily OHLCV data for Apple stock for the last month
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        apple_data = client.get_timeseries(
            rics="AAPL.O",  # Apple stock RIC
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            interval="daily"
        )
        if apple_data is not None:
            logger.info("Apple stock data:")
            logger.info("\n%s", apple_data.head())
        
        # Example 2: Fetch weekly data for multiple tech stocks
        tech_stocks = ["MSFT.O", "GOOGL.O", "META.O"]
        tech_data = client.get_timeseries(
            rics=tech_stocks,
            start_date="2023-01-01",
            end_date="2024-01-31",
            interval="weekly"
        )
        if tech_data is not None:
            logger.info("\nTech stocks weekly data:")
            logger.info("\n%s", tech_data.head())
        
        # Example 3: Fetch specific fundamental data
        fields = [
            "TR.PriceClose",    # Closing price
            "TR.PERatio",       # P/E Ratio
            "TR.MarketCap",     # Market Cap
            "TR.DivYield",      # Dividend Yield
            "TR.Revenue"        # Revenue
        ]
        fundamental_data = client.get_data(
            rics=["AAPL.O", "MSFT.O", "GOOGL.O"],
            fields=fields
        )
        if fundamental_data is not None:
            logger.info("\nFundamental data:")
            logger.info("\n%s", fundamental_data)
            
    except Exception as e:
        logger.error("Failed to run examples: %s", str(e))
        raise

if __name__ == "__main__":
    main() 