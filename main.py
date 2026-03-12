import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from github import Github
import requests
from datetime import datetime

# Environment variables
EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_TO = os.getenv("EMAIL_TO")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
GH_TOKEN = os.getenv("GH_TOKEN")

# Example social signal sources (Twitter, Reddit, etc. would need API keys)
SOCIAL_FEEDS = [
    "https://api.mock-social-feed.com/stock-signals"  # replace with real API
]

# Example stock universe
STOCKS = ["AAPL", "TSLA", "GOOGL", "AMZN", "MSFT"]

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

def get_social_signal_score(symbol: str) -> float:
    """Mock function to get a social signal score for a stock."""
    # Replace with actual API calls (Twitter sentiment, Reddit mentions, etc.)
    try:
        # response = requests.get(f"https://api.socialsignals.com/{symbol}")
        # data = response.json()
        # return data['sentiment_score']
        import random
        return round(random.uniform(-1, 1), 2)  # -1 = strong sell, 1 = strong buy
    except Exception as e:
        print(f"Failed to fetch social signal for {symbol}: {e}")
        return 0

def generate_trade_ideas():
    """Generate trade ideas using social signals and other criteria."""
    ideas = []

    for stock in STOCKS:
        score = get_social_signal_score(stock)

        if score > 0.3:
            action = "Buy"
        elif score < -0.3:
            action = "Sell"
        else:
            action = "Hold"

        ideas.append({
            "symbol": stock,
            "action": action,
            "score": score
        })

    # Format email body
    body = f"Daily Trade Ideas ({datetime.now().strftime('%Y-%m-%d %H:%M')}):\n\n"
    for idea in ideas:
        body += f"{idea['action']} {idea['symbol']} (Score: {idea['score']})\n"
    return body

def main():
    body = generate_trade_ideas()
    subject = "Daily Trade Ideas (Social Signals)"
    send_email(subject, body)

if __name__ == "__main__":
    main()
