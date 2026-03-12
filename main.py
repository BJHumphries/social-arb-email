import os
import smtplib
from email.mime.text import MIMEText

print("SCRIPT STARTED")

EMAIL_FROM = os.environ.get("EMAIL_FROM")
EMAIL_TO = os.environ.get("EMAIL_TO")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")

print("Connecting to Gmail...")

msg = MIMEText("GitHub Actions email test")
msg["Subject"] = "Email Test"
msg["From"] = EMAIL_FROM
msg["To"] = EMAIL_TO

with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
    server.login(EMAIL_FROM, EMAIL_PASSWORD)
    server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())

print("EMAIL SENT SUCCESSFULLY")
