import boto3
from botocore.exceptions import ClientError
import json
from ..config.settings import settings

def get_secret(secret_name: str) -> str:
    """
    Retrieve a secret from AWS Secrets Manager
    """
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=settings.AWS_REGION
    )

    try:
        response = client.get_secret_value(SecretId=secret_name)
        return response['SecretString']
    except ClientError as e:
        raise e

def list_secrets() -> list:
    """
    List all available secrets in AWS Secrets Manager
    """
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=settings.AWS_REGION
    )
    
    try:
        response = client.list_secrets()
        secrets = [secret['Name'] for secret in response['SecretList']]
        print("\nAvailable secrets in AWS Secrets Manager:")
        for secret in secrets:
            print(f"- {secret}")
        return secrets
    except ClientError as e:
        print(f"\nError listing secrets: {str(e)}")
        return [] 