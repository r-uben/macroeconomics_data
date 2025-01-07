import pytest
from macroeconomic_data.core.llm_client import LLMClient
import logging
from macroeconomic_data.utils.aws import get_secret
from macroeconomic_data.config.settings import settings
import json

logger = logging.getLogger(__name__)

def test_groq_secret():
    """Test GROQ secret retrieval and format"""
    try:
        # Get the raw secret
        secret_value = get_secret(settings.GROQ_SECRET_NAME)
        logger.info(f"\nRaw secret type: {type(secret_value)}")
        logger.info(f"Raw secret preview: {secret_value[:10]}..." if secret_value else "Empty secret")
        
        # Try to parse as JSON
        try:
            parsed = json.loads(secret_value)
            logger.info(f"Parsed as JSON: {parsed.keys()}")
        except json.JSONDecodeError:
            logger.info("Not valid JSON")
        
        # Initialize client
        client = LLMClient()
        logger.info("Successfully initialized GROQ client")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        pytest.fail(str(e)) 