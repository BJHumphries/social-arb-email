import os
import praw
from github import Github
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from google.cloud import secretmanager

# -------- CONFIG --------
TOP_N = 20
TICKERS = ["RKLB","ASTS","NVIDIA","IONQ","BLACKSKY"]  # Example tickers
SUBREDDITS = ['stocks','wallstreetbets','SpaceX','AI']

# -------- HELPER: Get secret from Secret Manager --------
def get_secret(secret_name):
    client = secretmanager.SecretManagerServiceClient()
    project_id = os.environ['GCP_PROJECT']
    name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

# Pull secrets
REDDIT_CLIENT_ID = get_secret("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = get_secret("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = "asym_trader"
GITHUB_TOKEN = get_secret("GITHUB_TOKEN")
EMAIL_FROM = get_secret("EMAIL_FROM")
EMAIL_TO = get_secret("EMAIL_TO")
EMAIL_PASSWORD = get_secret("EMAIL_PASSWORD")

# -------- FETCH SIGNALS --------
def fetch_reddit_signals():
    reddit = praw.Reddit(client_id=REDDIT_CLIENT_ID,
                         client_secret=REDDIT_CLIENT_SECRET,
                         user_agent=REDDIT_USER_AGENT)
    signals = {t: {"reddit":0} for t in TICKERS}
    for sub in SUBREDDITS:
        for post in reddit.subreddit(sub).hot(limit=100):
            for t in TICKERS:
                if t in post.title.upper() or t in post.selftext.upper():
                    signals[t]["reddit"] += 1
    return signals

def fetch_github_signals():
    g = Github(GITHUB_TOKEN)
    signals = {t: {"github":0} for t in TICKERS}
    for t in ["NVIDIA","IONQ"]:  # Example AI/Quantum
        repos = g.search_repositories(query=f"{t} topic:ai")
        signals[t]["github"] = repos.totalCount
    return signals

# Placeholder functions for TikTok, YouTube, VC APIs
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

    with smtplib.SMTP_SSL('smtp.gmail.com',465) as server:
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())

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
    return "Email sent successfully!"
