import smtplib
import traceback
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os
from dotenv import load_dotenv
# load env variables
load_dotenv()

def send_email(file_name=None, email_subject="", email_body=""):
    from_email = os.getenv("EMAIL_ADDRESS")
    to_emails = os.getenv("TO_EMAIL_ADDRESSES").split(",")  # Split comma-separated string into list
    email_password = os.getenv("EMAIL_PASSWORD")
    subject = email_subject

    try:
        # Create a multipart message
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = ", ".join(to_emails)  # This should be a string
        msg['Subject'] = subject

        # Add body to email
        body = email_body
        msg.attach(MIMEText(body, 'plain'))
        
        if file_name:
            # Attach the file
            with open(file_name, 'rb') as file:
                attach_file = MIMEApplication(file.read(), Name=file_name)
            attach_file['Content-Disposition'] = f'attachment; filename={file_name}'
            msg.attach(attach_file)

        # Connect to Gmail's SMTP server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        
        # Login
        server.login(from_email, email_password)

        # Send email
        server.sendmail(from_email, to_emails, msg.as_string())
        
        # Disconnect
        server.quit()

    except Exception as e:
        error_message = f"An error occurred while sending the email: {str(e)}\n"

        # get current traceback information to use in the logger file
        tb_info = traceback.extract_tb(sys.exc_info()[2])
        filename = tb_info[-1].filename  # get the name of the file where the error occurred

        print(error_message)

# Example use
# send_email('enabled_campaigns.txt')