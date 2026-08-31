import json
import requests
from bs4 import BeautifulSoup
from datetime import date
from urllib.parse import urljoin

SFI_HOME = "https://www.santafe.edu/"
HISTORY_FILE = "history.json"
OUTPUT_FILE = "tsapsui.json"


def load_history():
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "sfi": {
                "published": []
            }
        }


def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


def fetch_sfi_articles():
    response = requests.get(
        SFI_HOME,
        timeout=30,
        headers={"User-Agent": "Tsap-Sui/1.0"}
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
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
            "view all news",
            "news"
        }:
            continue

        url = urljoin(SFI_HOME, href)

        if url.rstrip("/") == "https://www.santafe.edu/news-center/news":
            continue

        if any(article["url"] == url for article in articles):
            continue

        articles.append({
            "source": "Santa Fe Institute",
            "title": title,
            "url": url,
            "date": str(date.today()),
            "archive": False
        })

    return articles


history = load_history()

published_urls = set(history["sfi"]["published"])

articles = fetch_sfi_articles()

if not articles:
    raise RuntimeError("No SFI news articles were found.")

unpublished = [
    article
    for article in articles
    if article["url"] not in published_urls
]

if unpublished:
    selected = unpublished[0]
    selected["archive"] = False
else:
    # Temporary archive behavior:
    # reuse the oldest visible SFI article if all current ones have appeared
    selected = articles[-1]
    selected["archive"] = True

# Remember this article
if selected["url"] not in published_urls:
    history["sfi"]["published"].append(selected["url"])

save_history(history)

data = {
    "updated": str(date.today()),
    "sections": {
        "complexity": [selected]
    }
}

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"Selected SFI article: {selected['title']}")
print(f"Archive: {selected['archive']}")
print(selected["url"])
