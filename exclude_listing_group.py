
def generate_remove_operations(client, resource_names_to_remove):
    operations = []
    for resource_name in resource_names_to_remove:
        remove_operation = client.get_type("MutateOperation")
        remove_operation.asset_group_listing_group_filter_operation.remove = resource_name  
        operations.append(remove_operation)
    return operations


def exclude_listing_group(client, customer_id, filter_resource_name, asset_group_resource_name, product_id):

    print(f"filter resource name: ", filter_resource_name)
    print(f"asset group resource name: ", asset_group_resource_name)
    remove_operations = generate_remove_operations(client, [filter_resource_name])

    operations = []
    operations.extend(remove_operations)

    # Add new unit with 'UNIT_EXCLUDED'
    add_unit_operation = client.get_type("MutateOperation")
    add_unit = add_unit_operation.asset_group_listing_group_filter_operation.create
    # Setting the type to UNIT_EXCLUDED
    add_unit.type_ = client.enums.ListingGroupFilterTypeEnum.UNIT_EXCLUDED  
    # Setting the asset_group field
    add_unit.asset_group = asset_group_resource_name 
    add_unit.vertical = "SHOPPING"
    # Setting the case_value with product_item_id
    add_unit.case_value.product_item_id.value =  product_id
    # add the filter resource name 
    add_unit.parent_listing_group_filter = filter_resource_name

    # Before executing operations, print them for debugging.
    print(f"Executing the following operations: {operations}")
    
    # Add other necessary fields for add_unit here.
    operations.append(add_unit_operation)


    # Execute operations
    googleads_service = client.get_service("GoogleAdsService")
    response = googleads_service.mutate(customer_id=customer_id, mutate_operations=operations)
    
    # Check for errors in the response
    if 'errors' in response:
        print(f"Errors occurred: {response.errors}")
        return False
    else:
        print("Successfully executed operations.")
        return True