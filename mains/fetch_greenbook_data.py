"""
Script to fetch and update Greenbook/Tealbook data from Philadelphia Fed.
"""
import logging
import argparse
import os
from pathlib import Path
import pandas as pd

from src.macroeconomic_data.greenbook import GreenBookDataFetcher
from src.macroeconomic_data.greenbook.utils.variable_mapper import VariableMapper

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def ensure_directory(path: str):
    """Ensure a directory exists."""
    Path(path).mkdir(parents=True, exist_ok=True)

def save_to_local(data: pd.DataFrame, variable_code: str, description: str):
    """Save data to local green_book directory."""
    base_dir = "data/green_book"
    var_dir = os.path.join(base_dir, variable_code)
    ensure_directory(var_dir)
    
    # Save data
    filename = os.path.join(var_dir, "data.csv")
    data.to_csv(filename, index=True)
    
    # Save metadata
    with open(os.path.join(var_dir, "metadata.txt"), "w") as f:
        f.write(f"Variable: {variable_code}\n")
        f.write(f"Description: {description}\n")
        f.write(f"Last updated: {pd.Timestamp.now()}\n")

def get_user_choice(matches: list) -> str:
    """Get user's choice when multiple matches are found."""
    print("\nMultiple matches found. Please choose one:")
    for i, match in enumerate(matches, 1):
        var_key = match['variable_key']
        reason = match['reasoning']
        print(f"{i}. {var_key} ({reason})")
    
    while True:
        try:
            choice = int(input("\nEnter number (0 to cancel): "))
            if choice == 0:
                return None
            if 1 <= choice <= len(matches):
                return matches[choice - 1]['variable_key']
        except ValueError:
            pass
        print("Invalid choice. Please try again.")

def main():
    """Main function to fetch and store Greenbook/Tealbook data."""
    parser = argparse.ArgumentParser(description="Fetch Greenbook/Tealbook data from Philadelphia Fed")
    parser.add_argument('--check-updates', action='store_true', 
                       help='Check for updates in existing data')
    parser.add_argument('--query', type=str,
                       help='Natural language query for specific variable')
    parser.add_argument('--force-download', action='store_true',
                       help='Force download even if data exists')
    args = parser.parse_args()
    
    fetcher = GreenBookDataFetcher()
    mapper = VariableMapper()
    
    try:
        # First, ensure we have the data in S3
        if args.force_download or args.check_updates:
            logger.info("Checking for updates in Greenbook/Tealbook data...")
            results = fetcher.check_for_updates()
            
            # Report results
            updated = [var for var, success in results.items() if success]
            failed = [var for var, success in results.items() if not success]
            
            if updated:
                logger.info(f"Successfully updated: {', '.join(updated)}")
            if failed:
                logger.warning(f"Failed to update: {', '.join(failed)}")
        
        # Handle specific query
        if args.query:
            logger.info(f"Processing query: {args.query}")
            matches = mapper.match_variable(args.query)
            
            if not matches:
                logger.error("No matching variables found")
                return 1
                
            # Handle multiple matches
            if len(matches) > 1:
                variable_key = get_user_choice(matches)
                if not variable_key:
                    logger.info("Operation cancelled by user")
                    return 0
            else:
                variable_key = matches[0]['variable_key']
            
            # Get variable code and info
            variable_code = mapper.get_variable_code(variable_key)
            variable_info = mapper.get_variable_info(variable_key)
            
            logger.info(f"Fetching data for {variable_code}...")
            data = fetcher.get_variable_data(variable_code)
            
            if data is not None:
                save_to_local(data, variable_code, variable_info['description'])
                logger.info(f"Successfully saved {variable_code} data to data/green_book/{variable_code}/")
            else:
                logger.error(f"Failed to fetch data for {variable_code}")
                return 1
                
        else:
            # Download all variables
            logger.info("Downloading all Greenbook/Tealbook variables...")
            success = True
            
            for var_key in mapper.VARIABLES_DICT.keys():
                if 'options' in mapper.VARIABLES_DICT[var_key]:
                    for opt_key in mapper.VARIABLES_DICT[var_key]['options'].keys():
                        full_key = f"{var_key}.{opt_key}"
                        code = mapper.get_variable_code(full_key)
                        info = mapper.get_variable_info(full_key)
                        
                        data = fetcher.get_variable_data(code)
                        if data is not None:
                            save_to_local(data, code, info['description'])
                            logger.info(f"Successfully saved {code} data")
                        else:
                            logger.error(f"Failed to fetch data for {code}")
                            success = False
                else:
                    code = mapper.get_variable_code(var_key)
                    info = mapper.get_variable_info(var_key)
                    
                    data = fetcher.get_variable_data(code)
                    if data is not None:
                        save_to_local(data, code, info['description'])
                        logger.info(f"Successfully saved {code} data")
                    else:
                        logger.error(f"Failed to fetch data for {code}")
                        success = False
            
            return 0 if success else 1
        
        return 0
        
    except Exception as e:
        logger.error(f"Program failed: {str(e)}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main()) 