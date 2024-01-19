from google.ads.googleads.errors import GoogleAdsException

def include_listing_group(client, customer_id, campaign_id, product_id):

    """
    Includes a product in a listing group of a specified campaign. Used for moving products from the normal pmax campaign, to the low-performing pmax campaign, or vice versa

    Args:
        client (GoogleAdsClient): The Google Ads API client.
        customer_id (str): The Google Ads customer ID.
        campaign_id (str): The ID of the campaign where the product will be included.
        product_id (str): The ID of the product to include.

    Returns:
        bool: True if the operation was successful, False otherwise. Used to determine if product was successfully included
    """

    # initialize an array to store our information
    operations = []
    googleads_service = client.get_service("GoogleAdsService")

    asset_group_resource_name = fetch_asset_group_resource_name(client, customer_id, campaign_id, product_id)
    if not asset_group_resource_name:
        print(f"No asset group found for campaign ID: {campaign_id}")
        return False

    existing_filter_resource_name, parent_listing_group_filter_resource_name = fetch_existing_filter_details(client, customer_id, campaign_id, product_id)

    if existing_filter_resource_name:
        remove_operation = client.get_type("MutateOperation")
        remove_operation.asset_group_listing_group_filter_operation.remove = existing_filter_resource_name
        operations.append(remove_operation)

    # Create the new included filter
    create_operation = client.get_type("MutateOperation")
    create = create_operation.asset_group_listing_group_filter_operation.create
    create.type_ = client.enums.ListingGroupFilterTypeEnum.UNIT_INCLUDED
    create.asset_group = asset_group_resource_name
    create.vertical = "SHOPPING"
    create.case_value.product_item_id.value = product_id
    create.parent_listing_group_filter = parent_listing_group_filter_resource_name
    operations.append(create_operation)

    # Execute the operations
    try:
        response = googleads_service.mutate(customer_id=customer_id, mutate_operations=operations)
        print(f"Product ID: {product_id} included in campaign ID: {campaign_id}.")
        return True
    except GoogleAdsException as ex:
        print(f"An error occurred: {ex}")
        return False
    
def fetch_asset_group_resource_name(client, customer_id, campaign_id, product_id):
    ga_service = client.get_service("GoogleAdsService")
    query = f"""
    SELECT
        asset_group.resource_name
    FROM asset_group_product_group_view
    WHERE campaign.id = {campaign_id}
    AND asset_group_listing_group_filter.case_value.product_item_id.value = '{product_id}'
    LIMIT 1
    """
    try:
        response = ga_service.search(customer_id=customer_id, query=query)
        for row in response:
            return row.asset_group.resource_name
    except GoogleAdsException as ex:
        print(f"An error occurred while fetching the asset group resource name for product ID {product_id}, within campaign ID: {campaign_id}: {ex}")
        return None
    
def fetch_existing_filter_details(client, customer_id, campaign_id, product_id):
    ga_service = client.get_service("GoogleAdsService")
    query = f"""
    SELECT    
        asset_group_listing_group_filter.resource_name,
        asset_group_listing_group_filter.parent_listing_group_filter,
        asset_group_listing_group_filter.case_value.product_item_id.value
    FROM asset_group_product_group_view
    WHERE campaign.id = {campaign_id}
    AND asset_group_listing_group_filter.case_value.product_item_id.value = '{product_id}'
    LIMIT 1
    """

    try:
        response = ga_service.search(customer_id=customer_id, query=query)
        for row in response:
            return row.asset_group_listing_group_filter.resource_name, row.asset_group_listing_group_filter.parent_listing_group_filter
    except GoogleAdsException as ex:
        print(f"An error occurred while fetching the existing filter details: {ex}")
        return None, None
    