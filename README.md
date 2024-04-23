# ListingGroupMigrator
Automate the movement of products/listing groups between campaigns based on performance goals using the Google Ads API. This tool is designed to save time and reduce errors in managing large-scale ad campaigns.

## Why?
Sony needed a solution to move products/listing groups between campaigns based on performance goals (return on ad spend). Doing this manually across thousands of products is tedious, time consuming and error prone. Using the [Google Ads API](https://github.com/googleads/google-ads-python) I was able to automate this, and save many hours spent on this mundane task.

## Prerequisites
- Python 3.8+
- Access to Google Ads account
- Gmail account for sending notifications (optional)

## Usage
Use the email_sender file to send an email on what the program does! This is configured for a gmail address, using the gmail SMTP server. 

Customize the query to pull in different metrics, in order to include/exclude or move listings between PMax campaigns. 

In order to include or exclude a product, the listing group filter must be removed and created again. Ensure that it's being created with the correct parameters. 

The include file relies on asset group strings to be the same. Ideally we wouldn't have to rely on this because the could potentially be adjusted in the Google Ads platform. In the future we will pull asset group IDs dynamically and match them across both campaigns. 

## How to Use
1. [Obtain a developer token](https://developers.google.com/google-ads/shopping/full-automation/articles/t11#obtain_a_developer_token)
2. [Choose a client library](https://developers.google.com/google-ads/shopping/full-automation/articles/t11#choose_a_client_library)
3. [Set up OAuth2](https://developers.google.com/google-ads/shopping/full-automation/articles/t11#set_up_oauth2)
4. [Get a refresh token](https://developers.google.com/google-ads/shopping/full-automation/articles/t11#get_a_refresh_token)
5. Update CID in the lambda_fetch_listing_group file
6. Add email address/[password](https://support.google.com/mail/answer/185833?hl=en) for sending emails using the gmail SMTP server
7. Try it out! Make sure to use a test campaign at first. All changes will be noted in the change history

## Security Note
Ensure that your credentials are stored securely. Avoid hardcoding sensitive information directly into your scripts. Use environment variables or secure credential storage services.

## Contributing
Feel free to fork this project and submit pull requests. For major changes, please open an issue first to discuss what you would like to change.

## Support
If you have any questions or encounter issues, please open an issue or contact reid.hommedahl@gmail.com
