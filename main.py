import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from textblob import TextBlob
import requests
import praw
import tweepy
from youtube_transcript_api import YouTubeTranscriptApi

# Environment variables
EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_TO = os.getenv("EMAIL_TO")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

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

# ------------------- Social Signal Functions -------------------

def fetch_reddit_signals(subreddit_name="stocks", limit=5):
    reddit = praw.Reddit(client_id=REDDIT_CLIENT_ID,
                         client_secret=REDDIT_CLIENT_SECRET,
                         user_agent=REDDIT_USER_AGENT)
    signals = []
    for submission in reddit.subreddit(subreddit_name).hot(limit=limit):
        text = f"{submission.title}\n{submission.selftext}"
        sentiment = TextBlob(text).sentiment.polarity
        signals.append({"source": "Reddit", "title": submission.title, "sentiment": sentiment})
    return signals

def fetch_twitter_signals(query="#stocks OR #investing", max_results=5):
    client = tweepy.Client(bearer_token=TWITTER_BEARER_TOKEN)
    tweets = client.search_recent_tweets(query=query, max_results=max_results)
    signals = []
    if tweets.data:
        for tweet in tweets.data:
            text = tweet.text
            sentiment = TextBlob(text).sentiment.polarity
            signals.append({"source": "Twitter", "text": text, "sentiment": sentiment})
    return signals

def fetch_youtube_transcript(video_id):
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        full_text = " ".join([t['text'] for t in transcript_list])
        sentiment = TextBlob(full_text).sentiment.polarity
        return {"video_id": video_id, "text": full_text, "sentiment": sentiment}
    except Exception as e:
        print(f"Failed to fetch transcript for {video_id}: {e}")
        return None

# ------------------- Main Workflow -------------------

def main():
    email_subject = "Daily Trade Ideas - Social Signals"
    body = "Here are the top signals and trade ideas:\n\n"

    # Reddit signals
    reddit_signals = fetch_reddit_signals()
    body += "Reddit Signals:\n"
    for s in reddit_signals:
        body += f"- {s['title']} (Sentiment: {s['sentiment']:.2f})\n"

    # Twitter signals
    twitter_signals = fetch_twitter_signals()
    body += "\nTwitter Signals:\n"
    for s in twitter_signals:
        body += f"- {s['text']} (Sentiment: {s['sentiment']:.2f})\n"

    # Example YouTube video IDs (replace with dynamic discovery if desired)
    youtube_ids = ["dQw4w9WgXcQ"]  # Replace with actual stock-related videos
    body += "\nYouTube Transcripts:\n"
    for vid in youtube_ids:
        transcript = fetch_youtube_transcript(vid)
        if transcript:
            body += f"- Video {vid} Sentiment: {transcript['sentiment']:.2f}\n"

    send_email(email_subject, body)

if __name__ == "__main__":
    main()
