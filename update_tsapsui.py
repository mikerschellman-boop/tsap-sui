import json
import requests
from bs4 import BeautifulSoup
from datetime import date, timedelta
from urllib.parse import urljoin
import xml.etree.ElementTree as ET


SFI_HOME = "https://www.santafe.edu/"
HEYLIGHEN_FEED = "https://francisheylighen.substack.com/feed"
TAIJIQUAN_JOURNAL_FEED = "https://taijiquanjournal.blogspot.com/feeds/posts/default?alt=rss"
JUDITH_WEINGARTEN_FEED = "https://judithweingarten.blogspot.com/feeds/posts/default?alt=rss"
ROGUE_CLASSICISM_FEED = "https://rogueclassicism.com/feed"
LIVING_TAO_STUDY = "https://livingtao.org/seminars/study-materials/"

HISTORY_FILE = "history.json"
OUTPUT_FILE = "tsapsui.json"
SFI_ARCHIVE_FILE = "sfi_archive.json"


# ==========================================
# TEST CONTROLS
# ==========================================

TEST_MODE = True
TEST_SOURCE = "judith_weingarten"

DRY_RUN = False


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

    history.setdefault("taijiquan_journal", {})
    history["taijiquan_journal"].setdefault("published", [])
    history["taijiquan_journal"].setdefault("current_issue", None)

    history.setdefault("judith_weingarten", {})
    history["judith_weingarten"].setdefault("published", [])
    history["judith_weingarten"].setdefault("current_issue", None)

    history.setdefault("rogue_classicism", {})
    history["rogue_classicism"].setdefault("published", [])
    history["rogue_classicism"].setdefault("current_issue", None)

    return history


def save_history(history):
    if DRY_RUN:
        print("DRY RUN: history.json not written.")
        return

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


# ==========================================
# SANTA FE INSTITUTE COLLECTOR
# ==========================================

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


# ==========================================
# TAIJIQUAN JOURNAL COLLECTOR
# ==========================================

def fetch_taijiquan_journal_current():
    response = requests.get(
        TAIJIQUAN_JOURNAL_FEED,
        timeout=30,
        headers={"User-Agent": "Mozilla/5.0"}
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
            "source": "Taijiquan Journal",
            "title": title.strip(),
            "url": link.strip(),
            "published_date": pub_date.strip() if pub_date else None,
            "summary": description.strip() if description else None,
            "archive": False
        })

    return articles


def fetch_judith_weingarten_current():
    response = requests.get(
        JUDITH_WEINGARTEN_FEED,
        timeout=30,
        headers={"User-Agent": "Mozilla/5.0"}
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
            "source": "Zenobia: Empress of the East",
            "author": "Judith Weingarten",
            "title": title.strip(),
            "url": link.strip(),
            "published_date": pub_date.strip() if pub_date else None,
            "summary": description.strip() if description else None,
            "archive": False
        })

    return articles

def fetch_rogue_classicism_current():
    response = requests.get(
        ROGUE_CLASSICISM_FEED,
        timeout=30,
        headers={"User-Agent": "Mozilla/5.0"}
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

        title = title.strip()

        # We want the substantial RC Bulletin posts,
        # not the short "This Day in Ancient History" items.
        if not title.lower().startswith("rc bulletin"):
            continue

        articles.append({
            "source": "Rogue Classicism",
            "title": title,
            "url": link.strip(),
            "published_date": pub_date.strip() if pub_date else None,
            "summary": description.strip() if description else None,
            "archive": False
        })

    return articles


# ==========================================
# LIVING TAO FOUNDATION COLLECTOR
# ==========================================

def fetch_living_tao_current():
    response = requests.get(
        LIVING_TAO_STUDY,
        timeout=30,
        headers={
    "User-Agent": "Mozilla/5.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9"
}
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    articles = []

    for link in soup.find_all("a", href=True):
        title = " ".join(link.get_text(" ", strip=True).split())
        href = link["href"]

        if not title:
            continue

        url = urljoin(LIVING_TAO_STUDY, href)

        # Study-material entries are individual pages beneath this section.
        if "/seminars/study-materials/" not in url:
            continue

        # Don't treat the index itself as an article.
        if url.rstrip("/") == LIVING_TAO_STUDY.rstrip("/"):
            continue

        # Avoid duplicate links to the same study material.
        if any(article["url"] == url for article in articles):
            continue

        articles.append({
            "source": "Living Tao Foundation",
            "title": title,
            "url": url,
            "published_date": None,
            "summary": None,
            "archive": False
        })

    return articles

# ==========================================
# CURRENT COLLECTOR TEST
# ==========================================

if TEST_MODE:
    print("\n--- TEST MODE ---")

    if TEST_SOURCE is None:
        print("No collector selected for testing.")

    elif TEST_SOURCE == "taijiquan_journal":
        articles = fetch_taijiquan_journal_current()

        print(f"Found {len(articles)} Taijiquan Journal articles.")

        for article in articles[:5]:
            print(article["title"])
            print(article["url"])
            print()

    elif TEST_SOURCE == "judith_weingarten":
        articles = fetch_judith_weingarten_current()

        print(f"Found {len(articles)} Judith Weingarten articles.")

        for article in articles[:5]:
            print(article["title"])
            print(article["url"])
            print()

    elif TEST_SOURCE == "rogue_classicism":
        articles = fetch_rogue_classicism_current()

        print(f"Found {len(articles)} Rogue Classicism bulletins.")

        for article in articles[:5]:
            print(article["title"])
            print(article["url"])
            print()

    else:
        print(f"Unknown test source: {TEST_SOURCE}")

    # Stop before the real issue builder.
    raise SystemExit

# ==========================================
# REAL ISSUE BUILDER
# ==========================================

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

# ==========================================
# TAIJIQUAN JOURNAL WEEKLY SELECTION
# ==========================================

taiji_current_issue = history["taijiquan_journal"]["current_issue"]

if (
    taiji_current_issue
    and taiji_current_issue.get("issue_date") == issue_date
):
    taiji_selected = taiji_current_issue["article"]
    print("Taijiquan Journal already selected for this week's issue.")

else:
    taiji_published_urls = set(
        history["taijiquan_journal"]["published"]
    )

    taiji_articles = fetch_taijiquan_journal_current()

    taiji_unpublished = [
        article
        for article in taiji_articles
        if article["url"] not in taiji_published_urls
    ]

    if not taiji_unpublished:
        raise RuntimeError(
            "No unseen Taijiquan Journal articles were found."
        )

    taiji_selected = taiji_unpublished[0]

    history["taijiquan_journal"]["published"].append(
        taiji_selected["url"]
    )

    history["taijiquan_journal"]["current_issue"] = {
        "issue_date": issue_date,
        "article": taiji_selected
    }

    save_history(history)

# ==========================================
# JUDITH WEINGARTEN WEEKLY SELECTION
# ==========================================

judith_current_issue = history["judith_weingarten"]["current_issue"]

if (
    judith_current_issue
    and judith_current_issue.get("issue_date") == issue_date
):
    judith_selected = judith_current_issue["article"]
    print("Judith Weingarten already selected for this week's issue.")

else:
    judith_published_urls = set(
        history["judith_weingarten"]["published"]
    )

    judith_articles = fetch_judith_weingarten_current()

    judith_unpublished = [
        article
        for article in judith_articles
        if article["url"] not in judith_published_urls
    ]

    if not judith_unpublished:
        raise RuntimeError(
            "No unseen Judith Weingarten articles were found."
        )

    judith_selected = judith_unpublished[0]

    history["judith_weingarten"]["published"].append(
        judith_selected["url"]
    )

    history["judith_weingarten"]["current_issue"] = {
        "issue_date": issue_date,
        "article": judith_selected
    }

    save_history(history)

# ==========================================
# ROGUE CLASSICISM WEEKLY SELECTION
# ==========================================

rogue_current_issue = history["rogue_classicism"]["current_issue"]

if (
    rogue_current_issue
    and rogue_current_issue.get("issue_date") == issue_date
):
    rogue_selected = rogue_current_issue["article"]
    print("Rogue Classicism already selected for this week's issue.")

else:
    rogue_published_urls = set(
        history["rogue_classicism"]["published"]
    )

    rogue_articles = fetch_rogue_classicism_current()

    rogue_unpublished = [
        article
        for article in rogue_articles
        if article["url"] not in rogue_published_urls
    ]

    if not rogue_unpublished:
        raise RuntimeError(
            "No unseen Rogue Classicism bulletins were found."
        )

    rogue_selected = rogue_unpublished[0]

    history["rogue_classicism"]["published"].append(
        rogue_selected["url"]
    )

    history["rogue_classicism"]["current_issue"] = {
        "issue_date": issue_date,
        "article": rogue_selected
    }

    save_history(history)

# The displayed date is the Tsap Sui issue date.
selected_for_output = dict(selected)
selected_for_output["date"] = issue_date

taiji_selected_for_output = dict(taiji_selected)
taiji_selected_for_output["date"] = issue_date

judith_selected_for_output = dict(judith_selected)
judith_selected_for_output["date"] = issue_date

rogue_selected_for_output = dict(rogue_selected)
rogue_selected_for_output["date"] = issue_date

data = {
    "issue_date": issue_date,
    "updated": str(date.today()),
    "sections": {
        "complexity": [selected_for_output],
        "taiji": [taiji_selected_for_output],
        "history": [
            judith_selected_for_output,
            rogue_selected_for_output
        ]
    }
}

if DRY_RUN:
    print("\n--- DRY RUN OUTPUT ---")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    print("\nDRY RUN: tsapsui.json not written.")
else:
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
print(f"Issue date: {issue_date}")
print(f"Selected SFI article: {selected['title']}")
print(selected["url"])
