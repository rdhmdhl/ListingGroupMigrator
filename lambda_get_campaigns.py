import sys
# used for local testing
# sys.path.append('/Users/reidhommedahl/github/lambda_layer/python/')
import json
from get_campaigns import main as get_campaigns_main
from initialize_google_ads_client import initialize_google_ads_client as initialize_google_ads_client_main

def lambda_handler(event, context):
    client = initialize_google_ads_client_main()
    customer_id = '9084369246'
    get_campaigns_main(client, customer_id)

lambda_handler(None, None)