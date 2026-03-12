import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from textblob import TextBlob
import yfinance as yf
from youtube_transcript_api import YouTubeTranscriptApi
import praw
import requests

# Environment variables
EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_TO = os.getenv("EMAIL_TO")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")

def fetch_reddit_stock_mentions(subreddit="stocks", limit=10):
    reddit = praw.Reddit(client_id=REDDIT_CLIENT_ID,
                         client_secret=REDDIT_CLIENT_SECRET,
                         user_agent=REDDIT_USER_AGENT)
    posts = reddit.subreddit(subreddit).hot(limit=limit)
    mentions = []
    for post in posts:
        if '$' in post.title:
            mentions.append(post.title)
    return mentions

def fetch_youtube_transcripts(keywords, max_results=3):
    transcripts = []
    for keyword in keywords:
        # Placeholder: search videos via YouTube API or use saved video IDs
        # Example with YouTube Data API omitted for brevity
        video_id = "dQw4w9WgXcQ"  # Replace with real search result
        try:
            t = YouTubeTranscriptApi.get_transcript(video_id)
            text = " ".join([x['text'] for x in t])
            transcripts.append(f"{keyword}:\n{text[:500]}...")  # Limit snippet
        except Exception as e:
            transcripts.append(f"{keyword}: Transcript not available")
    return transcripts

def analyze_sentiment(texts):
    analyzed = []
    for t in texts:
        blob = TextBlob(t)
        analyzed.append((t, blob.sentiment.polarity))
    return analyzed

def fetch_stock_data(tickers):
    data = {}
    for t in tickers:
        try:
            stock = yf.Ticker(t.replace('$',''))
            info = stock.info
            data[t] = f"Price: {info.get('currentPrice', 'N/A')}, Change: {info.get('regularMarketChangePercent', 'N/A')}%"
        except Exception as e:
            data[t] = "Data unavailable"
    return data

def send_email(subject, body):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_FROM
    msg['To'] = EMAIL_TO
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.send_message(msg)

    print("Email sent!")

def main():
    # 1. Fetch Reddit stock mentions
    mentions = fetch_reddit_stock_mentions(limit=10)

    # 2. Analyze sentiment
    sentiment = analyze_sentiment(mentions)

    # 3. Get stock tickers from mentions
    tickers = [m.split()[0] for m, _ in sentiment if m.startswith('$')]

    # 4. Fetch stock data
    stock_info = fetch_stock_data(tickers)

    # 5. Fetch YouTube transcripts for tickers
    transcripts = fetch_youtube_transcripts(tickers)

    # 6. Build email content
    email_body = "Daily Trade Ideas\n\n"
    email_body += "Reddit Mentions & Sentiment:\n"
    for m, s in sentiment:
        email_body += f"{m} - Sentiment: {s:.2f}\n"
    email_body += "\nStock Info:\n"
    for t, info in stock_info.items():
        email_body += f"{t}: {info}\n"
    email_body += "\nYouTube Transcripts Snippets:\n"
    for t in transcripts:
        email_body += f"{t}\n\n"

    # 7. Send email
    send_email("Daily Trade Ideas", email_body)

if __name__ == "__main__":
    main()
