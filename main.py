import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from github import Github

# Environment variables
EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_TO = os.getenv("EMAIL_TO")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
GH_TOKEN = os.getenv("GH_TOKEN")

def send_email(subject: str, body: str):
    """Send an email via SMTP."""
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_FROM
        msg['To'] = EMAIL_TO
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            server.send_message(msg)

        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

def get_latest_commit_message(repo_name: str):
    """Get the latest commit message from the given GitHub repo."""
    try:
        g = Github(GH_TOKEN)
        repo = g.get_repo(repo_name)
        commit = repo.get_commits()[0]
        return commit.commit.message
    except Exception as e:
        print(f"Failed to fetch commit: {e}")
        return None

def main():
    repo_name = "BJHumphries/social-arb-email"
    latest_commit = get_latest_commit_message(repo_name)
    if latest_commit:
        subject = f"Latest Commit in {repo_name}"
        body = f"The latest commit message is:\n\n{latest_commit}"
        send_email(subject, body)
    else:
        print("Could not retrieve the latest commit.")

if __name__ == "__main__":
    main()
