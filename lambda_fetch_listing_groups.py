import sys
# used for local testing
# sys.path.append('/Users/reidhommedahl/github/lambda_layer/python/')
import json
from fetch_listing_groups_normal_pmax import fetch_existing_listing_groups as fetch_listing_groups_normal
from fetch_listing_groups_low_performing import fetch_existing_listing_groups as fetch_listing_groups_low_performing
from initialize_google_ads_client import initialize_google_ads_client as initialize_google_ads_client_main


def lambda_handler(event, context):
    client = initialize_google_ads_client_main()
    customer_id = '9084369246'
    fetch_listing_groups_normal(client, customer_id)
    # fetch_listing_groups_low_performing(client, customer_id)

lambda_handler(None, None)