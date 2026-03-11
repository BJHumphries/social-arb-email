import os
import requests
from github import Github
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# -------- CONFIG --------
TOP_N = 20
TICKERS = ["RKLB","ASTS","NVIDIA","IONQ","BLACKSKY"]
SUBREDDITS = ['stocks','wallstreetbets','SpaceX','AI']

# -------- ENVIRONMENT VARIABLES --------
GITHUB_TOKEN = os.environ.get("GH_TOKEN")
EMAIL_FROM = os.environ.get("EMAIL_FROM")
EMAIL_TO = os.environ.get("EMAIL_TO")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")

# -------- FETCH REDDIT SIGNALS (Pushshift workaround) --------
def fetch_reddit_signals():
    signals = {t: {"reddit":0} for t in TICKERS}
    for sub in SUBREDDITS:
        url = f"https://api.pushshift.io/reddit/search/submission/?subreddit={sub}&size=100"
        try:
            data = requests.get(url).json().get('data', [])
            for post in data:
                title = post.get('title', '').upper()
                selftext = post.get('selftext', '').upper()
                for t in TICKERS:
                    if t in title or t in selftext:
                        signals[t]["reddit"] += 1
        except Exception as e:
            print(f"Error fetching Reddit for {sub}: {e}")
    return signals

# -------- FETCH GITHUB SIGNALS --------
def fetch_github_signals():
    g = Github(GITHUB_TOKEN)
    signals = {t: {"github":0} for t in TICKERS}
    for t in ["NVIDIA","IONQ"]:
        try:
            repos = g.search_repositories(query=f"{t} topic:ai")
            signals[t]["github"] = repos.totalCount
        except Exception as e:
            print(f"Error fetching GitHub for {t}: {e}")
    return signals

# -------- PLACEHOLDER FUNCTIONS --------
def fetch_tiktok_signals():
    return {t: {"tiktok":0} for t in TICKERS}
def fetch_youtube_signals():
    return {t: {"youtube":0} for t in TICKERS}
def fetch_vc_signals():
    return {t: {"vc":0} for t in TICKERS}

# -------- SCORE TICKERS --------
def calculate_score(signals):
    weights = {"reddit":0.25, "github":0.15, "tiktok":0.2, "youtube":0.15, "vc":0.25}
    scored = {}
    for t, sig in signals.items():
        score = 0
        for k, w in weights.items():
            score += sig.get(k,0)*w
        scored[t] = {"score":round(score,2), "drivers":[k for k in sig if sig.get(k,0)>0]}
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

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com',465) as server:
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
            print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

# -------- MAIN FUNCTION --------
def main(event=None, context=None):
    reddit_signals = fetch_reddit_signals()
    github_signals = fetch_github_signals()
    tiktok_signals = fetch_tiktok_signals()
    youtube_signals = fetch_youtube_signals()
    vc_signals = fetch_vc_signals()

    # Merge all signals
    all_signals = {}
    for t in TICKERS:
        all_signals[t] = {**reddit_signals.get(t,{}), **github_signals.get(t,{}),
                          **tiktok_signals.get(t,{}), **youtube_signals.get(t,{}),
                          **vc_signals.get(t,{})}

    scored = calculate_score(all_signals)
    top_tickers = dict(sorted(scored.items(), key=lambda x:x[1]['score'], reverse=True)[:TOP_N])
    send_email(top_tickers)
    return "Email process completed!"
