"""
AWS Secrets Manager utilities.
"""
import logging
import boto3
import json
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

def get_secret(secret_name: str, key: str = None) -> str:
    """Get a secret value from AWS Secrets Manager.
    
    Args:
        secret_name: Name of the secret in AWS Secrets Manager
        key: Optional key if the secret is stored as JSON
    """
    try:
        session = boto3.session.Session()
        client = session.client('secretsmanager')
        response = client.get_secret_value(SecretId=secret_name)
        secret = response['SecretString']
        
        # Try to parse as JSON
        try:
            secret_dict = json.loads(secret)
            # If a specific key is requested, return that
            if key and isinstance(secret_dict, dict):
                return secret_dict[key]
            # If it's a dict but no key specified, return the whole dict
            if isinstance(secret_dict, dict):
                return secret_dict
        except json.JSONDecodeError:
            # If not JSON, return as is
            return secret
            
    except ClientError as e:
        logger.error(f"Error getting secret '{secret_name}': {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting secret '{secret_name}': {str(e)}")
        raise 