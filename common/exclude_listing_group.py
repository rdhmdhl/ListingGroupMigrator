from google.ads.googleads.errors import GoogleAdsException

def exclude_listing_group(client, customer_id, campaign_id, product_id, generic_asset_group_resource_name, asset_group_listing_group_resource_name):
    # Exisiting filter resource name identifies the specific listing group filter we want to modify or remove. Having the precise resource name ensures operations only affect the intended target

    # Parent listing group filter resource name identifies the parent node of the listing group we're working with. In the hierarchy of product groups, each node (except the root) has a parent. 

    # When you add a new node (product group), you need to specify where in the hierarchy it should be placed. This is done by linking it to its parent node. The parent_listing_group_filter_resource_name ensures that your new node is correctly positioned in the hierarchy. Removing a node could remove all it's child nodes as well without understanding this hierarchy.
    # initialize an array to store our information
    operations = []
    googleads_service = client.get_service("GoogleAdsService")
    # asset_group_listing_group_resource_name is from the main file, where the listing group data is fetched
    existing_listing_group_filter_resource_name = asset_group_listing_group_resource_name 
    if not asset_group_listing_group_resource_name:
        print(f"No asset group listing group resource name provided to the exclude file")
        return False

    # TODO: look to see if this function is correct
    asset_group_resource_name_to_exclude, asset_group_name = fetch_asset_group_resource_name(client, customer_id, campaign_id, product_id, generic_asset_group_resource_name, existing_listing_group_filter_resource_name)
    if not asset_group_resource_name_to_exclude:
        print(f"No asset group found for campaign ID: {campaign_id}")
        return False
    
    parent_listing_group_filter_resource_name = fetch_existing_filter_details(client, customer_id, campaign_id, product_id, generic_asset_group_resource_name, existing_listing_group_filter_resource_name)
    if not parent_listing_group_filter_resource_name:
        print(f"No parent listing group filter found for the specified filter: {existing_listing_group_filter_resource_name}")
        return False

    # only proceed if there is an exising filter resource name, and a parent filter resource name
    if existing_listing_group_filter_resource_name and parent_listing_group_filter_resource_name:
        
        # create a removal operation for the existing filter
        remove_operation = client.get_type("MutateOperation")
        # This should be the specific filter's resource name to remove
        remove_operation.asset_group_listing_group_filter_operation.remove = existing_listing_group_filter_resource_name
        operations.append(remove_operation)
        # Create the new exclusion filter 
        create_operation = client.get_type("MutateOperation")
        create = create_operation.asset_group_listing_group_filter_operation.create
        create.type_ = client.enums.ListingGroupFilterTypeEnum.UNIT_EXCLUDED
        
        create.asset_group = asset_group_resource_name_to_exclude
        # always shopping for pmax retail
        create.vertical = "SHOPPING"
        # determine what value to filter on, using product item ID here
        # this is what we want to exclude, based on ROAS
        create.case_value.product_item_id.value = product_id
        # the resource name of the parent listing group filter
        create.parent_listing_group_filter = parent_listing_group_filter_resource_name 
        operations.append(create_operation)

        try:
            print(f"trying to exclude the product id {product_id} in asset group: {asset_group_name}\n")
            print(f"exclude opperations here: {operations}\n")
            # Execute the operations
            response = googleads_service.mutate(customer_id=customer_id, mutate_operations=operations)
            print(f"response from exlude mutation: {response}")
            return True
        except GoogleAdsException as ex:
            print(f"An error occurred: {ex} when trying to exclude product {product_id} from asset group: {asset_group_name}")
            return False
    else:
        return False
    
def fetch_asset_group_resource_name(client, customer_id, campaign_id, product_id, generic_asset_group_resource_name, existing_listing_group_filter_resource_name):
    ga_service = client.get_service("GoogleAdsService")
    query = f"""
    SELECT
        asset_group.name,
        asset_group.resource_name,
        asset_group_listing_group_filter.parent_listing_group_filter
    FROM asset_group_product_group_view
    WHERE campaign.id = {campaign_id}
    AND asset_group_listing_group_filter.case_value.product_item_id.value = '{product_id}'
    AND asset_group_listing_group_filter.resource_name = '{existing_listing_group_filter_resource_name}'
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

def fetch_existing_filter_details(client, customer_id, campaign_id, product_id, generic_asset_group_resource_name, existing_listing_group_filter_resource_name):
    ga_service = client.get_service("GoogleAdsService")
    query = f"""
    SELECT    
        asset_group_listing_group_filter.resource_name,
        asset_group_listing_group_filter.parent_listing_group_filter,
        asset_group_listing_group_filter.case_value.product_item_id.value
    FROM asset_group_product_group_view
    WHERE campaign.id = {campaign_id}
    AND asset_group_listing_group_filter.case_value.product_item_id.value = '{product_id}'
    AND asset_group_listing_group_filter.resource_name = '{existing_listing_group_filter_resource_name}'
    AND asset_group.resource_name NOT IN ('{generic_asset_group_resource_name}')
    LIMIT 1
    """

    try:
        response = ga_service.search(customer_id=customer_id, query=query)
        for row in response:
            return row.asset_group_listing_group_filter.parent_listing_group_filter
    except GoogleAdsException as ex:
        print(f"An error occurred while fetching the existing filter details: {ex}")
        return None, None
    
