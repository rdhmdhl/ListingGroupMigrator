import json
import boto3
import os
import yaml
from botocore.exceptions import ClientError
from google.ads.googleads.client import GoogleAdsClient

def get_secret():
    secret_name = "prod/google-ads-api"
    region_name = "us-west-1"

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
