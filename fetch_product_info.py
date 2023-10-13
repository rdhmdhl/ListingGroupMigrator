from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

def get_product_info(client, customer_id, asset_group_id, resource_name):
    try:
        ga_service = client.get_service("GoogleAdsService")

        # Create the query
        query = f"""
            SELECT
                asset_group_listing_group_filter.case_value.product_type.value,
                asset_group_listing_group_filter.case_value.product_item_id.value
            FROM asset_group_product_group_view
            WHERE asset_group.id = {asset_group_id}
            AND asset_group_listing_group_filter.resource_name = '{resource_name}'
        """

        # Execute the query
        response = ga_service.search(customer_id=customer_id, query=query)

        # Process the response
        for row in response:
            product_type = row.asset_group_listing_group_filter.case_value.product_type.value
            product_item_id = row.asset_group_listing_group_filter.case_value.product_item_id.value

            print(f" Product Type: {product_type}, Product Item ID: {product_item_id}")

    except GoogleAdsException as ex:
        print(f"An error occurred: {ex}")
