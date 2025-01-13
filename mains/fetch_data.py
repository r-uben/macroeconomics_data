"""
Master script to fetch data from either FRED or Greenbook based on user's query.
"""
import logging
import argparse
import groq
import json
from typing import Tuple, Optional
import sys
from pathlib import Path

from macroeconomic_data.aws.secrets_manager import get_secret
from mains import fetch_federal_reserve_data, fetch_greenbook_data

# Configure logging to only show our formatted messages
logging.basicConfig(
    level=logging.WARNING,  # Only show warnings and above from other modules
    format='%(message)s'
)

# Set our logger to INFO but others to WARNING
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Suppress all loggers
for log_name in ['botocore', 'urllib3', 'httpx', 'boto3', 'src.macroeconomic_data', 'mains.fetch_greenbook_data']:
    logging.getLogger(log_name).setLevel(logging.ERROR)

PROMPT = """You are an expert in economic data. Your task is to determine whether a user's query is asking for:
1. Historical/actual data from FRED (Federal Reserve Economic Data)
2. Forecast/projection data from the Greenbook/Tealbook

Consider:
- If the query mentions projections, forecasts, predictions, or Greenbook/Tealbook -> use Greenbook
- If the query is about historical or actual data, or just mentions the variable without context -> use FRED
- If unclear, default to FRED as it's the actual historical data

User query: "{query}"

Return a JSON object in this format:
{{
    "source": "FRED" or "GREENBOOK",
    "confidence": 0-1 score,
    "reasoning": "brief explanation of why this source was chosen",
    "query": "cleaned query focusing on the variable name"
}}"""

def print_separator():
    """Print a separator line."""
    print("\n" + "="*80 + "\n")

def determine_data_source(query: str) -> Tuple[str, str]:
    """Use LLM to determine which data source to use."""
    try:
        # Get Groq API key
        api_key = get_secret('GROQ_API_KEY')
        if isinstance(api_key, dict):
            api_key = api_key.get('api_key')
        if not api_key:
            raise ValueError("Could not find valid Groq API key")
            
        # Initialize Groq client
        client = groq.Groq(api_key=api_key)
        
        print_separator()
        print("🤔 Analyzing your query...")
        
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": PROMPT.format(query=query)}],
            model="mixtral-8x7b-32768",
            temperature=0.1,
            max_tokens=500
        )
        
        result = json.loads(completion.choices[0].message.content)
        
        print(f"📊 Selected Data Source: {result['source']}")
        print(f"💡 Reasoning: {result['reasoning']}")
        
        return result['source'], result['query']
        
    except Exception as e:
        print("\n⚠️  Could not determine data source automatically. Falling back to FRED...")
        # Extract the main variable name from the query by removing common keywords
        cleaned_query = query.lower()
        for word in ['historical', 'actual', 'current', 'data', 'value', 'series']:
            cleaned_query = cleaned_query.replace(word, '').strip()
        return "FRED", cleaned_query

def fetch_data(query: str, force_reload: bool = False) -> Optional[bool]:
    """Fetch data from the appropriate source based on the query."""
    try:
        # Determine which source to use
        source, cleaned_query = determine_data_source(query)
        
        print_separator()
        
        # Handle FRED data differently
        if source == "FRED":
            print(f"📥 Fetching historical data from FRED...")
            from src.macroeconomic_data.fred.services.data_fetcher import DataFetcher
            fetcher = DataFetcher()
            data = fetcher.get_series(cleaned_query)
            print(f"\n📊 Found data for: {cleaned_query}")
            print(f"📅 Date range: {data.index.min().strftime('%Y-%m-%d')} to {data.index.max().strftime('%Y-%m-%d')}")
            latest_value = float(data.iloc[-1].iloc[0])  # Get the scalar value first, then convert to float
            print(f"📈 Latest value: {latest_value:,.2f}")  # Add thousands separator and ensure float formatting
            return True
        else:
            print(f"📥 Fetching Greenbook projections...")
            from src.macroeconomic_data.greenbook.services.data_fetcher import GreenBookDataFetcher
            from src.macroeconomic_data.greenbook.utils.variable_mapper import VariableMapper
            
            # Initialize fetcher and mapper
            fetcher = GreenBookDataFetcher()
            mapper = VariableMapper()
            
            # Find matches for the query
            matches = mapper.match_variable(cleaned_query)
            if not matches:
                print("\n❌ No matching variables found.")
                return False
            
            # If multiple matches, let user choose
            if len(matches) > 1:
                print("\nMultiple matches found. Please choose one:")
                for idx, match in enumerate(matches, 1):
                    var_info = mapper.get_variable_info(match['variable_key'])
                    print(f"{idx}. {match['variable_key']} ({var_info['description']})")
                
                while True:
                    try:
                        choice = int(input("\nEnter number (0 to cancel): "))
                        if choice == 0:
                            return False
                        if 1 <= choice <= len(matches):
                            selected_match = matches[choice - 1]
                            break
                        print("Invalid choice. Please try again.")
                    except ValueError:
                        print("Please enter a valid number.")
            else:
                selected_match = matches[0]
            
            # Get the variable key and fetch data
            variable_key = selected_match['variable_key']  # Use the full key
            success = fetcher.download_and_store_variable(variable_key, force_download=force_reload)
            
            return success
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return None

def main():
    """Main function to fetch economic data from either FRED or Greenbook."""
    parser = argparse.ArgumentParser(
        description="Fetch economic data from either FRED or Greenbook based on query"
    )
    parser.add_argument(
        'query', 
        type=str, 
        nargs='+',
        help='Query describing the data you want (e.g., "greenbook projections for real gdp" or "historical real gdp")'
    )
    parser.add_argument(
        '--reload',
        action='store_true',
        help='Force reload data from source instead of using cached version'
    )
    args = parser.parse_args()
    
    query = ' '.join(args.query)
    print("\n🔍 Processing query:", query)
    
    success = fetch_data(query, force_reload=args.reload)
    print_separator()
    
    if success:
        print("✅ Data fetched and saved successfully!")
    else:
        print("❌ Failed to fetch data. Please try again or modify your query.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 