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

        combined_id = None # initializing variable
        listing_group_filter_id = None # initializing variable

        # Process the response
        for row in response:

            resource_name = row.asset_group_listing_group_filter.resource_name
            parts = resource_name.split("/")
            # Get the last part of the resource_name
            combined_id = parts[-1]  
            # seperate the asset id from listing filter id
            seperate_listing_asset_id = combined_id.split("~")
            # Get the listing group filter id from both
            listing_group_filter_id = seperate_listing_asset_id[1]  

            product_item_id = row.asset_group_listing_group_filter.case_value.product_item_id.value
            # print(f"combined ids: ", combined_id)
            # print(f"listing group filter id: {listing_group_filter_id}, Product Item ID: {product_item_id}")

        return check_and_update_listing_group_status(client, customer_id, listing_group_filter_id, resource_name)

    except GoogleAdsException as ex:
        print(f"An error occurred: {ex}")


def check_and_update_listing_group_status(client, customer_id, listing_group_filter_id, resource_name):
    try:

        filter_type_map = {
            3: 'UNIT_INCLUDED',
            4: 'UNIT_EXCLUDED',
            # add more mapping here as needed
        }
                
        google_ads_service = client.get_service("GoogleAdsService")
        
        query = f"""
        SELECT 
            asset_group_listing_group_filter.type
        FROM 
            asset_group_listing_group_filter
        WHERE 
            asset_group_listing_group_filter.resource_name = '{resource_name}'
        """
        
        response = google_ads_service.search(customer_id=customer_id, query=query)
        
        for row in response:
            filter_type = filter_type_map.get(row.asset_group_listing_group_filter.type_, 'UNKNOWN')
            return filter_type

    except GoogleAdsException as ex:
        print(f"An error occurred: {ex}")