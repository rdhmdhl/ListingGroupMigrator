from google.ads.googleads.errors import GoogleAdsException

# TODO: CHANGE THIS FROM REMOVING AND CREATING, TO UPDATING 

def exclude_listing_group(client, customer_id, filter_resource_name, asset_group_resource_name, product_id, parent_listing_group_filter_resource_name):
    # initialize an array to store our information
    operations = []

    # create a removal operation for the existing filter
    remove_operation = client.get_type("MutateOperation")
    # This should be the specific filter's resource name to remove
    remove_operation.asset_group_listing_group_filter_operation.remove = filter_resource_name  
    operations.append(remove_operation)
 
    # Create the new exclusion filter 
    # with the temporary ID as its parent
    create_operation = client.get_type("MutateOperation")
    create = create_operation.asset_group_listing_group_filter_operation.create
    # excluding product from asset group :)
    create.type_ = client.enums.ListingGroupFilterTypeEnum.UNIT_EXCLUDED
    # passed down as a parameter
    create.asset_group = asset_group_resource_name
    # always shopping for pmax retail
    create.vertical = "SHOPPING"
    # determine what value to filter on, using product item ID here
    # this is what we want to exclude, based on ROAS
    create.case_value.product_item_id.value = product_id
    # the resource name of the parent listing group filter
    create.parent_listing_group_filter = parent_listing_group_filter_resource_name 
    operations.append(create_operation)

    # Get the Google Ads service
    googleads_service = client.get_service("GoogleAdsService")

    try:
        # Execute the operations
        response = googleads_service.mutate(customer_id=customer_id, mutate_operations=operations)
        print(f"trying to exclude the product id: ", product_id)
        print("Successfully executed operations.")
        return True
    except GoogleAdsException as ex:
        print(f"An error occurred: {ex}")
        return False