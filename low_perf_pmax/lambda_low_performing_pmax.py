import sys
# used for local testing
# sys.path.append('/Users/reidhommedahl/github/lambda_layer/python/')
import json
from fetch_listing_groups_low_performing import fetch_existing_listing_groups as fetch_listing_groups_low_performing
from common.initialize_google_ads_client import initialize_google_ads_client as initialize_google_ads_client_main
import os
# from dotenv import load_dotenv
# load env variables
# load_dotenv()

def lambda_handler(event, context):
    try:
        client = initialize_google_ads_client_main()
        customer_id = os.getenv("CID")
        if not customer_id:
            raise ValueError("Customer ID not set in environment variables")

        to_emails = os.getenv("TO_EMAIL_ADDRESSES")
        if not to_emails:
            raise ValueError("To email addresses not set in environment variables")

        fetch_listing_groups_low_performing(client, customer_id, to_emails)
        return {"status": "Success"}
    except Exception as e:
        return {"error": str(e), "status": "Failed"}

lambda_handler(None, None)