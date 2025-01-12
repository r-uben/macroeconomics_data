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

def fetch_data(query: str) -> Optional[bool]:
    """Fetch data from the appropriate source based on the query."""
    try:
        # Determine which source to use
        source, cleaned_query = determine_data_source(query)
        
        print_separator()
        
        # Save original argv
        original_argv = sys.argv
        
        try:
            # Run the appropriate script with the cleaned query
            if source == "FRED":
                print(f"📥 Fetching historical data from FRED...")
                sys.argv = ['fetch-federal-reserve-data', '--query', cleaned_query]
                success = fetch_federal_reserve_data.main() == 0
            else:
                print(f"📥 Fetching Greenbook projections...")
                # Just pass the query without force-download
                sys.argv = ['fetch-greenbook-data', '--query', cleaned_query]
                success = fetch_greenbook_data.main() == 0
                
            return success
            
        finally:
            # Restore original argv
            sys.argv = original_argv
            
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
    args = parser.parse_args()
    
    query = ' '.join(args.query)
    print("\n🔍 Processing query:", query)
    
    success = fetch_data(query)
    print_separator()
    
    if success:
        print("✅ Data fetched and saved successfully!")
    else:
        print("❌ Failed to fetch data. Please try again or modify your query.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 