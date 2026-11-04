import json
import re
import time
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse, urlunparse

BASE_URL = "https://cimafu.live"
FEED_URL = BASE_URL + "/feed/"
OUTPUT = Path(__file__).parent / "catalogue.json"

MAX_CATEGORY_PAGES = 8
MAX_CATEGORIES = 40
REQUEST_DELAY = 0.4

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
    )
}


def clean(value):
    value = re.sub(r"<[^>]*>", " ", value or "")
    value = unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def fetch(url):
    request = urllib.request.Request(url, headers=HEADERS)

    try:
        with urllib.request.urlopen(request, timeout=35) as response:
            return response.read()
    except Exception as error:
        print("Could not fetch:", url, "-", error)
        return None


def normalize_url(url):
    url = urljoin(BASE_URL, url)
    parsed = urlparse(url)

    if parsed.netloc.lower() not in (
        "cimafu.live",
        "www.cimafu.live"
    ):
        return ""

    return urlunparse((
        "https",
        "cimafu.live",
        parsed.path.rstrip("/") + "/",
        "",
        "",
        ""
    ))


def detect_type(title, category=""):
    text = (title + " " + category).lower()

    anime_words = [
        "anime", "انمي", "أنمي",
        "كرتون", "cartoon",
        "demon slayer", "naruto",
        "one piece", "bleach"
    ]

    if any(word in text for word in anime_words):
        return "anime"

    series_words = [
        "series", "مسلسل", "مسلسلات",
        "episode", "الحلقة",
        "season", "الموسم",
        "تركية", "كورية",
        "اسيوية", "آسيوية"
    ]

    if any(word in text for word in series_words):
        return "series"

    return "movie"


class PageParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.links = []
        self.current_link = None
        self.current_text = []
        self.current_depth = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)

        if tag == "a" and attrs.get("href"):
            if self.current_link is not None:
                self.finish_link()

            self.current_link = attrs.get("href")
            self.current_text = []
            self.current_depth = 1

        elif self.current_link is not None:
            if tag not in ("img", "br", "hr", "input"):
                self.current_depth += 1

            if tag == "img" and attrs.get("alt"):
                self.current_text.append(attrs.get("alt"))

    def handle_data(self, data):
        if self.current_link is not None:
            self.current_text.append(data)

    def handle_endtag(self, tag):
        if self.current_link is None:
            return

        if tag == "a":
            self.finish_link()
        elif tag not in ("br", "hr", "img", "input"):
            self.current_depth -= 1
            if self.current_depth <= 0:
                self.finish_link()

    def finish_link(self):
        if self.current_link is not None:
            self.links.append({
                "url": self.current_link,
                "text": clean(" ".join(self.current_text))
            })

        self.current_link = None
        self.current_text = []
        self.current_depth = 0


def is_category_url(url):
    path = urlparse(url).path.lower()

    return (
        "/category/" in path
        or "/genre/" in path
        or "/type/" in path
    )


def is_post_url(url):
    path = urlparse(url).path.lower()

    if not path or path == "/":
        return False

    excluded = [
        "/category/",
        "/genre/",
        "/type/",
        "/tag/",
        "/author/",
        "/page/",
        "/wp-",
        "/feed/",
        "/search/",
        "/privacy",
        "/contact",
        "/about"
    ]

    if any(part in path for part in excluded):
        return False

    if path.endswith((".jpg", ".jpeg", ".png", ".webp", ".css", ".js")):
        return False

    return True


def parse_page(html):
    parser = PageParser()
    parser.feed(html.decode("utf-8", errors="replace"))
    return parser.links


def add_item(items, seen, title, url, description="", category=""):
    title = clean(title)
    url = normalize_url(url)

    if not title or not url or not is_post_url(url):
        return

    if url in seen:
        return

    seen.add(url)

    items.append({
        "title": title,
        "url": url,
        "description": clean(description)[:500],
        "type": detect_type(title, category),
        "category": clean(category)
    })


def get_categories(home_html):
    categories = {}

    for link in parse_page(home_html):
        url = normalize_url(link["url"])
        name = clean(link["text"])

        if not url or not name:
            continue

        if is_category_url(url):
            categories[url] = name

    return categories


def scrape_listing(url, category, items, seen):
    html = fetch(url)

    if not html:
        return 0

    links = parse_page(html)
    before = len(items)

    for link in links:
        post_url = normalize_url(link["url"])
        title = link["text"]

        if not post_url or not title:
            continue

        if is_post_url(post_url):
            add_item(
                items,
                seen,
                title,
                post_url,
                "",
                category
            )

    return len(items) - before


def scrape_feed(items, seen):
    print("Reading RSS feed...")

    data = fetch(FEED_URL)

    if not data:
        return

    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        print("RSS feed could not be parsed.")
        return

    for entry in root.findall(".//item"):
        title = entry.findtext("title", default="")
        link = entry.findtext("link", default="")
        description = entry.findtext("description", default="")

        add_item(
            items,
            seen,
            title,
            link,
            description,
            ""
        )


def main():
    items = []
    seen = set()

    print("Fetching Cima4U homepage...")

    home = fetch(BASE_URL + "/")

    if not home:
        raise RuntimeError(
            "Could not download Cima4U homepage. "
            "Keeping the existing catalogue."
        )

    categories = get_categories(home)

    print("Categories discovered:", len(categories))

    # Collect titles from the homepage.
    for link in parse_page(home):
        url = normalize_url(link["url"])

        if url and is_post_url(url) and link["text"]:
            add_item(
                items,
                seen,
                link["text"],
                url
            )

    # Collect titles from category pages.
    category_list = list(categories.items())[:MAX_CATEGORIES]

    for index, (category_url, category_name) in enumerate(
        category_list,
        start=1
    ):
        print(
            "[" + str(index) + "/" + str(len(category_list)) + "]",
            category_name
        )

        for page_number in range(1, MAX_CATEGORY_PAGES + 1):
            if page_number == 1:
                page_url = category_url
            else:
                page_url = (
                    category_url.rstrip("/")
                    + "/page/"
                    + str(page_number)
                    + "/"
                )

            count = scrape_listing(
                page_url,
                category_name,
                items,
                seen
            )

            if page_number > 1 and count == 0:
                break

            time.sleep(REQUEST_DELAY)

    # Import additional entries from RSS.
    scrape_feed(items, seen)

    if not items:
        raise RuntimeError(
            "No titles were collected. "
            "The existing catalogue was not replaced."
        )

    # Save only after successful collection.
    OUTPUT.write_text(
        json.dumps(items, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print("")
    print("Catalogue successfully saved.")
    print("Total titles:", len(items))
    print("Movies:", sum(1 for x in items if x["type"] == "movie"))
    print("Series:", sum(1 for x in items if x["type"] == "series"))
    print("Anime:", sum(1 for x in items if x["type"] == "anime"))
    print("Saved to:", OUTPUT)


if __name__ == "__main__":
    main()
