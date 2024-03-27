import sys
# used for local testing
# sys.path.append('/Users/reidhommedahl/github/lambda_layer/python/')
import json
from fetch_listing_groups_low_performing import fetch_existing_listing_groups as fetch_listing_groups_low_performing
from initialize_google_ads_client import initialize_google_ads_client as initialize_google_ads_client_main
import os
from dotenv import load_dotenv
# load env variables
load_dotenv()

def lambda_handler(event, context):
    client = initialize_google_ads_client_main()
    customer_id = os.getenv("CID")
    to_emails = os.getenv("TO_EMAIL_ADDRESSES")
    fetch_listing_groups_low_performing(client, customer_id, to_emails)

lambda_handler(None, None)