from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

def get_listing_group_status(client, customer_id, campaign_id, product_id, resource_name):
    try:
        ga_service = client.get_service("GoogleAdsService")
        print(f"fetching the product {product_id}, in campaign {campaign_id}, but NOT WITH resource name {resource_name}")
        # Create the query
        # use the asset_group_id and the product id to fetch the product status
        query = f"""
        SELECT    
            asset_group.name,
            asset_group.resource_name,
            asset_group_listing_group_filter.resource_name,
            asset_group_listing_group_filter.type,
            campaign.id,
            asset_group.status
        FROM asset_group_product_group_view
        WHERE campaign.id = {campaign_id}
        AND asset_group.status = 'ENABLED'
        AND asset_group_listing_group_filter.case_value.product_item_id.value = '{product_id}'
        AND asset_group.resource_name NOT IN ('{resource_name}')
        LIMIT 1
        """        
        filter_type_map = {
            3: 'UNIT_INCLUDED',
            4: 'UNIT_EXCLUDED',
            # add more mapping here as needed
        }

        # Execute the query
        response = ga_service.search(customer_id=customer_id, query=query)
        print(f"response: {response}")
        # Process the response
        for row in response:
            filter_type = filter_type_map.get(row.asset_group_listing_group_filter.type_, 'UNKNOWN')
            print(f"listing group status: {filter_type} within campaign ID: {campaign_id} and asset group {row.asset_group.name}")
            return filter_type
        
        # default value if no rows are found
        print("listing group status not found")
        return "NOT_FOUND"
        
    except GoogleAdsException as ex:
        print(f"An error occurred: {ex}")
        return 'ERROR'