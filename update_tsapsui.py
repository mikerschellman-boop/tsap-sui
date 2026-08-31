import json
import requests
from bs4 import BeautifulSoup
from datetime import date
from urllib.parse import urljoin

SFI_HOME = "https://www.santafe.edu/"

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

    # Ignore generic navigation links
    if title.lower() in {
        "learn more",
        "view all news",
        "news"
    }:
        continue

    url = urljoin(SFI_HOME, href)

    if url.rstrip("/") == "https://www.santafe.edu/news-center/news":
        continue

    # Avoid duplicate URLs
    if any(article["url"] == url for article in articles):
        continue

    articles.append({
        "source": "Santa Fe Institute",
        "title": title,
        "url": url,
        "date": str(date.today()),
        "archive": False
    })

if not articles:
    raise RuntimeError("No SFI news articles were found.")

selected = articles[0]

data = {
    "updated": str(date.today()),
    "sections": {
        "complexity": [selected]
    }
}

with open("tsapsui.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"Selected SFI article: {selected['title']}")
print(selected["url"])
