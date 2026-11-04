import json
import re
import time
import urllib.request
import xml.etree.ElementTree as ET
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse, urlunparse

BASE = "https://cimafu.live"
FEED = BASE + "/feed/"
OUTPUT = Path(__file__).parent / "catalogue.json"

MAX_CATEGORIES = 40
MAX_PAGES = 8
MAX_DETAILS = 300
DELAY = 0.35

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
    )
}


def clean(value):
    value = re.sub(r"<[^>]*>", " ", value or "")
    return re.sub(r"\s+", " ", unescape(value)).strip()


def fetch(url):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.read().decode("utf-8", errors="replace")
    except Exception as error:
        print("Fetch failed:", url, error)
        return ""


def local_url(url):
    url = urljoin(BASE, url)
    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        return ""

    if parsed.netloc.lower() not in ("cimafu.live", "www.cimafu.live"):
        return ""

    return urlunparse((
        "https", "cimafu.live", parsed.path, "", "", ""
    ))


def detect_type(title, category=""):
    value = (title + " " + category).lower()

    if any(x in value for x in (
        "anime", "انمي", "أنمي", "naruto",
        "demon slayer", "one piece", "bleach"
    )):
        return "anime"

    if any(x in value for x in (
        "مسلسل", "الحلقة", "الموسم",
        "episode", "season", "series"
    )):
        return "series"

    return "movie"


class Parser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.links = []
        self.servers = []
        self.images = []
        self.categories = []
        self.current = None
        self.depth = 0
        self.text_parts = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)

        if tag == "a" and a.get("href"):
            if self.current:
                self.finish_link()

            self.current = a["href"]
            self.text_parts = []
            self.depth = 1

        elif self.current and tag not in (
            "img", "br", "hr", "input", "source"
        ):
            self.depth += 1

        if tag == "img":
            src = a.get("data-src") or a.get("data-lazy-src") or a.get("src")
            if src:
                self.images.append(src)

        for key in ("data-server", "data-url", "data-embed"):
            value = a.get(key)
            if value:
                self.servers.append(value)

        if tag == "iframe" and a.get("src"):
            self.servers.append(a["src"])

    def handle_data(self, data):
        if self.current:
            self.text_parts.append(data)

    def handle_endtag(self, tag):
        if self.current is None:
            return

        if tag == "a":
            self.finish_link()
        elif tag not in ("img", "br", "hr", "input", "source"):
            self.depth -= 1
            if self.depth <= 0:
                self.finish_link()

    def finish_link(self):
        if self.current:
            self.links.append({
                "url": self.current,
                "title": clean(" ".join(self.text_parts))
            })

        self.current = None
        self.text_parts = []
        self.depth = 0


def parse(html):
    parser = Parser()
    parser.feed(html)
    return parser


def is_category(url):
    path = urlparse(url).path.lower()
    return "/category/" in path or "/genre/" in path


def is_post(url):
    path = urlparse(url).path.lower()

    if not path or path == "/":
        return False

    blocked = (
        "/category/", "/tag/", "/author/",
        "/page/", "/feed/", "/wp-",
        "/search/", "/privacy", "/contact"
    )

    if any(x in path for x in blocked):
        return False

    return True


def add_title(items, seen, title, url, category=""):
    url = local_url(url)
    title = clean(title)

    if not url or not title or not is_post(url):
        return

    if url in seen:
        return

    seen.add(url)

    items.append({
        "title": title,
        "url": url,
        "description": "",
        "type": detect_type(title, category),
        "category": category,
        "poster": "",
        "servers": []
    })


def collect_feed(items, seen):
    print("Reading RSS feed...")
    data = fetch(FEED)

    if not data:
        return

    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        print("RSS feed parsing failed.")
        return

    for entry in root.findall(".//item"):
        add_title(
            items,
            seen,
            entry.findtext("title", ""),
            entry.findtext("link", "")
        )


def collect_categories(home):
    found = {}

    for link in parse(home).links:
        url = local_url(link["url"])
        name = clean(link["title"])

        if url and name and is_category(url):
            found[url] = name

    return list(found.items())[:MAX_CATEGORIES]


def collect_listing(url, category, items, seen):
    html = fetch(url)

    if not html:
        return 0

    before = len(items)
    parser = parse(html)

    for link in parser.links:
        post_url = local_url(link["url"])

        if post_url and link["title"] and is_post(post_url):
            add_title(
                items,
                seen,
                link["title"],
                post_url,
                category
            )

    return len(items) - before


def extract_details(item):
    html = fetch(item["url"])

    if not html:
        return

    parser = parse(html)

    # Extract description.
    description = re.search(
        r'<meta[^>]+(?:name=["\']description["\']|'
        r'property=["\']og:description["\'])'
        r'[^>]+content=["\']([^"\']+)',
        html,
        re.I
    )

    if description:
        item["description"] = clean(description.group(1))[:1000]

    # Extract poster.
    poster = re.search(
        r'<meta[^>]+property=["\']og:image["\']'
        r'[^>]+content=["\']([^"\']+)',
        html,
        re.I
    )

    if poster:
        item["poster"] = urljoin(item["url"], poster.group(1))
    elif parser.images:
        item["poster"] = urljoin(item["url"], parser.images[0])

    # Extract embedded server URLs.
    servers = []

    for value in parser.servers:
        value = unescape(value).strip()

        if value.startswith("//"):
            value = "https:" + value

        if value.startswith("https://"):
            if value not in servers:
                servers.append(value)

    # Extract server URLs from common server-list markup.
    server_block = re.search(
        r'<(?:ul|div)[^>]*(?:server_list|servers-list|'
        r'player-list)[^>]*>(.*?)</(?:ul|div)>',
        html,
        re.I | re.S
    )

    if server_block:
        block = server_block.group(1)

        for match in re.findall(
            r'(?:data-server|data-url|data-embed|src)\s*=\s*'
            r'["\']([^"\']+)["\']',
            block,
            re.I
        ):
            value = unescape(match).strip()

            if value.startswith("//"):
                value = "https:" + value

            if value.startswith("https://") and value not in servers:
                servers.append(value)

    item["servers"] = servers


def main():
    items = []
    seen = set()

    print("Downloading homepage...")
    home = fetch(BASE + "/")

    if not home:
        raise RuntimeError("Homepage unavailable. Catalogue not replaced.")

    for link in parse(home).links:
        url = local_url(link["url"])

        if url and link["title"] and is_post(url):
            add_title(items, seen, link["title"], url)

    categories = collect_categories(home)
    print("Categories found:", len(categories))

    for index, pair in enumerate(categories, 1):
        category_url, category_name = pair
        print("Category", index, ":", category_name)

        for page in range(1, MAX_PAGES + 1):
            if page == 1:
                page_url = category_url
            else:
                page_url = (
                    category_url.rstrip("/")
                    + "/page/" + str(page) + "/"
                )

            count = collect_listing(
                page_url, category_name, items, seen
            )

            if page > 1 and count == 0:
                break

            time.sleep(DELAY)

    collect_feed(items, seen)

    if not items:
        raise RuntimeError("No titles collected. Existing catalogue preserved.")

    print("Titles collected:", len(items))
    print("Extracting title details and servers...")

    for index, item in enumerate(items[:MAX_DETAILS], 1):
        print(
            "Details", index, "/", min(len(items), MAX_DETAILS),
            "-", item["title"]
        )

        extract_details(item)
        time.sleep(DELAY)

    # Preserve entries beyond the detail-fetch limit.
    OUTPUT.write_text(
        json.dumps(items, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print("Catalogue saved:", OUTPUT)
    print("Total titles:", len(items))
    print("Titles with servers:", sum(
        1 for item in items if item["servers"]
    ))


if __name__ == "__main__":
    main()
