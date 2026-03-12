import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from github import Github
import requests
from datetime import datetime
from textblob import TextBlob
from collections import defaultdict
import yfinance as yf
from youtube_transcript_api import YouTubeTranscriptApi

# Environment variables
EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_TO = os.getenv("EMAIL_TO")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
GH_TOKEN = os.getenv("GH_TOKEN")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")  # For X API

REPO_NAME = "BJHumphries/social-arb-email"

# --- Email ---
def send_email(subject: str, body: str):
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

# --- GitHub ---
def get_latest_commit_message(repo_name: str) -> str:
    try:
        g = Github(GH_TOKEN)
        repo = g.get_repo(repo_name)
        commit = repo.get_commits()[0]
        return commit.commit.message
    except Exception as e:
        print(f"Failed to fetch commit: {e}")
        return "N/A"

# --- StockTwits ---
def get_stocktwits_trending_symbols(limit=10):
    try:
        resp = requests.get("https://api.stocktwits.com/api/2/trending/symbols.json", timeout=10)
        data = resp.json()
        return [item.get("symbol") for item in data.get("symbols", [])[:limit]]
    except Exception as e:
        print(f"StockTwits fetch failed: {e}")
        return []

# --- Reddit ---
def get_reddit_sentiment(symbol):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        url = f"https://www.reddit.com/r/stocks/search.json?q={symbol}&sort=new&limit=10"
        resp = requests.get(url, headers=headers, timeout=10)
        posts = resp.json().get("data", {}).get("children", [])
        score = 0
        for post in posts:
            text = post['data'].get('title', '') + " " + post['data'].get('selftext', '')
            score += TextBlob(text).sentiment.polarity
        return score / max(1, len(posts))
    except Exception as e:
        print(f"Reddit error for {symbol}: {e}")
        return 0

# --- Twitter/X ---
def get_twitter_sentiment(symbol):
    try:
        headers = {"Authorization": f"Bearer {TWITTER_BEARER_TOKEN}"}
        url = f"https://api.twitter.com/2/tweets/search/recent?query={symbol}&max_results=10&tweet.fields=text"
        resp = requests.get(url, headers=headers, timeout=10).json()
        tweets = resp.get("data", [])
        score = 0
        for tweet in tweets:
            score += TextBlob(tweet.get("text", "")).sentiment.polarity
        return score / max(1, len(tweets))
    except Exception as e:
        print(f"Twitter error for {symbol}: {e}")
        return 0

# --- YouTube ---
def get_youtube_sentiment(symbol):
    try:
        url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={symbol}&type=video&key={YOUTUBE_API_KEY}&maxResults=5"
        resp = requests.get(url, timeout=10).json()
        score = 0
        count = 0
        for item in resp.get("items", []):
            video_id = item['id']['videoId']
            try:
                transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
                text = " ".join([t['text'] for t in transcript_list])
                score += TextBlob(text).sentiment.polarity
                count += 1
            except:
                continue
        return score / max(1, count)
    except Exception as e:
        print(f"YouTube error for {symbol}: {e}")
        return 0

# --- Trade Aggregator ---
def generate_trade_ideas():
    symbols = get_stocktwits_trending_symbols(limit=10)
    ideas = []

    for symbol in symbols:
        reddit_score = get_reddit_sentiment(symbol)
        twitter_score = get_twitter_sentiment(symbol)
        youtube_score = get_youtube_sentiment(symbol)

        # Optional: include price/volume momentum from yfinance
        price_score = 0
        try:
            data = yf.Ticker(symbol).history(period="5d")
            if len(data) >= 2:
                price_change = (data['Close'][-1] - data['Close'][-2]) / data['Close'][-2]
                price_score = price_change * 5  # scale
        except:
            pass

        total_score = reddit_score + twitter_score + youtube_score + price_score

        if total_score > 0.1:
            action = "Buy"
        elif total_score < -0.1:
            action = "Sell"
        else:
            action = "Hold"

        ideas.append({
            "symbol": symbol,
            "action": action,
            "score": round(total_score,2),
            "reddit": round(reddit_score,2),
            "twitter": round(twitter_score,2),
            "youtube": round(youtube_score,2),
            "price": round(price_score,2)
        })
    return ideas

def format_email_body(ideas, latest_commit):
    body = f"Daily Trade Ideas ({datetime.now().strftime('%Y-%m-%d %H:%M')}):\n\n"
    for idea in ideas:
        body += (f"{idea['action']} {idea['symbol']} | "
                 f"Score: {idea['score']} "
                 f"(Reddit: {idea['reddit']}, Twitter: {idea['twitter']}, "
                 f"YouTube: {idea['youtube']}, Price: {idea['price']})\n")
    body += f"\nLatest GitHub commit:\n{latest_commit}\n"
    return body

def main():
    ideas = generate_trade_ideas()
    latest_commit = get_latest_commit_message(REPO_NAME)
    body = format_email_body(ideas, latest_commit)
    send_email("Daily Trade Ideas (Multi-Signal)", body)

if __name__ == "__main__":
    main()
