import groq
import json
import logging
from ..utils.aws import get_secret
from ..config.settings import settings

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self):
        try:
            secret_value = get_secret(settings.GROQ_SECRET_NAME)
            logger.info(f"Retrieved secret value type: {type(secret_value)}")
            logger.info(f"Secret value preview: {secret_value[:10]}..." if secret_value else "Empty secret")
            
            # Handle both JSON and plain text secrets
            try:
                parsed = json.loads(secret_value)
                logger.info(f"Parsed JSON keys: {parsed.keys()}")
                api_key = parsed['api_key']
            except json.JSONDecodeError:
                logger.info("Secret is not JSON, using as plain text")
                api_key = secret_value
            except KeyError:
                logger.error("JSON secret does not contain 'api_key' field")
                raise ValueError("Secret JSON missing 'api_key' field")
            
            if not api_key or not isinstance(api_key, str):
                logger.error(f"Invalid API key type: {type(api_key)}")
                raise ValueError(f"Invalid GROQ API key format")
                
            logger.info("Initializing GROQ client...")
            self.client = groq.Groq(api_key=api_key)
            
            # Test the connection with a simple model list
            logger.info("Testing GROQ connection...")
            try:
                models = self.client.models.list()
                available_models = []
                for model in models:
                    if hasattr(model, 'id'):
                        available_models.append(model.id)
                    elif isinstance(model, (tuple, list)) and len(model) > 0:
                        available_models.append(str(model[0]))
                    else:
                        available_models.append(str(model))
                
                logger.info(f"Available models: {available_models}")
                
                if settings.GROQ_MODEL not in available_models:
                    logger.warning(f"Configured model {settings.GROQ_MODEL} not found in available models")
                    logger.warning(f"Available models are: {available_models}")
                    
            except Exception as e:
                logger.warning(f"Could not list models: {str(e)}")
                logger.info("Continuing anyway as this might be an API limitation")
            
        except Exception as e:
            logger.error(f"GROQ initialization error: {str(e)}")
            raise ValueError(f"Failed to initialize GROQ client: {str(e)}")
    
    def get_completion(self, prompt: str, temperature: float = 0.1) -> str:
        """Get completion from LLM"""
        try:
            logger.debug(f"Sending request to GROQ with model {settings.GROQ_MODEL}")
            completion = self.client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert in economic data analysis."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=50,
                timeout=30  # Add timeout
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"GROQ completion error: {str(e)}")
            raise ValueError(f"Error getting completion from GROQ: {str(e)}") 