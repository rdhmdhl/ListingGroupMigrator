from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from fetch_listing_group_status import get_listing_group_status as get_listing_group_status
from exclude_listing_group import exclude_listing_group as exclude_listing_group_main
from include_listing_group import include_listing_group as include_listing_group_main
import datetime
from email_sender import send_email

def fetch_existing_listing_groups(client, customer_id, to_emails):
    try:
        ga_service = client.get_service("GoogleAdsService")

        # Calculate the last 30 days
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=30)
        print("first query for fetch_existing_listing_groups")
        low_performing_generic_asset_group_resource_name = 'customers/9084369246/assetGroups/6475967165'
        main_pmax_generic_asset_group_resource_name = 'customers/9084369246/assetGroups/6475496996'
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
        AND asset_group.status = 'ENABLED'
        AND metrics.cost_micros > 2000000000
        AND segments.date BETWEEN '{start_date}' AND '{end_date}'
        AND asset_group.resource_name NOT IN ('{low_performing_generic_asset_group_resource_name}') 
        AND asset_group.resource_name NOT IN ('{main_pmax_generic_asset_group_resource_name}')
        AND asset_group_listing_group_filter.case_value.product_item_id.value IS NOT NULL
        """
        # Execute the query
        response = ga_service.search(customer_id=customer_id, query=query)
        # initialize email body variable
        email_body = ""
        print(f"response: {response}")
        # Process the response
        for row in response:
            # Convert cost from micros to dollars and round to 2 decimal places
            real_cost = round(row.metrics.cost_micros / 1_000_000, 2)
            # Convert conversion value to dollars and round to 2 decimal places
            conversion_value = round(row.metrics.conversions_value, 2)
            # Calculate and round ROAS to 2 decimal places
            roas = round(row.metrics.conversions_value / real_cost, 2)
            product_id = row.asset_group_listing_group_filter.case_value.product_item_id.value
            # low performing campaign ID
            low_performing_campaign_id = 20520625833
            normal_pmax_campaign_id = 20510025794
            # filter status for the product within the low-performing pmax campaign, PASSING GENERIC ASSET GROUP TO FILTER NOT IN
            low_perf_camp_product_status = get_listing_group_status(client, customer_id, low_performing_campaign_id, product_id, low_performing_generic_asset_group_resource_name)
            # filter status for the product within the low-performing pmax campaign, PASSING GENERIC ASSET GROUP TO FILTER NOT IN
            normal_camp_product_status = get_listing_group_status(client, customer_id, normal_pmax_campaign_id, product_id, main_pmax_generic_asset_group_resource_name)
            print(f"product {product_id} has a roas of ${roas}")
            
            asset_group_listing_group_resource_name = row.asset_group_listing_group_filter.resource_name

            asset_group_name = row.asset_group.name

            if roas < 7:
                print(f"filter status is {normal_camp_product_status} for product id {product_id} within the main pmax campaign, and ROAS is ${roas}\n")
                # if included within the main pmax campaign, move forward to exclude
                if normal_camp_product_status == 'UNIT_INCLUDED':
                    # remove listing group filter, and create a new one with "unit_excluded" due to roas below goal
                    print("excluding in the main pmax campaign...")
                    excluded = exclude_listing_group_main(client, customer_id, normal_pmax_campaign_id, product_id, main_pmax_generic_asset_group_resource_name,asset_group_listing_group_resource_name)
                    added_to_low_performing = False

                    # if successfully excluded, and the listing group status for low-performing pmax campaign is excluded, move forward
                    if excluded and low_perf_camp_product_status == 'UNIT_EXCLUDED':
                        # if the exclusion works, add product to the other campaign, due to roas goals not being met
                        print("including in the low-performing pmax campaign...")
                        added_to_low_performing = include_listing_group_main(client, customer_id, low_performing_campaign_id, product_id, low_performing_generic_asset_group_resource_name, asset_group_name)
                
                        if added_to_low_performing:
                                email_body += (
                                    f"Campaign -- {row.campaign.name},"
                                    f" with asset group name {row.asset_group.name}, "
                                    f"has a product: {row.asset_group_listing_group_filter.case_value.product_item_id.value}, "
                                    f"that has spent ${real_cost} in the last 30 days, "
                                    f"with a conversion value of ${conversion_value}, "
                                    f"and ROAS of ${roas}. \n"
                                    f"Listing group {product_id} was excluded within the main pmax campaign, and included successfully in the low-performing pmax campaign -- which was previously not included.\n"
                                    f"\n")
                                print(f"sucess! excluded under-performing listing group in the main pmax campaign, and included product id: ", product_id + " in the low-performing pmax campaign: ", {normal_pmax_campaign_id})   
                                print("\n")
                                print("\n")
                    if excluded and low_perf_camp_product_status == 'UNIT_INCLUDED':
                        print("listing group already included within the low-performing campaign...")
                        email_body += (
                            f"Campaign -- {row.campaign.name},"
                            f" with asset group name {row.asset_group.name}, "
                            f"has a product: {row.asset_group_listing_group_filter.case_value.product_item_id.value}, "
                            f"that has spent ${real_cost} in the last 30 days, "
                            f"with a conversion value of ${conversion_value}, "
                            f"and ROAS of ${roas}. \n"
                            f"Listing group {product_id} was excluded within the main pmax campaign, but was already included in the low-performing pmax campaign.\n"
                            f"\n")

                elif normal_camp_product_status == 'UNIT_EXCLUDED' and low_perf_camp_product_status == 'UNIT_EXCLUDED':
                    print("listing group found excluded within the normal pmax campaign...")
                    # remove listing group filter, and create a new one with "unit_excluded" due to roas below goal
                    print("including in the low performing pmax campaign...")
                    included = include_listing_group_main(client, customer_id, low_performing_campaign_id, product_id, low_performing_generic_asset_group_resource_name, asset_group_name)
                    if included:
                        email_body += (
                                f"Campaign -- {row.campaign.name},"
                                f" with asset group name {row.asset_group.name}, "
                                f"has a product: {row.asset_group_listing_group_filter.case_value.product_item_id.value}, "
                                f"that has spent ${real_cost} in the last 30 days, "
                                f"with a conversion value of ${conversion_value}, "
                                f"and ROAS of ${roas}. \n"
                                f"This listing group was already excluded within this campaign, "
                                f"but successfully included within the low-performing campaign. \n"
                                f"\n"
                                )
                    else:
                        print("inclusion failed!")
                        email_body += (
                            f"Campaign -- {row.campaign.name},"
                            f" with asset group name {row.asset_group.name}, "
                            f"has a product: {row.asset_group_listing_group_filter.case_value.product_item_id.value}, "
                            f"that has spent ${real_cost} in the last 30 days, "
                            f"with a conversion value of ${conversion_value}, "
                            f"and ROAS of ${roas}. \n"
                            f"This listing group was already excluded within this campaign, "
                            f"{row.asset_group_listing_group_filter.case_value.product_item_id.value} was NOT successfully included within the "
                            f"low performing campaign, "
                            f"under asset group name {row.asset_group.name}.\n"
                            "\n"
                            )
                # no actions taken
                elif normal_camp_product_status == 'UNIT_EXCLUDED' and low_perf_camp_product_status == 'UNIT_INCLUDED':
                    print("listing group already included within the low-performing pmax campaign, and excluded within the main pmax campaign. no further actions taken.")
                    
                # handling for status not found
                elif low_perf_camp_product_status not in ('UNIT_EXCLUDED', 'UNIT_INCLUDED'):
                    email_body += (
                        f"This listing group status was not found within the low performing pmax campaign, "
                        f" which likely means it needs to be created. \n"
                        f"\n"
                        )

                # handling for status not found
                elif normal_camp_product_status not in ('UNIT_EXCLUDED', 'UNIT_INCLUDED'):
                    email_body += (
                            f"Campaign -- {row.campaign.name},"
                            f" with asset group name {row.asset_group.name}, "
                            f"has a product: {row.asset_group_listing_group_filter.case_value.product_item_id.value}, "
                            f"that has spent ${real_cost} in the last 30 days, "
                            f"with a conversion value of ${conversion_value}, "
                            f"and ROAS of ${roas}. \n"
                            f"This listing group status was not found within the main pmax campaign. This likely means it does not exist yet. No actions taken. \n"
                            f"\n")
            # do nothing if roas is meeting the goal
            elif roas >= 7:
                print(f"product {product_id} found, but roas is >= $7. no actions taken.")
                        
        # Send email once the loop is finished
        if email_body:  # only send if email_body is not empty
            send_email(file_name=None, email_subject="Sony | Listing group Update in PMax: Shopping ads (United States)",email_body=email_body, is_html=False, to_emails=to_emails)
        else:
            print(f"no listing groups found that meet the criteria :)")

    except GoogleAdsException as ex:
        print(f"An error occurred: {ex}")