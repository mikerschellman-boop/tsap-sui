import json
import requests
from bs4 import BeautifulSoup
from datetime import date, timedelta
from urllib.parse import urljoin
import xml.etree.ElementTree as ET


SFI_HOME = "https://www.santafe.edu/"
HEYLIGHEN_FEED = "https://square-sunset-4b67.mike-r-schellman.workers.dev/feed/heylighen"
CASSIE_FEED = "https://square-sunset-4b67.mike-r-schellman.workers.dev/feed/cassie"
SLOW_PEACE_FEED = "https://square-sunset-4b67.mike-r-schellman.workers.dev/feed/slowpeace"
JAMES_KA_SMITH_FEED = "https://square-sunset-4b67.mike-r-schellman.workers.dev/feed/jameskasmith"
PROCESS_THIS_FEED = "https://square-sunset-4b67.mike-r-schellman.workers.dev/feed/processthis"
INTERTEXTUAL_BIBLE_FEED = "https://square-sunset-4b67.mike-r-schellman.workers.dev/feed/intertextualbible"
TAIJIQUAN_JOURNAL_FEED = "https://taijiquanjournal.blogspot.com/feeds/posts/default?alt=rss"
JUDITH_WEINGARTEN_FEED = "https://judithweingarten.blogspot.com/feeds/posts/default?alt=rss"
ROGUE_CLASSICISM_FEED = "https://rogueclassicism.com/feed"
LIVING_TAO_STUDY = "https://livingtao.org/seminars/study-materials/"
BENEBELL_WEN_FEED = "https://benebellwen.com/feed/"
DIGITAL_AMBLER_FEED = "https://digitalambler.com/feed/"
GOETEIA_BLOG = "https://goeteia.com/blog"

HISTORY_FILE = "history.json"
OUTPUT_FILE = "tsapsui.json"
SFI_ARCHIVE_FILE = "sfi_archive.json"


# ==========================================
# TEST CONTROLS
# ==========================================

TEST_MODE = True
TEST_SOURCE = "esoterica"

DRY_RUN = True


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

    history.setdefault("heylighen", {})
    history["heylighen"].setdefault("published", [])
    history["heylighen"].setdefault("current_issue", None)

    history.setdefault("taijiquan_journal", {})
    history["taijiquan_journal"].setdefault("published", [])
    history["taijiquan_journal"].setdefault("current_issue", None)

    history.setdefault("slow_peace", {})
    history["slow_peace"].setdefault("published", [])
    history["slow_peace"].setdefault("current_issue", None)

    history.setdefault("james_ka_smith", {})
    history["james_ka_smith"].setdefault("published", [])
    history["james_ka_smith"].setdefault("current_issue", None)

    history.setdefault("process_this", {})
    history["process_this"].setdefault("published", [])
    history["process_this"].setdefault("current_issue", None)

    history.setdefault("intertextual_bible", {})
    history["intertextual_bible"].setdefault("published", [])
    history["intertextual_bible"].setdefault("current_issue", None)

    history.setdefault("judith_weingarten", {})
    history["judith_weingarten"].setdefault("published", [])
    history["judith_weingarten"].setdefault("current_issue", None)

    history.setdefault("cassie", {})
    history["cassie"].setdefault("published", [])
    history["cassie"].setdefault("current_issue", None)

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
# FRANCIS HEYLIGHEN COLLECTOR
# ==========================================

def fetch_heylighen_current():
    response = requests.get(
        HEYLIGHEN_FEED,
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
            "source": "The Self-Organizing Universe",
            "author": "Francis Heylighen",
            "title": title.strip(),
            "url": link.strip(),
            "published_date": pub_date.strip() if pub_date else None,
            "summary": description.strip() if description else None,
            "archive": False
        })

    return articles


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
            "summary": None,
            "archive": False
        })

    return articles


# ==========================================
# SLOW PEACE COLLECTOR
# ==========================================

def fetch_slow_peace_current():
    response = requests.get(
        SLOW_PEACE_FEED,
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

        summary = description.strip() if description else None
        summary_lower = summary.lower() if summary else ""

        # Slow Peace identifies paid-only material in its public RSS teaser.
        if "paid subscriber" in summary_lower or "paid-only" in summary_lower:
            access = "subscription"
        else:
            access = "open"

        articles.append({
            "source": "Slow Peace",
            "author": "Morgan Buchanan",
            "title": title.strip(),
            "url": link.strip(),
            "published_date": pub_date.strip() if pub_date else None,
            "summary": summary,
            "access": access,
            "support_url": "https://morganbuchanan.substack.com/",
            "support_label": "Support this writer",
            "archive": False
        })

    return articles


# ==========================================
# CHRISTIANITY / SUBSTACK COLLECTORS
# ==========================================

def fetch_substack_current(feed_url, source, author=None, support_url=None):
    """Collect only metadata exposed by the public RSS feed."""
    response = requests.get(feed_url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
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

        summary = description.strip() if description else None
        lower = summary.lower() if summary else ""
        access = "subscription" if any(
            phrase in lower for phrase in ("paid subscriber", "paid-only", "paid subscription")
        ) else "open"

        article = {
            "source": source, "title": title.strip(), "url": link.strip(),
            "published_date": pub_date.strip() if pub_date else None,
            "summary": summary, "access": access, "archive": False
        }
        if author:
            article["author"] = author
        if support_url:
            article["support_url"] = support_url
            article["support_label"] = "Support this writer"
        articles.append(article)
    return articles


def fetch_james_ka_smith_current():
    return fetch_substack_current(
        JAMES_KA_SMITH_FEED, "Quid Amo", "James K.A. Smith",
        "https://jameskasmith.substack.com/"
    )


def fetch_process_this_current():
    return fetch_substack_current(
        PROCESS_THIS_FEED, "Process This", "Tripp Fuller",
        "https://processthis.substack.com/"
    )


def fetch_intertextual_bible_current():
    return fetch_substack_current(
        INTERTEXTUAL_BIBLE_FEED, "Intertextual Bible", None,
        "https://intertextualbible.substack.com/"
    )

# ==========================================
# BENEBELL WEN COLLECTOR
# ==========================================

def fetch_benebell_wen_current():
    response = requests.get(
        BENEBELL_WEN_FEED,
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

        # Don't surface protected material in Tsap Sui.
        title_lower = title.lower()
        if "protected:" in title_lower:
            continue

        articles.append({
            "source": "Benebell Wen",
            "author": "Benebell Wen",
            "title": title.strip(),
            "url": link.strip(),
            "published_date": pub_date.strip() if pub_date else None,
            "summary": None,
            "archive": False
        })

    return articles


# ==========================================
# DIGITAL AMBLER COLLECTOR
# ==========================================

def fetch_digital_ambler_current():
    response = requests.get(
        DIGITAL_AMBLER_FEED,
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

        if not title or not link:
            continue

        articles.append({
            "source": "The Digital Ambler",
            "author": "Sam Block",
            "title": title.strip(),
            "url": link.strip(),
            "published_date": pub_date.strip() if pub_date else None,
            "summary": None,
            "archive": False
        })

    return articles

# ==========================================
# GOETEIA / FRATER ACHER COLLECTOR
# ==========================================

def fetch_goeteia_current():
    response = requests.get(
        GOETEIA_BLOG,
        timeout=30,
        headers={"User-Agent": "Mozilla/5.0"}
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    articles = []

    links = soup.find_all("a", href=True)

    print(f"Goêteia page returned {len(links)} links total.")

    seen = set()

    for link in links:
        text = " ".join(link.get_text(" ", strip=True).split())
        href = link.get("href")

        if not text or not href:
            continue

        # Ignore short navigation labels so we can see likely article titles.
        if len(text) < 20:
            continue

        if href in seen:
            continue

        seen.add(href)

        print("TEXT:", repr(text))
        print("HREF:", repr(href))
        print()
            
    return articles
    
# ==========================================
# CASSIE / SERIOUSLY MEDIEVAL COLLECTOR
# ==========================================

def fetch_cassie_current():
    response = requests.get(
        CASSIE_FEED,
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
            "source": "Seriously Medieval",
            "author": "Cassie Beyer",
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

    # Judith's Blogger/FeedBurner feed is Atom, not RSS.
    atom = {"atom": "http://www.w3.org/2005/Atom"}

    articles = []

    for entry in root.findall("atom:entry", atom):
        title = entry.findtext("atom:title", default="", namespaces=atom)
        published = entry.findtext(
            "atom:published",
            default="",
            namespaces=atom
        )
        summary = entry.findtext(
            "atom:summary",
            default="",
            namespaces=atom
        )

        # Blogger Atom entries can contain several links.
        # We specifically want the normal article permalink.
        link = None

        for link_element in entry.findall("atom:link", atom):
            if link_element.get("rel") == "alternate":
                link = link_element.get("href")
                break

        if not title or not link:
            continue

        articles.append({
            "source": "Zenobia: Empress of the East",
            "author": "Judith Weingarten",
            "title": title.strip(),
            "url": link.strip(),
            "published_date": published.strip() if published else None,
            "summary": None,
            "archive": True
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
            "summary": None,
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

    elif TEST_SOURCE == "heylighen":
        articles = fetch_heylighen_current()

        print(f"Found {len(articles)} Francis Heylighen articles.")

        for article in articles[:5]:
            print(article["title"])
            print(article["url"])
            print()

    elif TEST_SOURCE == "taijiquan_journal":
        articles = fetch_taijiquan_journal_current()

        print(f"Found {len(articles)} Taijiquan Journal articles.")

        for article in articles[:5]:
            print(article["title"])
            print(article["url"])
            print()

    elif TEST_SOURCE == "slow_peace":
        articles = fetch_slow_peace_current()

        print(f"Found {len(articles)} Slow Peace articles.")

        for article in articles[:5]:
            print(article["title"])
            print(f"Access: {article['access']}")
            print(article["url"])
            print()

    elif TEST_SOURCE in {"james_ka_smith", "process_this", "intertextual_bible"}:
        fetchers = {
            "james_ka_smith": fetch_james_ka_smith_current,
            "process_this": fetch_process_this_current,
            "intertextual_bible": fetch_intertextual_bible_current,
        }
        articles = fetchers[TEST_SOURCE]()
        print(f"Found {len(articles)} {TEST_SOURCE} articles.")
        for article in articles[:5]:
            print(article["title"])
            print(f"Access: {article['access']}")
            print(article["url"])
            print()

    elif TEST_SOURCE == "cassie":
        articles = fetch_cassie_current()

        print(f"Found {len(articles)} Cassie Beyer articles.")

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

    elif TEST_SOURCE == "esoterica":
        benebell_articles = fetch_benebell_wen_current()
        digital_ambler_articles = fetch_digital_ambler_current()
        goeteia_articles = fetch_goeteia_current()

        print(f"Found {len(benebell_articles)} Benebell Wen articles.")

        for article in benebell_articles[:5]:
            print(article["title"])
            print(article["url"])
            print()

        print(f"Found {len(digital_ambler_articles)} Digital Ambler articles.")

        for article in digital_ambler_articles[:5]:
            print(article["title"])
            print(article["url"])
            print()

        print(f"Found {len(goeteia_articles)} Goêteia articles.")

        for article in goeteia_articles[:5]:
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
# FRANCIS HEYLIGHEN WEEKLY SELECTION
# ==========================================

heylighen_current_issue = history["heylighen"]["current_issue"]

if (
    heylighen_current_issue
    and heylighen_current_issue.get("issue_date") == issue_date
):
    heylighen_selected = heylighen_current_issue["article"]
    print("Francis Heylighen already selected for this week's issue.")

else:
    heylighen_published_urls = set(
        history["heylighen"]["published"]
    )

    heylighen_articles = fetch_heylighen_current()

    heylighen_unpublished = [
        article
        for article in heylighen_articles
        if article["url"] not in heylighen_published_urls
    ]

    if not heylighen_unpublished:
        raise RuntimeError(
            "No unseen Francis Heylighen articles were found."
        )

    heylighen_selected = heylighen_unpublished[0]

    history["heylighen"]["published"].append(
        heylighen_selected["url"]
    )

    history["heylighen"]["current_issue"] = {
        "issue_date": issue_date,
        "article": heylighen_selected
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
# SLOW PEACE WEEKLY SELECTION
# ==========================================

slow_peace_current_issue = history["slow_peace"]["current_issue"]

if (
    slow_peace_current_issue
    and slow_peace_current_issue.get("issue_date") == issue_date
):
    slow_peace_selected = slow_peace_current_issue["article"]
    print("Slow Peace already selected for this week's issue.")

else:
    slow_peace_published_urls = set(
        history["slow_peace"]["published"]
    )

    slow_peace_articles = fetch_slow_peace_current()

    slow_peace_unpublished = [
        article
        for article in slow_peace_articles
        if article["url"] not in slow_peace_published_urls
    ]

    if not slow_peace_unpublished:
        raise RuntimeError(
            "No unseen Slow Peace articles were found."
        )

    slow_peace_selected = slow_peace_unpublished[0]

    history["slow_peace"]["published"].append(
        slow_peace_selected["url"]
    )

    history["slow_peace"]["current_issue"] = {
        "issue_date": issue_date,
        "article": slow_peace_selected
    }

    save_history(history)


# ==========================================
# CHRISTIANITY WEEKLY SELECTIONS
# ==========================================

def select_weekly_article(history, history_key, issue_date, fetcher, display_name):
    current_issue = history[history_key]["current_issue"]
    if current_issue and current_issue.get("issue_date") == issue_date:
        print(f"{display_name} already selected for this week's issue.")
        return current_issue["article"]

    published_urls = set(history[history_key]["published"])
    unpublished = [a for a in fetcher() if a["url"] not in published_urls]
    if not unpublished:
        raise RuntimeError(f"No unseen {display_name} articles were found.")

    selected_article = unpublished[0]
    history[history_key]["published"].append(selected_article["url"])
    history[history_key]["current_issue"] = {
        "issue_date": issue_date, "article": selected_article
    }
    save_history(history)
    return selected_article


james_ka_smith_selected = select_weekly_article(
    history, "james_ka_smith", issue_date, fetch_james_ka_smith_current, "James K.A. Smith"
)
process_this_selected = select_weekly_article(
    history, "process_this", issue_date, fetch_process_this_current, "Process This"
)
intertextual_bible_selected = select_weekly_article(
    history, "intertextual_bible", issue_date, fetch_intertextual_bible_current, "Intertextual Bible"
)


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
# CASSIE / SERIOUSLY MEDIEVAL WEEKLY SELECTION
# ==========================================

cassie_current_issue = history["cassie"]["current_issue"]

if (
    cassie_current_issue
    and cassie_current_issue.get("issue_date") == issue_date
):
    cassie_selected = cassie_current_issue["article"]
    print("Cassie Beyer already selected for this week's issue.")

else:
    cassie_published_urls = set(
        history["cassie"]["published"]
    )

    cassie_articles = fetch_cassie_current()

    cassie_unpublished = [
        article
        for article in cassie_articles
        if article["url"] not in cassie_published_urls
    ]

    if not cassie_unpublished:
        raise RuntimeError(
            "No unseen Cassie Beyer articles were found."
        )

    cassie_selected = cassie_unpublished[0]

    history["cassie"]["published"].append(
        cassie_selected["url"]
    )

    history["cassie"]["current_issue"] = {
        "issue_date": issue_date,
        "article": cassie_selected
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

heylighen_selected_for_output = dict(heylighen_selected)
heylighen_selected_for_output["date"] = issue_date

taiji_selected_for_output = dict(taiji_selected)
taiji_selected_for_output["date"] = issue_date

slow_peace_selected_for_output = dict(slow_peace_selected)
slow_peace_selected_for_output["date"] = issue_date

james_ka_smith_selected_for_output = dict(james_ka_smith_selected)
james_ka_smith_selected_for_output["date"] = issue_date

process_this_selected_for_output = dict(process_this_selected)
process_this_selected_for_output["date"] = issue_date

intertextual_bible_selected_for_output = dict(intertextual_bible_selected)
intertextual_bible_selected_for_output["date"] = issue_date

judith_selected_for_output = dict(judith_selected)
judith_selected_for_output["date"] = issue_date

cassie_selected_for_output = dict(cassie_selected)
cassie_selected_for_output["date"] = issue_date

rogue_selected_for_output = dict(rogue_selected)
rogue_selected_for_output["date"] = issue_date

data = {
    "issue_date": issue_date,
    "updated": str(date.today()),
    "sections": {
        "complexity": [
            selected_for_output,
            heylighen_selected_for_output
        ],
        "taiji": [
            taiji_selected_for_output,
            slow_peace_selected_for_output
        ],
        "history": [
            judith_selected_for_output,
            cassie_selected_for_output,
            rogue_selected_for_output
        ],
        "christianity": [
            james_ka_smith_selected_for_output,
            process_this_selected_for_output,
            intertextual_bible_selected_for_output
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
