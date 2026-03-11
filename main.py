import praw
import requests
from github import Github
from googleapiclient.discovery import build
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# -------- CONFIG --------
REDDIT_CLIENT_ID = "YOUR_REDDIT_CLIENT_ID"
REDDIT_CLIENT_SECRET = "YOUR_REDDIT_SECRET"
REDDIT_USER_AGENT = "asym_trader"
GITHUB_TOKEN = "YOUR_GITHUB_TOKEN"
EMAIL_FROM = "your_email@gmail.com"
EMAIL_TO = "recipient_email@example.com"
EMAIL_PASSWORD = "YOUR_EMAIL_PASSWORD"  # or App Password
TOP_N = 20

# -------- FETCH SIGNALS --------
def fetch_reddit_signals():
    reddit = praw.Reddit(client_id=REDDIT_CLIENT_ID,
                         client_secret=REDDIT_CLIENT_SECRET,
                         user_agent=REDDIT_USER_AGENT)
    tickers = ["RKLB","ASTS","NVIDIA","IONQ","BLACKSKY"]  # Example
    signals = {t: {"reddit":0} for t in tickers}
    subreddits = ['stocks','wallstreetbets','SpaceX','AI']
    for sub in subreddits:
        for post in reddit.subreddit(sub).hot(limit=100):
            for t in tickers:
                if t in post.title.upper() or t in post.selftext.upper():
                    signals[t]["reddit"] += 1
    return signals

def fetch_github_signals():
    g = Github(GITHUB_TOKEN)
    tickers = ["NVIDIA","IONQ"]  # Example AI/Quantum
    signals = {t: {"github":0} for t in tickers}
    for t in tickers:
        repos = g.search_repositories(query=f"{t} topic:ai")
        signals[t]["github"] = repos.totalCount
    return signals

# TikTok, YouTube, VC APIs would be added similarly

# -------- SCORE TICKERS --------
def calculate_score(signals):
    weights = {"reddit":0.25, "github":0.15, "tiktok":0.2, "youtube":0.15, "vc":0.25}
    scored = {}
    for t, sig in signals.items():
        score = 0
        for k, w in weights.items():
            score += sig.get(k,0)*w
        scored[t] = {"score":round(score,2), "drivers":[k for k in sig if sig[k]>0]}
    return scored

# -------- SEND EMAIL --------
def send_email(top_tickers):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Daily Pre-Market Asymmetric Trade Watchlist"
    msg['From'] = EMAIL_FROM
    msg['To'] = EMAIL_TO

    html = "<h2>Top Asymmetric Trade Candidates</h2><table border='1'><tr><th>Rank</th><th>Ticker</th><th>Score</th><th>Signals</th></tr>"
    for i, (t, data) in enumerate(top_tickers.items(), start=1):
        html += f"<tr><td>{i}</td><td>{t}</td><td>{data['score']}</td><td>{', '.join(data['drivers'])}</td></tr>"
    html += "</table>"
    msg.attach(MIMEText(html, 'html'))

    with smtplib.SMTP_SSL('smtp.gmail.com',465) as server:
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())

# -------- MAIN --------
def main(event=None, context=None):  # Required for Cloud Functions
    reddit_signals = fetch_reddit_signals()
    github_signals = fetch_github_signals()

    # Merge signals
    all_signals = {}
    for t in reddit_signals:
        all_signals[t] = {**reddit_signals[t], **github_signals.get(t, {})}

    scored = calculate_score(all_signals)
    top_tickers = dict(sorted(scored.items(), key=lambda x:x[1]['score'], reverse=True)[:TOP_N])
    send_email(top_tickers)
    return "Email sent successfully!"