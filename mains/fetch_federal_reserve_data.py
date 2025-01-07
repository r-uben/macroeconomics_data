import logging
from src.macroeconomic_data.services.data_fetcher import DataFetcher
import pandas as pd
import argparse

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def fetch_key_economic_indicators():
    """Fetch key economic indicators from Federal Reserve Economic Data (FRED)"""
    logger.info("Fetching key economic indicators from FRED...")
    
    try:
        fetcher = DataFetcher()
        
        # Dictionary to store our data
        indicators = {}
        
        # Real Economy
        logger.info("\n=== Real Economy Indicators ===")
        indicators['gdp'] = fetcher.get_series("real gdp")
        indicators['industrial_production'] = fetcher.get_series("industrial production")
        indicators['unemployment'] = fetcher.get_series("unemployment rate")
        
        # Prices and Inflation
        logger.info("\n=== Price and Inflation Indicators ===")
        indicators['cpi'] = fetcher.get_series("consumer price index")
        indicators['core_inflation'] = fetcher.get_series("core inflation")
        
        # Financial Conditions
        logger.info("\n=== Financial Indicators ===")
        indicators['fed_funds'] = fetcher.get_series("federal funds rate")
        
        # Print summary statistics
        logger.info("\n=== Data Summary ===")
        for name, data in indicators.items():
            logger.info(f"\n{name.upper()}:")
            logger.info(f"Frequency: {data.index.freq if data.index.freq else 'Inferred from data'}")
            logger.info(f"Date range: {data.index.min()} to {data.index.max()}")
            logger.info(f"Latest value: {data['value'].iloc[-1]:.2f}")
        
        return indicators
        
    except Exception as e:
        logger.error(f"Error fetching economic data: {str(e)}")
        raise

def interactive_mode():
    """Interactive mode for querying FRED data"""
    logger.info("\nEntering interactive mode...")
    logger.info("Type 'exit' or 'quit' to end the session")
    logger.info("Example queries:")
    logger.info("  - real gdp")
    logger.info("  - unemployment rate")
    logger.info("  - consumer price index")
    logger.info("  - federal funds rate")
    
    fetcher = DataFetcher()
    
    while True:
        try:
            query = input("\nEnter your query: ").strip().lower()
            
            if query in ['exit', 'quit']:
                logger.info("Exiting interactive mode...")
                break
            
            if not query:
                continue
                
            data = fetcher.get_series(query)
            
            # Print summary statistics
            logger.info("\n=== Data Summary ===")
            logger.info(f"Query: {query}")
            logger.info(f"Frequency: {data.index.freq if data.index.freq else 'Inferred from data'}")
            logger.info(f"Date range: {data.index.min()} to {data.index.max()}")
            logger.info(f"Latest value: {data['value'].iloc[-1]:.2f}")
            
            # Ask if user wants to see more details
            show_more = input("\nWould you like to see more details? (y/n): ").strip().lower()
            if show_more == 'y':
                print("\nLast 5 observations:")
                print(data.tail())
                print("\nBasic statistics:")
                print(data.describe())
            
        except KeyboardInterrupt:
            logger.info("\nExiting interactive mode...")
            break
        except Exception as e:
            logger.error(f"Error: {str(e)}")

def main():
    """Main function to fetch and display Federal Reserve economic data"""
    parser = argparse.ArgumentParser(description="Fetch economic data from Federal Reserve (FRED)")
    parser.add_argument('-i', '--interactive', action='store_true', 
                       help='Enter interactive mode for querying FRED data')
    args = parser.parse_args()
    
    if args.interactive:
        interactive_mode()
        return 0
    
    logger.info("Starting Federal Reserve data fetch...")
    try:
        indicators = fetch_key_economic_indicators()
        logger.info("\nSuccessfully retrieved all economic indicators")
        return 0
    except Exception as e:
        logger.error(f"Program failed: {str(e)}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main()) 