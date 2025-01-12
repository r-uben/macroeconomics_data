"""
Utility module for mapping user queries to Greenbook variables using LLM.
"""
import json
import logging
from typing import Dict, List, Optional
import groq
from thefuzz import fuzz

from ...aws.secrets_manager import get_secret
from ...aws.bucket_manager import BucketManager

logger = logging.getLogger(__name__)

def get_groq_api_key() -> str:
    """Get Groq API key from AWS Secrets Manager."""
    try:
        api_key = get_secret('GROQ_API_KEY')
        if isinstance(api_key, dict):
            api_key = api_key.get('api_key')
        if not api_key:
            raise ValueError("Could not find valid Groq API key")
        return api_key
    except Exception as e:
        logger.error(f"Error getting Groq API key: {str(e)}")
        raise

GROQ_PROMPT = """You are an expert in economic data and terminology. Your task is to match a user's query to the most relevant Greenbook/Tealbook variable(s).

Available variables:
{variables_list}

User query: "{query}"

Consider:
1. Economic meaning and context
2. Common alternative names/terms
3. Related concepts

Return a JSON list of matches in format:
{{
    "matches": [
        {{
            "variable_key": "category.type (e.g., 'cpi.core', 'gdp.real_gdp')",
            "confidence": 0-1 score,
            "reasoning": "brief explanation"
        }}
    ]
}}

IMPORTANT: For variables with options, use dot notation (e.g., 'cpi.core', 'gdp.real_gdp'). For simple variables, just use the name (e.g., 'unemployment').
Only return variables that are truly relevant. If no good match exists, return an empty list."""

class VariableMapper:
    """Maps user queries to Greenbook variables using LLM."""
    
    VARIABLES_DICT = {
        'gdp': {
            'options': {
                'real_gdp': {
                    'code': 'gRGDP',
                    'description': 'Real GDP (Q/Q Growth; Annualized Percentage Points)',
                    'first_date': 'March 29, 1967'
                },
                'price_gdp': {
                    'code': 'gPGDP',
                    'description': 'GDP Price Inflation (Q/Q; Annualized Percentage Points)',
                    'first_date': 'March 29, 1967'
                }
            }
        },
        'unemployment': {
            'code': 'UNEMP',
            'description': 'Unemployment Rate (Level; Percentage Points)',
            'first_date': 'March 29, 1967'
        },
        'cpi': {
            'options': {
                'headline': {
                    'code': 'gPCPI',
                    'description': 'Headline CPI Inflation (Q/Q; Annualized Percentage Points)',
                    'first_date': 'February 5, 1986'
                },
                'core': {
                    'code': 'gPCPIX',
                    'description': 'Core CPI Inflation (Q/Q; Annualized Percentage Points)',
                    'first_date': 'February 5, 1986'
                }
            }
        },
        'pce': {
            'options': {
                'headline': {
                    'code': 'gPPCE',
                    'description': 'Headline PCE Inflation (Q/Q; Annualized Percentage Points)',
                    'first_date': 'January 27, 2000'
                },
                'core': {
                    'code': 'gPPCEX',
                    'description': 'Core PCE Inflation (Q/Q; Annualized Percentage Points)',
                    'first_date': 'January 27, 2000'
                }
            }
        },
        'consumption': {
            'code': 'gRPCE',
            'description': 'Real Personal Consumption Expenditures (Q/Q Growth; Annualized Percentage Points)',
            'first_date': 'June 14, 1978'
        },
        'investment': {
            'options': {
                'business': {
                    'code': 'gRBF',
                    'description': 'Real Business Fixed Investment (Q/Q Growth; Annualized Percentage Points)',
                    'first_date': 'June 14, 1978'
                },
                'residential': {
                    'code': 'gRRES',
                    'description': 'Real Residential Investment (Q/Q Growth; Annualized Percentage Points)',
                    'first_date': 'June 14, 1978'
                }
            }
        },
        'government': {
            'options': {
                'federal': {
                    'code': 'gRGOVF',
                    'description': 'Real Federal Government C and GI (Q/Q Growth; Annualized Percentage Points)',
                    'first_date': 'June 14, 1978'
                },
                'state_local': {
                    'code': 'gRGOVSL',
                    'description': 'Real State and Local Government C and GI (Q/Q Growth; Annualized Percentage Points)',
                    'first_date': 'June 14, 1978'
                }
            }
        },
        'housing': {
            'code': 'HSTART',
            'description': 'Housing Starts (Level; Millions of Units; Annual Rate)',
            'first_date': 'April 26, 1967'
        },
        'industrial_production': {
            'code': 'gIP',
            'description': 'Industrial Production Index (Q/Q Growth; Annualized Percentage Points)',
            'first_date': 'April 26, 1967'
        }
    }

    def __init__(self):
        """Initialize the variable mapper."""
        self.bucket_manager = BucketManager(bucket_name="greenbook-forecasts")
        api_key = get_groq_api_key()
        self.client = groq.Groq(api_key=api_key)
        self._ensure_mapping_in_bucket()

    def _ensure_mapping_in_bucket(self):
        """Ensure the variable mapping exists in the bucket."""
        try:
            mapping = self.bucket_manager.get_content("variable_mapping.json")
        except:
            # If not found, store the default mapping
            self.bucket_manager.upload_file(
                file_content=json.dumps(self.VARIABLES_DICT, indent=2).encode(),
                file_path="variable_mapping.json",
                metadata={
                    'content_type': 'application/json',
                    'description': 'Mapping of user-friendly terms to Greenbook variable codes'
                }
            )

    def _format_variables_for_prompt(self) -> str:
        """Format variables dictionary for the LLM prompt."""
        lines = []
        for key, value in self.VARIABLES_DICT.items():
            if 'options' in value:
                for opt_key, opt_value in value['options'].items():
                    lines.append(f"- {key} ({opt_key}): {opt_value['description']}")
            else:
                lines.append(f"- {key}: {value['description']}")
        return "\n".join(lines)

    def match_variable(self, query: str) -> List[Dict]:
        """Match user query to variables using LLM."""
        variables_list = self._format_variables_for_prompt()
        prompt = GROQ_PROMPT.format(variables_list=variables_list, query=query)
        
        try:
            completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="mixtral-8x7b-32768",
                temperature=0.1,
                max_tokens=500
            )
            
            result = json.loads(completion.choices[0].message.content)
            return result['matches']
            
        except Exception as e:
            logger.error(f"Error matching variable with LLM: {str(e)}")
            # Fallback to fuzzy matching
            return self._fuzzy_match(query)

    def _fuzzy_match(self, query: str) -> List[Dict]:
        """Fallback fuzzy string matching when LLM fails."""
        matches = []
        
        for key, value in self.VARIABLES_DICT.items():
            if 'options' in value:
                for opt_key, opt_value in value['options'].items():
                    score = fuzz.token_set_ratio(query.lower(), f"{key} {opt_key} {opt_value['description']}")
                    if score > 70:  # Threshold for relevance
                        matches.append({
                            'variable_key': f"{key}.{opt_key}",
                            'confidence': score / 100,
                            'reasoning': 'Matched using fuzzy string matching'
                        })
            else:
                score = fuzz.token_set_ratio(query.lower(), f"{key} {value['description']}")
                if score > 70:
                    matches.append({
                        'variable_key': key,
                        'confidence': score / 100,
                        'reasoning': 'Matched using fuzzy string matching'
                    })
        
        return sorted(matches, key=lambda x: x['confidence'], reverse=True)

    def get_variable_code(self, variable_key: str) -> Optional[str]:
        """Get the Greenbook variable code from a variable key."""
        if '.' in variable_key:
            main_key, sub_key = variable_key.split('.')
            return self.VARIABLES_DICT[main_key]['options'][sub_key]['code']
        return self.VARIABLES_DICT[variable_key]['code']

    def get_variable_info(self, variable_key: str) -> Optional[Dict]:
        """Get full variable information from a variable key."""
        if '.' in variable_key:
            main_key, sub_key = variable_key.split('.')
            return self.VARIABLES_DICT[main_key]['options'][sub_key]
        return self.VARIABLES_DICT[variable_key] 