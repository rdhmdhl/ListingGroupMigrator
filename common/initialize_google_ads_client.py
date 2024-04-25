import json
import boto3
import os
from botocore.exceptions import ClientError
from google.ads.googleads.client import GoogleAdsClient
import os
from dotenv import load_dotenv
# load env variables
load_dotenv()

# grab secret from AWS secrets manager, or another secure provider
def get_secret():
    secret_name = os.getenv('SECRET_NAME')
    region_name = os.getenv('REGION_NAME')

    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        raise e

    secret = get_secret_value_response['SecretString']
    return json.loads(secret)

def initialize_google_ads_client():
    secret_dict = get_secret()

    # Load the configuration directly from the JSON data
    googleads_client = GoogleAdsClient.load_from_dict(secret_dict)

    return googleads_client
