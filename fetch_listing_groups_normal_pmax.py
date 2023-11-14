from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from fetch_product_info import get_product_info as get_product_info_main
from exclude_listing_group import exclude_listing_group as exclude_listing_group_main
import datetime
from email_sender import send_email

def fetch_existing_listing_groups(client, customer_id):
    try:
        ga_service = client.get_service("GoogleAdsService")

        # Calculate the last 30 days
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=30)

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
        WHERE campaign.name LIKE '%PMax:%'
        AND campaign.id = {20510025794}
        AND metrics.cost_micros > 2000000000
        AND segments.date BETWEEN '{start_date}' AND '{end_date}'
        AND asset_group_listing_group_filter.case_value.product_item_id.value IS NOT NULL
        """
        
        # Execute the query
        response = ga_service.search(customer_id=customer_id, query=query)
        # initialize email body variable
        email_body = ""

        # Process the response
        for row in response:
            # Convert cost from micros to dollars and round to 2 decimal places
            real_cost = round(row.metrics.cost_micros / 1_000_000, 2)

            # Convert conversion value to dollars and round to 2 decimal places
            conversion_value = round(row.metrics.conversions_value, 2)

            # Calculate and round ROAS to 2 decimal places
            roas = round(row.metrics.conversions_value / real_cost, 2)


            if real_cost != 0:
                if roas < 7:
                    # Get product information for this listing group
                    asset_group_id = row.asset_group.id
                    # filter resource name
                    filter_resource_name = row.asset_group_listing_group_filter.resource_name
                    # asset group resource name
                    asset_group_resource_name = row.asset_group.resource_name

                    filter_status = get_product_info_main(client, customer_id, asset_group_id, filter_resource_name)

                    product_id = row.asset_group_listing_group_filter.case_value.product_item_id.value

                    parent_listing_group_filter_resource_name = row.asset_group_listing_group_filter.parent_listing_group_filter

                    if filter_status == 'UNIT_INCLUDED':
                        print(f"calling exclude listing groups now...")
                        # remove listing group filter, and create a new one with "unit_excluded"
                        success = exclude_listing_group_main(client, customer_id, filter_resource_name, asset_group_resource_name, product_id, parent_listing_group_filter_resource_name)

                        if success:
                            email_body += (
                                f"Campaign -- {row.campaign.name},"
                                f" with asset group name {row.asset_group.name}, "
                                f"has a product: {row.asset_group_listing_group_filter.case_value.product_item_id.value}, "
                                f"that has spent ${real_cost} in the last 30 days, "
                                f"with a conversion value of ${conversion_value}, "
                                f"and ROAS of ${roas}. \n"
                                f"This listing group has been excluded! \n"
                                f"\n")
                            print(f"sucess! excluded listing group: ", row.asset_group_listing_group_filter.case_value.product_item_id.value)
                        
        # Send email once the loop is finished
        if email_body:  # only send if email_body is not empty
            send_email(None, "Listing groups with ROAS < $7 found in PMax: Shopping ads (United States)", email_body)
        else:
            print(f"no listing groups found that meet the criteria :)")

    except GoogleAdsException as ex:
        print(f"An error occurred: {ex}")