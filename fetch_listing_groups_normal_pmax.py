from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from fetch_product_info import get_product_info as get_product_info_main
from exclude_listing_group import exclude_listing_group as exclude_listing_group_main
from include_listing_group import include_listing_group as include_listing_group_main
import datetime
from email_sender import send_email

def fetch_existing_listing_groups(client, customer_id):
    try:
        ga_service = client.get_service("GoogleAdsService")

        # Calculate the last 30 days
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=30)
        print("first query for fetch_existing_listing_groups")
        # Create the query
        query = f"""
        SELECT
            asset_group.id,
            asset_group.name,
            asset_group_listing_group_filter.resource_name,
            asset_group_listing_group_filter.parent_listing_group_filter,
            asset_group_listing_group_filter.case_value.product_item_id.value,
            campaign.id,
            campaign.name,
            metrics.cost_micros,
            metrics.conversions_value
        FROM asset_group_product_group_view
        WHERE campaign.id = {20510025794}
        AND metrics.cost_micros > 2000000000
        AND segments.date BETWEEN '{start_date}' AND '{end_date}'
        AND asset_group_listing_group_filter.case_value.product_item_id.value IS NOT NULL
        """
        
        # Execute the query
        response = ga_service.search(customer_id=customer_id, query=query)
        # initialize email body variable
        email_body = ""

        print("response ", response)
        # Process the response
        for row in response:
            # Convert cost from micros to dollars and round to 2 decimal places
            real_cost = round(row.metrics.cost_micros / 1_000_000, 2)

            # Convert conversion value to dollars and round to 2 decimal places
            conversion_value = round(row.metrics.conversions_value, 2)

            # Calculate and round ROAS to 2 decimal places
            roas = round(row.metrics.conversions_value / real_cost, 2)

            # print(f"cost {real_cost}")
            # print(f"roas {roas}")

            if real_cost != 0:
                if roas < 7:
                    # Get product information for this listing group
                    asset_group_id = row.asset_group.id
                    # filter resource name
                    filter_resource_name = row.asset_group_listing_group_filter.resource_name
                    # asset group resource name
                    asset_group_resource_name = row.asset_group.resource_name

                    # look if the product is included or excluded
                    filter_status = get_product_info_main(client, customer_id, asset_group_id, filter_resource_name)
                    
                    product_id = row.asset_group_listing_group_filter.case_value.product_item_id.value

                    parent_listing_group_filter_resource_name = row.asset_group_listing_group_filter.parent_listing_group_filter

                    low_performing_campaign_id = 20520625833
                    
                    print(f"filter status is {filter_status}, for product id {product_id} and parent listing group filter {parent_listing_group_filter_resource_name}")

                    if filter_status == 'UNIT_INCLUDED':
                        # remove listing group filter, and create a new one with "unit_excluded"
                        print("excluding...")
                        excluded = exclude_listing_group_main(client, customer_id, filter_resource_name, asset_group_resource_name, product_id, parent_listing_group_filter_resource_name)

                        added_to_low_performing = False

                        if excluded:
                            # if the exclusion works, add product to the other campaign
                            print("including...")
                            added_to_low_performing = include_listing_group_main(client, customer_id, low_performing_campaign_id, product_id)

                        if excluded and added_to_low_performing:
                                email_body += (
                                    f"Campaign -- {row.campaign.name},"
                                    f" with asset group name {row.asset_group.name}, "
                                    f"has a product: {row.asset_group_listing_group_filter.case_value.product_item_id.value}, "
                                    f"that has spent ${real_cost} in the last 30 days, "
                                    f"with a conversion value of ${conversion_value}, "
                                    f"and ROAS of ${roas}. \n"
                                    f"This listing group has been excluded and added to the low-performing campaign. \n"
                                    f"\n")
                                print(f"Excluded listing group: ", row.asset_group_listing_group_filter.case_value.product_item_id.value + " in the following campaign: ", row.campaign.name) 
                                print(f"Sucess! includes listing group: ", row.asset_group_listing_group_filter.case_value.product_item_id.value + " in the low-performing pmax campaign.") 
                        elif not excluded:
                            email_body += (
                                    f"Campaign -- {row.campaign.name},"
                                    f" with asset group name {row.asset_group.name}, "
                                    f"has a product: {row.asset_group_listing_group_filter.case_value.product_item_id.value}, "
                                    f"that has spent ${real_cost} in the last 30 days, "
                                    f"with a conversion value of ${conversion_value}, "
                                    f"and ROAS of ${roas}. \n"
                                    f"This listing group NOT been sucessfully excluded. \n"
                                    f"\n")
                        
                        elif excluded and not added_to_low_performing:
                            email_body += (
                                    f"Campaign -- {row.campaign.name},"
                                    f" with asset group name {row.asset_group.name}, "
                                    f"has a product: {row.asset_group_listing_group_filter.case_value.product_item_id.value}, "
                                    f"that has spent ${real_cost} in the last 30 days, "
                                    f"with a conversion value of ${conversion_value}, "
                                    f"and ROAS of ${roas}. \n"
                                    f"This listing group has been excluded, but NOT been added to the low-performing campaign. \n"
                                    f"\n")
                        
        # Send email once the loop is finished
        if email_body:  # only send if email_body is not empty
            send_email(None, "Listing groups with ROAS < $7 found in PMax: Shopping ads (United States)", email_body)
        else:
            print(f"no listing groups found that meet the criteria :)")

    except GoogleAdsException as ex:
        print(f"An error occurred: {ex}")