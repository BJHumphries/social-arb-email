import os
import requests
from github import Github
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# -------- CONFIG --------
TOP_N = 20
TICKERS = ["RKLB", "ASTS", "NVDA", "IONQ", "BKSY"]
SUBREDDITS = ["stocks", "wallstreetbets", "SpaceX", "artificial"]

# -------- ENVIRONMENT VARIABLES --------
GITHUB_TOKEN = os.environ.get("GH_TOKEN")
EMAIL_FROM = os.environ.get("EMAIL_FROM")
EMAIL_TO = os.environ.get("EMAIL_TO")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")

# -------- FETCH REDDIT SIGNALS --------
def fetch_reddit_signals():
    print("Fetching Reddit signals...")
    signals = {t: {"reddit": 0} for t in TICKERS}

    for sub in SUBREDDITS:
        try:
            url = f"https://api.pushshift.io/reddit/search/submission/?subreddit={sub}&size=100"
            response = requests.get(url, timeout=10)

            if response.status_code != 200:
                print(f"Reddit API error for {sub}")
                continue

            posts = response.json().get("data", [])

            for post in posts:
                text = (post.get("title", "") + post.get("selftext", "")).upper()

                for ticker in TICKERS:
                    if ticker in text:
                        signals[ticker]["reddit"] += 1

        except Exception as e:
            print(f"Reddit fetch error: {e}")

    print("Reddit signals:", signals)
    return signals


# -------- FETCH GITHUB SIGNALS --------
def fetch_github_signals():
    print("Fetching GitHub signals...")
    signals = {t: {"github": 0} for t in TICKERS}

    try:
        g = Github(GITHUB_TOKEN)

        for ticker in ["NVDA", "IONQ"]:
            try:
                repos = g.search_repositories(query=ticker)
                signals[ticker]["github"] = repos.totalCount
            except Exception as e:
                print(f"GitHub query error for {ticker}: {e}")

    except Exception as e:
        print("GitHub connection error:", e)

    print("GitHub signals:", signals)
    return signals


# -------- PLACEHOLDER SIGNAL SOURCES --------
def fetch_tiktok_signals():
    print("TikTok signals placeholder")
    return {t: {"tiktok": 0} for t in TICKERS}


def fetch_youtube_signals():
    print("YouTube signals placeholder")
    return {t: {"youtube": 0} for t in TICKERS}


def fetch_vc_signals():
    print("VC signals placeholder")
    return {t: {"vc": 0} for t in TICKERS}


# -------- SCORE TICKERS --------
def calculate_score(signals):
    print("Scoring tickers...")

    weights = {
        "reddit": 0.25,
        "github": 0.15,
        "tiktok": 0.2,
        "youtube": 0.15,
        "vc": 0.25,
    }

    scored = {}

    for ticker, sig in signals.items():
        score = 0

        for key, weight in weights.items():
            score += sig.get(key, 0) * weight

        scored[ticker] = {
            "score": round(score, 2),
            "drivers": [k for k in sig if sig.get(k, 0) > 0],
        }

    print("Scores:", scored)
    return scored


# -------- SEND EMAIL --------
def send_email(top_tickers):
    print("Preparing email...")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Daily Pre-Market Asymmetric Trade Watchlist"
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO

    html = """
    <h2>Top Asymmetric Trade Candidates</h2>
    <table border='1'>
    <tr>
    <th>Rank</th>
    <th>Ticker</th>
    <th>Score</th>
    <th>Signals</th>
    </tr>
    """

    for i, (ticker, data) in enumerate(top_tickers.items(), start=1):
        html += f"""
        <tr>
        <td>{i}</td>
        <td>{ticker}</td>
        <td>{data['score']}</td>
        <td>{', '.join(data['drivers'])}</td>
        </tr>
        """

    html += "</table>"

    msg.attach(MIMEText(html, "html"))

    try:
        print("Connecting to Gmail SMTP...")

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())

        print("Email sent successfully!")

    except Exception as e:
        print("Email sending failed:", e)


# -------- MAIN --------
def main():
    print("Starting asymmetric trade scanner...")

    reddit_signals = fetch_reddit_signals()
    github_signals = fetch_github_signals()
    tiktok_signals = fetch_tiktok_signals()
    youtube_signals = fetch_youtube_signals()
    vc_signals = fetch_vc_signals()

    # merge signals
    all_signals = {}

    for ticker in TICKERS:
        all_signals[ticker] = {
            **reddit_signals.get(ticker, {}),
            **github_signals.get(ticker, {}),
            **tiktok_signals.get(ticker, {}),
            **youtube_signals.get(ticker, {}),
            **vc_signals.get(ticker, {}),
        }

    scored = calculate_score(all_signals)

    top_tickers = dict(
        sorted(scored.items(), key=lambda x: x[1]["score"], reverse=True)[:TOP_N]
    )

    print("Top tickers:", top_tickers)

    send_email(top_tickers)


# -------- EXECUTE SCRIPT --------
if __name__ == "__main__":
    main()
