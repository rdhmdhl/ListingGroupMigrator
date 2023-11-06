from google.ads.googleads.errors import GoogleAdsException

# def generate_remove_operations(client, resource_names_to_remove):
#     operations = []
#     for resource_name in resource_names_to_remove:
#         remove_operation = client.get_type("MutateOperation")
#         remove_operation.asset_group_listing_group_filter_operation.remove = resource_name  
#         operations.append(remove_operation)
#     return operations


def exclude_listing_group(client, customer_id, filter_resource_name, asset_group_resource_name, product_id, parent_listing_group_filter_resource_name):
    # initialize an array to store our information
    operations = []

    # create a removal operation for the existing filter
    remove_operation = client.get_type("MutateOperation")
    remove_operation.asset_group_listing_group_filter_operation.remove = filter_resource_name  # This should be the specific filter's resource name to remove
    operations.append(remove_operation)

    # Create the new exclusion filter with the temporary ID as its parent
    create_operation = client.get_type("MutateOperation")
    create = create_operation.asset_group_listing_group_filter_operation.create
    create.type_ = client.enums.ListingGroupFilterTypeEnum.UNIT_EXCLUDED
    create.asset_group = asset_group_resource_name
    create.vertical = "SHOPPING"
    create.case_value.product_item_id.value = product_id
    create.parent_listing_group_filter = parent_listing_group_filter_resource_name  # The resource name of the parent listing group filter
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