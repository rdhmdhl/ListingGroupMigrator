from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from email_sender import send_email

def main(client, customer_id):

    ga_service = client.get_service("GoogleAdsService")

    query = """
        SELECT
          campaign.id,
          campaign.name,
          ad_group_criterion.criterion_id,
          ad_group_criterion.listing_group.type
        FROM ad_group_criterion
        WHERE 
            ad_group_criterion.status = 'ENABLED'
            AND campaign.name LIKE '%PMax:%'
        ORDER BY campaign.id"""
    
    # Issues a search request using streaming.
    stream = ga_service.search_stream(customer_id=customer_id, query=query)

    # Issues a search request using streaming.
    with open('enabled_campaigns_and_listing_groups.txt', 'w') as file:
        for batch in stream:
            for row in batch.results:
                file.write(
                    f"Campaign with ID {row.campaign.id.value} and name "
                    f'"{row.campaign.name.value}" was found.\n'
                )
                
                if 'listing_group' in row.ad_group_criterion:
                    file.write(
                        f"Listing Group with ID {row.ad_group_criterion.criterion_id.value}, "
                        f"type {row.ad_group_criterion.listing_group.type}.\n"
                    )

    send_email('enabled_campaigns_and_listing_groups.txt', "testing for sony", "campaigns")