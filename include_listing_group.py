from google.ads.googleads.errors import GoogleAdsException
from fetch_and_print_product_tree import fetch_and_print_partition_tree
def include_listing_group(client, customer_id, campaign_id, product_id, generic_asset_group_resource_name, asset_group_name):
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

    if not asset_group_name or not isinstance(asset_group_name, str) or asset_group_name.strip() == "":
        print("Invalid or empty asset group name provided.")
        return False

    asset_group_resource_name_to_include, asset_group_name = fetch_asset_group_resource_name(client, customer_id, campaign_id, product_id, generic_asset_group_resource_name, asset_group_name)
    if not asset_group_resource_name_to_include:
        print(f"No asset group found for product ID: {product_id} within campaign ID: {campaign_id}")
        return False 

    # Exisiting filter resource name identifies the specific listing group filter we want to modify or remove. Having the precise resource name ensures operations only affect the intended target

    # Parent listing group filter resource name identifies the parent node of the listing group we're working with. In the hierarchy of product groups, each node (except the root) has a parent. 

    # When you add a new node (product group), you need to specify where in the hierarchy it should be placed. This is done by linking it to its parent node. The parent_listing_group_filter_resource_name ensures that your new node is correctly positioned in the hierarchy. Removing a node could remove all it's child nodes as well without understanding this hierarchy.
    existing_filter_resource_name, parent_listing_group_filter_resource_name = fetch_existing_filter_details(client, customer_id, campaign_id, product_id, generic_asset_group_resource_name, asset_group_name)

    # check to see if there is a filter for this product already, if so, proceed with the inclusion
    if existing_filter_resource_name and parent_listing_group_filter_resource_name:
        print("adding to the asset group... ", asset_group_name)
        # fetch_and_print_partition_tree(client, customer_id, existing_filter_resource_name)
        print("asset group listing group filter: ", existing_filter_resource_name)
        # Remove the existing filter
        remove_operation = client.get_type("MutateOperation")
        remove_operation.asset_group_listing_group_filter_operation.remove = existing_filter_resource_name
        operations.append(remove_operation)
        # Create the new included filter
        create_operation = client.get_type("MutateOperation")
        create = create_operation.asset_group_listing_group_filter_operation.create
        create.type_ = client.enums.ListingGroupFilterTypeEnum.UNIT_INCLUDED
        create.asset_group = asset_group_resource_name_to_include
        create.vertical = "SHOPPING"
        create.case_value.product_item_id.value = product_id
        create.parent_listing_group_filter = parent_listing_group_filter_resource_name
        operations.append(create_operation)
        # Execute the operations
        try:
            print(f"trying to include the product id {product_id} in asset group: {asset_group_name}\n")
            print(f"include opperations here: {operations}\n")
            response = googleads_service.mutate(customer_id=customer_id, mutate_operations=operations)
            print(f"response from include mutation: {response}")
            return True
        except GoogleAdsException as ex:
            print(f"An error occurred: {ex}")
            return False
    else:
        # Log or handle the case where no existing filter was found
        print(f"No existing filter found for product ID: {product_id} in campaign ID: {campaign_id}. Product will not be included.")
        return False
    
# FINDING THE PRODUCT WITHIN THE NON-GENERIC ASSET GROUP    
def fetch_asset_group_resource_name(client, customer_id, campaign_id, product_id, generic_asset_group_resource_name, asset_group_name):
    ga_service = client.get_service("GoogleAdsService")
    query = f"""
    SELECT
        asset_group.name,
        asset_group.resource_name
    FROM asset_group_product_group_view
    WHERE campaign.id = {campaign_id}
    AND asset_group.name LIKE '%{asset_group_name}%'
    AND asset_group_listing_group_filter.case_value.product_item_id.value = '{product_id}'
    AND asset_group.resource_name NOT IN ('{generic_asset_group_resource_name}')
    LIMIT 1
    """
    try:
        response = ga_service.search(customer_id=customer_id, query=query)
        for row in response:
            return row.asset_group.resource_name, row.asset_group.name
    except GoogleAdsException as ex:
        print(f"An error occurred while fetching the asset group resource name for product ID {product_id}, within campaign ID: {campaign_id}: {ex}")
        return None

# FINDING THE LISTING GROUP FILTER & PARENT LISTING GROUP FILTER WITHIN THE NON-GENERIC ASSET GROUP   
def fetch_existing_filter_details(client, customer_id, campaign_id, product_id, generic_asset_group_resource_name, asset_group_name):
    ga_service = client.get_service("GoogleAdsService")
    query = f"""
    SELECT    
        asset_group.resource_name,
        asset_group_listing_group_filter.resource_name,
        asset_group_listing_group_filter.parent_listing_group_filter,
        asset_group_listing_group_filter.case_value.product_item_id.value
    FROM asset_group_product_group_view
    WHERE campaign.id = {campaign_id}
    AND asset_group.name LIKE '%{asset_group_name}%'
    AND asset_group_listing_group_filter.case_value.product_item_id.value = '{product_id}'
    AND asset_group.resource_name NOT IN ('{generic_asset_group_resource_name}')
    LIMIT 1
    """

    try:
        response = ga_service.search(customer_id=customer_id, query=query)
        for row in response:
            return row.asset_group_listing_group_filter.resource_name, row.asset_group_listing_group_filter.parent_listing_group_filter
    except GoogleAdsException as ex:
        print(f"An error occurred while fetching the existing filter details: {ex}")
        return None, None