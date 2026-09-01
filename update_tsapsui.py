import json
import requests
from bs4 import BeautifulSoup
from datetime import date, timedelta
from urllib.parse import urljoin
import xml.etree.ElementTree as ET


SFI_HOME = "https://www.santafe.edu/"
HEYLIGHEN_FEED = "https://francisheylighen.substack.com/feed"

def get_issue_date():
    """Return the most recent Sunday."""
    today = date.today()
    days_since_sunday = (today.weekday() + 1) % 7
    return today - timedelta(days=days_since_sunday)


def load_history():
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = json.load(f)
    except FileNotFoundError:
        history = {}

    history.setdefault("sfi", {})
    history["sfi"].setdefault("published", [])
    history["sfi"].setdefault("current_issue", None)

    return history


def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


def extract_sfi_articles(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    articles = []

    for link in soup.find_all("a", href=True):
        href = link["href"]
        title = " ".join(link.get_text(" ", strip=True).split())

        if not title:
            continue

        if "/news-center/news/" not in href:
            continue

        if title.lower() in {
            "learn more",
            "read more",
            "view all news",
            "news"
        }:
            continue

        url = urljoin(base_url, href)

        if url.rstrip("/") == "https://www.santafe.edu/news-center/news":
            continue

        if any(article["url"] == url for article in articles):
            continue

        articles.append({
            "source": "Santa Fe Institute",
            "title": title,
            "url": url,
            "archive": False
        })

    return articles


def fetch_sfi_current():
    response = requests.get(
        SFI_HOME,
        timeout=30,
        headers={"User-Agent": "Tsap-Sui/1.0"}
    )
    response.raise_for_status()

    return extract_sfi_articles(response.text, SFI_HOME)


def fetch_sfi_archive(published_urls):
    with open(SFI_ARCHIVE_FILE, "r", encoding="utf-8") as f:
        archive_articles = json.load(f)

    for article in archive_articles:
        if article["url"] not in published_urls:
            return {
                "source": "Santa Fe Institute",
                "title": article["title"],
                "url": article["url"],
                "published_date": article.get("published_date"),
                "archive": True
            }

    return None

def fetch_heylighen_current():
    response = requests.get(
        HEYLIGHEN_FEED,
        timeout=30,
        headers={"User-Agent": "Tsap-Sui/1.0"}
    )
    response.raise_for_status()

    root = ET.fromstring(response.content)

    articles = []

    for item in root.findall(".//item"):
        title = item.findtext("title")
        link = item.findtext("link")
        pub_date = item.findtext("pubDate")
        description = item.findtext("description")

        if not title or not link:
            continue

        articles.append({
            "source": "Francis Heylighen",
            "origin": "The Self-Organizing Universe",
            "title": title.strip(),
            "url": link.strip(),
            "published_date": pub_date.strip() if pub_date else None,
            "summary": description.strip() if description else None,
            "archive": False
        })

    return articles

# TEMPORARY HEYLIGHEN RSS TEST
print("\n--- HEYLIGHEN RSS TEST ---")

heylighen_test = fetch_heylighen_current()

print(f"Articles found: {len(heylighen_test)}")

if heylighen_test:
    first = heylighen_test[0]

    print(f"Title: {first['title']}")
    print(f"URL: {first['url']}")
    print(f"Published: {first['published_date']}")
    print(f"Origin: {first['origin']}")
    print(f"Archive: {first['archive']}")
    print(f"Summary available: {bool(first['summary'])}")
else:
    print("No Heylighen articles found.")


# ==========================================
# STOP HERE DURING COLLECTOR TESTING
# Nothing below this line will run.
# ==========================================

raise SystemExit

history = load_history()
issue_date = str(get_issue_date())

current_issue = history["sfi"]["current_issue"]

# If SFI already has a selection for this week's issue,
# keep publishing the same one.
if current_issue and current_issue.get("issue_date") == issue_date:
    selected = current_issue["article"]
    print("SFI already selected for this week's issue.")

else:
    published_urls = set(history["sfi"]["published"])

    articles = fetch_sfi_current()

    unpublished = [
        article
        for article in articles
        if article["url"] not in published_urls
    ]

    if unpublished:
        selected = unpublished[0]
        selected["archive"] = False

    else:
        print("No unseen current SFI articles remain.")
        print("Searching the SFI archive...")

        selected = fetch_sfi_archive(published_urls)

    if selected is None:
        raise RuntimeError(
            "No unseen SFI archive articles were found."
        )

    history["sfi"]["published"].append(selected["url"])

    history["sfi"]["current_issue"] = {
        "issue_date": issue_date,
        "article": selected
    }

    save_history(history)

# The displayed date is the Tsap Sui issue date.
selected_for_output = dict(selected)
selected_for_output["date"] = issue_date

data = {
    "issue_date": issue_date,
    "updated": str(date.today()),
    "sections": {
        "complexity": [selected_for_output]
    }
}

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
    
print(f"Issue date: {issue_date}")
print(f"Selected SFI article: {selected['title']}")
print(selected["url"])
