import pytest
import boto3
from macroeconomic_data.utils.aws import list_secrets
from macroeconomic_data.config.settings import settings
from botocore.exceptions import ClientError

def test_aws_secrets_comprehensive():
    """Comprehensive test of AWS Secrets Manager access and configuration"""
    client = boto3.client('secretsmanager', region_name=settings.AWS_REGION)
    
    # 1. Test AWS credentials
    session = boto3.Session()
    credentials = session.get_credentials()
    region = session.region_name
    
    print(f"\n1. AWS Configuration:")
    print(f"  Region: {region}")
    print(f"  Credentials from: {credentials.method}")
    
    # 2. Try direct access to FRED_API_KEY
    print("\n2. Direct access to FRED_API_KEY:")
    try:
        response = client.describe_secret(SecretId='FRED_API_KEY')
        print("  Secret exists!")
        print(f"  ARN: {response['ARN']}")
        print(f"  Name: {response['Name']}")
        print(f"  Last Changed: {response.get('LastChangedDate')}")
        
        # Try to get the actual value
        value_response = client.get_secret_value(SecretId='FRED_API_KEY')
        print("  ✓ Secret value is accessible")
        
    except ClientError as e:
        print(f"  ✗ Error: {e.response['Error']['Message']}")
    
    # 3. List all secrets
    print("\n3. All available secrets:")
    try:
        all_secrets = []
        paginator = client.get_paginator('list_secrets')
        
        for page in paginator.paginate():
            all_secrets.extend(page['SecretList'])
        
        print(f"  Found {len(all_secrets)} secrets:")
        for secret in sorted(all_secrets, key=lambda x: x['Name']):
            print(f"  - {secret['Name']}")
            # Print additional details if it's our target secret
            if secret['Name'] == 'FRED_API_KEY':
                print(f"    ARN: {secret['ARN']}")
                print(f"    Last Changed: {secret.get('LastChangedDate')}")
                if 'DeletedDate' in secret:
                    print(f"    ⚠️ Marked as deleted on: {secret['DeletedDate']}")
    
    except ClientError as e:
        print(f"  ✗ Error listing secrets: {e.response['Error']['Message']}")
    
    # 4. Test actual secret usage
    print("\n4. Testing secret in application context:")
    try:
        from macroeconomic_data.core.fred_client import FREDClient
        client = FREDClient()
        print("  ✓ FREDClient initialized successfully")
        
        # Try a simple API call
        gdp = client.get_series('GDP', limit=1)
        print("  ✓ Successfully made API call to FRED")
        
    except Exception as e:
        print(f"  ✗ Error using FRED client: {str(e)}") 