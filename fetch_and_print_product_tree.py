from collections import defaultdict


all_children = set()

def fetch_and_print_partition_tree(client, customer_id, asset_group_listing_group_filter_name):
    ga_service = client.get_service("GoogleAdsService")

    # Ensure the resource name is properly formatted as a string for the query
    formatted_resource_name = f"'{asset_group_listing_group_filter_name}'"
    # Split by '/' and then by '~'
    parts = formatted_resource_name.split('/')
    last_part = parts[-1]  # Get the last part after splitting by '/'
    asset_group_id = last_part.split('~')[0]  # Split by '~' and get the last part

    print("Asset Group ID: ", asset_group_id)  # Output: 11450422096

        # Create the query to fetch the structure of listing groups
    query = f"""
    SELECT
        asset_group.resource_name,
        asset_group_listing_group_filter.resource_name,
        asset_group_listing_group_filter.parent_listing_group_filter,
        asset_group_listing_group_filter.type,
        asset_group_listing_group_filter.case_value.product_item_id.value,
        asset_group_listing_group_filter.case_value.product_type.value
    FROM asset_group_listing_group_filter
    WHERE asset_group_listing_group_filter.asset_group = 'customers/{customer_id}/assetGroups/{asset_group_id}'
    """

    # Execute the query
    response = ga_service.search(customer_id=customer_id, query=query)
    
    # Build the tree structure (this is a simplified representation)
    tree = {}
    children_of = defaultdict(set)

    asset_group_name = fetch_asset_group_name(client, customer_id, asset_group_id)
    if asset_group_name:
        print(f"Asset Group Name: {asset_group_name}")
    else:
        print("Asset group not found.")

    for row in response:
        node = row.asset_group_listing_group_filter
        # print("node: ", node)
        # print(f"Resource Name: {node.resource_name}, Type: {node.type_}, Product Item ID: {node.case_value.product_item_id.value}")
        # Determine the status based on the type of the filter
        # if node.type_ == client.enums.ListingGroupFilterTypeEnum.UNIT_INCLUDED:
        #     status = 'INCLUDED'
        # elif node.type_ == client.enums.ListingGroupFilterTypeEnum.UNIT_EXCLUDED:
        #     status = 'EXCLUDED'
        # else:
        #     status = 'OTHER'  # or handle subdivisions or other types as needed
        
        tree[node.resource_name] = {
            'type': node.type_,
            'parent': node.parent_listing_group_filter,
            'asset_group': asset_group_name,
            'product_item_id': node.case_value.product_item_id.value,
            'product_type': node.case_value.product_type.value,
            # 'status': status,
            'children': []
            # Add other relevant fields here
        }

        # Add the node to its parent's list of children
        if node.parent_listing_group_filter:
            children_of[node.parent_listing_group_filter].add(node.resource_name)
            all_children.add(node.resource_name)  # Add to the set of all children

        # Now populate the 'children' field for each node
        for parent, children in children_of.items():
            if parent in tree:  # Check if the parent is in the tree
                tree[parent]['children'] = list(children)

    # Print the tree
    # print_partition_tree(tree)

def print_partition_tree(tree, resource_name=None, level=0):
    if resource_name is None:
        # Find the root node(s) and start the recursion
        for resource_name, node in tree.items():
            if resource_name not in all_children:
                print_partition_tree(tree, resource_name, level)
    else:
        node = tree[resource_name]
        indent = '  ' * level
        if node['type'] == 4:
            included_or_excluded = 'UNIT_EXCLUDED'
        elif node['type'] == 3:
            included_or_excluded = 'UNIT_INCLUDED'
        elif node['type'] == 2:
            included_or_excluded = 'SUBDIVISION'

        # Prepare the string to print for the current node
        node_info = f"{indent}{included_or_excluded} - {node['product_item_id'] or node['product_type'] or 'All products'}"
        node_info += f" | Asset Group: {node['asset_group']}"
        
        print(node_info)

       # Recursively print child nodes
        if node['children']:  # Debug print
            print(f"{indent}Children of {resource_name}: {node['children']}")  # Debug print
        for child_resource_name in node['children']:
            print_partition_tree(tree, child_resource_name, level + 1)

def fetch_asset_group_name(client, customer_id, asset_group_id):
    ga_service = client.get_service("GoogleAdsService")

    # Create the query to fetch the asset group name
    query = f"""
    SELECT
        asset_group.name
    FROM asset_group
    WHERE asset_group.id = {asset_group_id}
    LIMIT 1
    """
    response = ga_service.search(customer_id=customer_id, query=query)

    # Process the response to extract the asset group name
    for row in response:
        return row.asset_group.name

    return None  # Return None if no name is found
