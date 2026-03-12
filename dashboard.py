import os
from textblob import TextBlob
import praw
import tweepy
from youtube_transcript_api import YouTubeTranscriptApi
import streamlit as st

# ------------------- Environment Variables -------------------
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

# ------------------- Functions -------------------

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
        return {"video_id": video_id, "text": "", "sentiment": 0.0, "error": str(e)}

# ------------------- Streamlit Dashboard -------------------

st.title("📊 Social Signals & Trade Ideas Dashboard")

st.header("Reddit Signals")
reddit_signals = fetch_reddit_signals()
for s in reddit_signals:
    st.write(f"**{s['title']}**")
    st.write(f"Sentiment: {s['sentiment']:.2f}")
    st.write("---")

st.header("Twitter Signals")
twitter_signals = fetch_twitter_signals()
for s in twitter_signals:
    st.write(f"**{s['text']}**")
    st.write(f"Sentiment: {s['sentiment']:.2f}")
    st.write("---")

st.header("YouTube Transcripts")
# Example IDs - you can replace with dynamic trending videos
youtube_ids = ["dQw4w9WgXcQ"]
for vid in youtube_ids:
    transcript = fetch_youtube_transcript(vid)
    if transcript.get("error"):
        st.write(f"Failed to fetch {vid}: {transcript['error']}")
    else:
        st.write(f"Video ID: {vid}")
        st.write(f"Sentiment: {transcript['sentiment']:.2f}")
        st.write(transcript['text'][:500] + "…")  # preview first 500 chars
    st.write("---")
