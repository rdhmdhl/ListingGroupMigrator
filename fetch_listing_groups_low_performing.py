from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from fetch_listing_group_status import get_listing_group_status as get_listing_group_status
from exclude_listing_group import exclude_listing_group as exclude_listing_group_main
from include_listing_group import include_listing_group as include_listing_group_main
import datetime
from email_sender import send_email
# use from email_module.email_sender import send_email in AWS, as it's in layer 3

def fetch_existing_listing_groups(client, customer_id, to_emails):
    try:
        ga_service = client.get_service("GoogleAdsService")

        # Calculate the last 30 days
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=30)
        low_performing_generic_asset_group_resource_name = 'customers/9084369246/assetGroups/6475967165'
        main_pmax_generic_asset_group_resource_name = 'customers/9084369246/assetGroups/6475496996'
        # Create the query
        query = f"""
        SELECT
            asset_group.id,
            asset_group.resource_name,
            asset_group.name,
            asset_group.status,
            asset_group_listing_group_filter.resource_name,
            asset_group_listing_group_filter.case_value.product_item_id.value,
            campaign.id,
            campaign.name,
            metrics.cost_micros,
            metrics.conversions_value
        FROM asset_group_product_group_view
        WHERE campaign.id = {20520625833}
        AND asset_group.status = 'ENABLED'
        AND metrics.cost_micros >= 1000000000
        AND segments.date BETWEEN '{start_date}' AND '{end_date}'
        AND asset_group.resource_name NOT IN ('{low_performing_generic_asset_group_resource_name}') 
        AND asset_group.resource_name NOT IN ('{main_pmax_generic_asset_group_resource_name}')
        AND asset_group_listing_group_filter.case_value.product_item_id.value IS NOT NULL
        """
        
        # Execute the query
        response = ga_service.search(customer_id=customer_id, query=query)
        # initialize email body variable
        email_body = ""
        print("response: ", response)
        # Process the response
        for row in response:
            # Convert cost from micros to dollars and round to 2 decimal places
            real_cost = round(row.metrics.cost_micros / 1_000_000, 2)
            # Convert conversion value to dollars and round to 2 decimal places
            conversion_value = round(row.metrics.conversions_value, 2)
            # Calculate and round ROAS to 2 decimal places
            roas = round(row.metrics.conversions_value / real_cost, 2)
            product_id = row.asset_group_listing_group_filter.case_value.product_item_id.value
            print(f"product found: {product_id} with ${roas} roas")
            # low performing campaign ID
            low_performing_campaign_id = 20520625833
            normal_pmax_campaign_id = 20510025794
            # filter status for the product within the low-performing pmax campaign, PASSING GENERIC ASSET GROUP TO FILTER NOT IN
            low_perf_camp_product_status = get_listing_group_status(client, customer_id, low_performing_campaign_id, product_id, low_performing_generic_asset_group_resource_name)
            # filter status for the product within the low-performing pmax campaign, PASSING GENERIC ASSET GROUP TO FILTER NOT IN
            normal_camp_product_status = get_listing_group_status(client, customer_id, normal_pmax_campaign_id, product_id, main_pmax_generic_asset_group_resource_name)

            if roas < 4:
                print(f"filter status is {low_perf_camp_product_status} for product id {product_id} within the low-performing pmax campaign, and ROAS is ${roas}\n")
                # check if the product is included in the low-performing campaign
                if low_perf_camp_product_status == 'UNIT_INCLUDED':
                    # remove listing group filter, and create a new one with "unit_excluded"
                    print(f"excluding {product_id} from low-performing pmax campaign becuase ROAS is ${roas}\n")
                    excluded = exclude_listing_group_main(client, customer_id, low_performing_campaign_id, product_id, low_performing_generic_asset_group_resource_name)
                    
                    if excluded:
                        email_body += (
                            f"Campaign -- {row.campaign.name},"
                            f" with asset group name {row.asset_group.name}, "
                            f"has a product: {product_id}, "
                            f"that has spent ${real_cost} in the last 30 days, "
                            f"with a conversion value of ${conversion_value}, "
                            f"and ROAS of ${roas}."
                            f"This listing group has been excluded! \n"
                            f"\n")
                        print(f"sucess! excluded listing group: {product_id} in the following campaign {row.campaign.name} and asset group {row.asset_group.name}")   
                        print('\n')
                elif low_perf_camp_product_status == 'UNIT_EXCLUDED': 
                    print("listing group was already excluded in the low-performing pmax campaign.")
                    email_body += (
                        f"Campaign -- {row.campaign.name},"
                        f" with asset group name {row.asset_group.name}, "
                        f"has a product: {product_id}, "
                        f"that has spent ${real_cost} in the last 30 days, "
                        f"with a conversion value of ${conversion_value}, "
                        f"and ROAS of ${roas}."
                        f"This listing group {product_id} was already excluded in the low-performing pmax campaign -- no actions taken.\n"
                        f"\n"
                        )
                    
                elif low_perf_camp_product_status not in ('UNIT_INCLUDED', 'UNIT_EXCLUDED'):
                    print("listing group status was not found in low-performing campaign.")
                    email_body += (
                        f"Campaign -- {row.campaign.name},"
                        f" with asset group name {row.asset_group.name}, "
                        f"has a product: {product_id}, "
                        f"that has spent ${real_cost} in the last 30 days, "
                        f"with a conversion value of ${conversion_value}, "
                        f"and ROAS of ${roas}."
                        f"listing group {product_id} status was not found in the low-performing pmax campaign -- no actions taken.\n"
                        f"\n"
                        )

            # if roas is greater than or equal to $4, include in main campaign, exclude in low performing
            if roas >= 7:
                # CHECK IF THE LISTING GROUP FILTER STATUS IS INCLUDED within the MAIN CAMPAIGN
                # if it's excluded, create a new filter with the status "included"
                if normal_camp_product_status == 'UNIT_EXCLUDED':
                    print(f"including {product_id} in main pmax campaign, because ROAS is ${roas} within the low-performing campaign. the product is currently excluded within the main pmax campaign. \n")
                    # include in main pmax campaign
                    added_to_normal_pmax = include_listing_group_main(client, customer_id, normal_pmax_campaign_id, product_id, main_pmax_generic_asset_group_resource_name)

                    # ensure product was added to normal pmax, and the product status
                    # within the low-performing campaign is 'unit included' before excluding
                    if added_to_normal_pmax: 
                        print(f"successfully included in main campaign.\n")
                        email_body += (
                            f"Campaign -- {row.campaign.name},"
                            f" with asset group name {row.asset_group.name}, "
                            f"has a product: {product_id}, "
                            f"that has spent ${real_cost} in the last 30 days, "
                            f"with a conversion value of ${conversion_value}, "
                            f"and ROAS of ${roas}. "
                            f"Listing group {product_id} was included successfully in the main pmax campaign -- which was previously not included."
                        )

                        # exclude the listing group within the low performing pmax campaign if included
                        if low_perf_camp_product_status == 'UNIT_INCLUDED':
                            exclusion_complete = exclude_listing_group_main(client, customer_id, low_performing_campaign_id, product_id, low_performing_generic_asset_group_resource_name)

                            if exclusion_complete:
                                email_body += (
                                        f"This over-performing listing group has been excluded within the low-performing pmax campaign. \n"
                                        f"\n")
                                print(f"sucess! excluded over-performing listing group in the low-performing pmax campaign, and included product id: ", product_id + " in the main pmax campaign: ", {normal_pmax_campaign_id})   
                                print("\n")
                                print("\n")
                        
                            else:
                                print("Listing group was not excluded successfully in the low-performing pmax campaign, but it was successfully added to the main pmax campaign. \n")
                                email_body += (f"listing group {product_id} in asset group {row.asset_group.name} was not excluded successfully in the low-performing pmax campaign, but it was successfully added to the main pmax campaign. \n")
                            
                        elif low_perf_camp_product_status == 'UNIT_EXCLUDED':
                            print(f"Product ID: {product_id} was already excluded in the low-performing pmax campaign.\n")
                            email_body += (
                                f"Listing group {product_id} was already excluded in the low-performing pmax campaign. \n"
                                f"\n"
                                )
                    else:
                        print("listing group was not successfully added to the main pmax campaign \n")
                        email_body += (f"Listing group {product_id} was not successfully added to the main pmax campaign. \n")
                
                elif normal_camp_product_status == 'UNIT_INCLUDED':
                    print("listing group was already included in the main pmax campaign. checking if it's already included within the low-performing campaign now...")
                    # exclude the low performing pmax campaign
                    if low_perf_camp_product_status == 'UNIT_INCLUDED':
                        print("listing group is currently included within the low-performing campaign, excluding now...")
                        exclusion_complete = exclude_listing_group_main(client, customer_id, low_performing_campaign_id, product_id, low_performing_generic_asset_group_resource_name)

                        if exclusion_complete:
                            print(f"exclusion completed within the low-performing campaign. \n")
                            email_body += (
                                f"Campaign -- {row.campaign.name},"
                                f" with asset group name {row.asset_group.name}, "
                                f"has a product: {product_id}, "
                                f"that has spent ${real_cost} in the last 30 days, "
                                f"with a conversion value of ${conversion_value}, "
                                f"and ROAS of ${roas}. "
                                f"Listing group {product_id} was already included in the main pmax campaign, and it was successfully excluded from the low-performing campaign due to ROAS overperforming, at ${roas}. \n"
                                f"\n"
                                )
                        else:
                            print(f"error! exclusion not completed within the low-performing campaign! \n")
                            email_body += (
                                f"Campaign -- {row.campaign.name},"
                                f" with asset group name {row.asset_group.name}, "
                                f"has a product: {product_id}, "
                                f"that has spent ${real_cost} in the last 30 days, "
                                f"with a conversion value of ${conversion_value}, "
                                f"and ROAS of ${roas}. "
                                f"Listing group {product_id} was already included in the main pmax campaign, but it was NOT successfully excluded from the low-performing campaign.\n"
                                f"\n"
                                )

                    elif low_perf_camp_product_status == 'UNIT_EXCLUDED': 
                        print("listing group was already excluded in the low-performing campaign")
                        email_body += (f"Listing group {product_id} was already excluded in the low-performing campaign (${roas} ROAS), and already included within the main pmax campaign. no actions taken.\n")

                elif normal_camp_product_status not in ('UNIT_EXCLUDED', 'UNIT_INCLUDED'):
                    print("listing group was not found within the main pmax campaign. it likely needs to be created.. no action taken.")
                    email_body += (
                                f"Campaign -- {row.campaign.name},"
                                f" with asset group name {row.asset_group.name}, "
                                f"has a product: {product_id}, "
                                f"that has spent ${real_cost} in the last 30 days, "
                                f"with a conversion value of ${conversion_value}, "
                                f"and ROAS of ${roas}. "
                                f"Listing group {product_id} was not found within the main pmax campaign. This likely means it does not exist yet. No actions taken. \n"
                                f"\n")

        # Send email once the loop is finished
        if email_body:  # only send if email_body is not empty
            send_email(file_name=None, email_subject="Sony | Listing Groups Updated in Low-Performing PMax Campaign", email_body=email_body, is_html=False, to_emails=to_emails)
            # print("pretending to send an email")
        else:
            print(f"no listing groups found that meet the criteria :) \n")

    except GoogleAdsException as ex:
        print(f"An error occurred: {ex}")