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

MAX_CATEGORIES = 60
MAX_PAGES = 12
MAX_DETAILS = 300
DELAY = 0.25

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xml,application/rss+xml,*/*"
}

BLOCKED_PATHS = (
    "/category/", "/tag/", "/author/", "/page/",
    "/feed/", "/wp-", "/search/", "/privacy",
    "/contact", "/login", "/register"
)


def clean(value):
    value = unescape(value or "")
    value = re.sub(r"<[^>]*>", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def fetch(url):
    try:
        request = urllib.request.Request(url, headers=HEADERS)

        with urllib.request.urlopen(request, timeout=35) as response:
            if response.status != 200:
                return ""

            return response.read().decode(
                "utf-8",
                errors="replace"
            )

    except Exception as error:
        print("Fetch failed:", url, str(error))
        return ""


def local_url(value):
    if not value:
        return ""

    value = unescape(value.strip())

    if value.startswith("//"):
        value = "https:" + value

    value = urljoin(BASE, value)
    parsed = urlparse(value)

    if parsed.scheme not in ("http", "https"):
        return ""

    if parsed.hostname not in (
        "cimafu.live",
        "www.cimafu.live"
    ):
        return ""

    return urlunparse((
        "https",
        "cimafu.live",
        parsed.path,
        "",
        "",
        ""
    ))


def is_post(url):
    path = urlparse(url).path.lower()

    if not path or path == "/":
        return False

    return not any(
        part in path for part in BLOCKED_PATHS
    )


def is_category(url):
    path = urlparse(url).path.lower()

    return (
        "/category/" in path
        or "/genre/" in path
    )


def detect_type(title, category=""):
    value = (title + " " + category).lower()

    anime_words = (
        "anime", "انمي", "أنمي", "naruto",
        "demon slayer", "one piece", "bleach",
        "attack on titan"
    )

    series_words = (
        "مسلسل", "الحلقة", "الموسم", "حلقه",
        "episode", "season", "series", "الحلقه"
    )

    if any(word in value for word in anime_words):
        return "anime"

    if any(word in value for word in series_words):
        return "series"

    return "movie"


class PageParser(HTMLParser):

    def __init__(self):
        super().__init__(convert_charrefs=True)

        self.links = []
        self.images = []
        self.servers = []
        self.meta = {}
        self.anchors = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)

        if tag == "a":
            self.anchors.append({
                "url": attrs.get("href", ""),
                "text": []
            })

        elif tag == "img":
            src = (
                attrs.get("data-src")
                or attrs.get("data-lazy-src")
                or attrs.get("data-original")
                or attrs.get("src")
            )

            if src:
                self.images.append(src)

        elif tag == "meta":
            key = (
                attrs.get("property")
                or attrs.get("name")
                or attrs.get("itemprop")
                or ""
            ).lower()

            value = attrs.get("content", "")

            if key and value:
                self.meta[key] = value

        for key in (
            "data-server",
            "data-url",
            "data-embed",
            "data-src",
            "data-iframe"
        ):
            value = attrs.get(key)

            if value:
                self.servers.append(value)

        if tag == "iframe":
            src = attrs.get("src")

            if src:
                self.servers.append(src)

        if tag == "source":
            src = attrs.get("src")

            if src:
                self.servers.append(src)

    def handle_data(self, data):
        for anchor in self.anchors:
            anchor["text"].append(data)

    def handle_endtag(self, tag):
        if tag != "a" or not self.anchors:
            return

        anchor = self.anchors.pop()

        self.links.append({
            "url": anchor["url"],
            "title": clean(" ".join(anchor["text"]))
        })

    def close(self):
        super().close()

        while self.anchors:
            anchor = self.anchors.pop()

            self.links.append({
                "url": anchor["url"],
                "title": clean(" ".join(anchor["text"]))
            })


def parse_page(html):
    parser = PageParser()
    parser.feed(html)
    parser.close()

    return parser


def add_title(
    items,
    seen,
    title,
    url,
    category="",
    description=""
):
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
        "description": clean(description)[:1200],
        "type": detect_type(title, category),
        "category": clean(category),
        "poster": "",
        "servers": []
    })


def collect_feed(items, seen):
    print("Reading RSS feed...")

    xml_data = fetch(FEED)

    if not xml_data:
        print("RSS unavailable.")
        return

    try:
        root = ET.fromstring(xml_data)

    except ET.ParseError as error:
        print("RSS XML error:", error)
        return

    for entry in root.findall(".//item"):

        title = entry.findtext("title", "")
        link = entry.findtext("link", "")

        description = (
            entry.findtext("description", "")
            or entry.findtext(
                "{http://purl.org/rss/1.0/modules/content/}encoded",
                ""
            )
        )

        add_title(
            items,
            seen,
            title,
            link,
            description=description
        )


def collect_categories(home_html):
    parser = parse_page(home_html)
    categories = {}

    for link in parser.links:

        url = local_url(link["url"])
        name = clean(link["title"])

        if url and name and is_category(url):
            categories[url] = name

    return list(categories.items())[:MAX_CATEGORIES]


def collect_listing(
    url,
    category,
    items,
    seen
):
    html = fetch(url)

    if not html:
        return 0

    parser = parse_page(html)
    before = len(items)

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


# =========================================
# Extract REAL video servers from episode page
# =========================================

def extract_server_urls(html, parser):

    found = []

    def add(value):

        value = unescape(value or "").strip()
        value = value.replace("\\/", "/")

        if value.startswith("//"):
            value = "https:" + value

        if value.startswith("http://"):
            value = "https://" + value[7:]

        if not value.startswith("https://"):
            return

        parsed = urlparse(value)

        if not parsed.hostname:
            return

        if parsed.hostname in (
            "cimafu.live",
            "www.cimafu.live"
        ):
            return

        # Remove duplicate servers.
        if value not in found:
            found.append(value)

    # Extract servers from parsed HTML attributes.
    for value in parser.servers:
        add(value)

    # Extract servers from raw HTML.
    patterns = [

        r'data-server\s*=\s*["\']([^"\']+)',

        r'data-url\s*=\s*["\']([^"\']+)',

        r'data-embed\s*=\s*["\']([^"\']+)',

        r'data-src\s*=\s*["\']([^"\']+)',

        r'<iframe[^>]+src\s*=\s*["\']([^"\']+)',

        r'["\'](?:url|embed|src|link)["\']'
        r'\s*:\s*["\']([^"\']+)'
    ]

    for pattern in patterns:

        matches = re.findall(
            pattern,
            html,
            re.I
        )

        for match in matches:
            add(match)

    # Keep at most 12 servers per title.
    return found[:12]


# =========================================
# Extract title details and video servers
# =========================================

def extract_details(item):

    html = fetch(item["url"])

    if not html:
        return

    parser = parse_page(html)

    description = (
        parser.meta.get("og:description")
        or parser.meta.get("description")
        or parser.meta.get("twitter:description")
    )

    if description:
        item["description"] = clean(description)[:1200]

    poster = (
        parser.meta.get("og:image")
        or parser.meta.get("twitter:image")
        or parser.meta.get("twitter:image:src")
    )

    if poster:

        item["poster"] = urljoin(
            item["url"],
            poster
        )

    else:

        for image in parser.images:

            image_url = urljoin(
                item["url"],
                image
            )

            if image_url.startswith("https://"):
                item["poster"] = image_url
                break

    # THIS IS THE IMPORTANT NEW PART.
    # Extract the actual episode video servers.
    item["servers"] = extract_server_urls(
        html,
        parser
    )

    # Refine type using the article's actual title.
    page_title = parser.meta.get("og:title", "")

    if page_title:

        item["type"] = detect_type(
            clean(page_title),
            item.get("category", "")
        )


# =========================================
# Main catalogue updater
# =========================================

def main():

    items = []
    seen = set()

    print("Fetching Cima4U homepage...")

    home = fetch(BASE + "/")

    if not home:

        raise RuntimeError(
            "Cannot fetch Cima4U homepage. "
            "Existing catalogue preserved."
        )

    homepage_parser = parse_page(home)

    # Collect homepage titles.
    for link in homepage_parser.links:

        url = local_url(link["url"])

        if url and link["title"] and is_post(url):

            add_title(
                items,
                seen,
                link["title"],
                url
            )

    # Collect category pages.
    categories = collect_categories(home)

    print("Categories found:", len(categories))

    for index, (category_url, category_name) in enumerate(
        categories,
        start=1
    ):

        print(
            "Category",
            index,
            "of",
            len(categories),
            ":",
            category_name
        )

        for page in range(1, MAX_PAGES + 1):

            if page == 1:

                page_url = category_url

            else:

                page_url = (
                    category_url.rstrip("/")
                    + "/page/"
                    + str(page)
                    + "/"
                )

            count = collect_listing(
                page_url,
                category_name,
                items,
                seen
            )

            print(
                "  Page",
                page,
                "- new titles:",
                count
            )

            if page > 1 and count == 0:
                break

            time.sleep(DELAY)

    # RSS is an additional source.
    collect_feed(items, seen)

    if not items:

        raise RuntimeError(
            "No titles found. "
            "Existing catalogue preserved."
        )

    print("Total titles collected:", len(items))

    # Fetch posters, descriptions and servers.
    detail_count = min(
        len(items),
        MAX_DETAILS
    )

    print(
        "Extracting details for",
        detail_count,
        "titles..."
    )

    for index, item in enumerate(
        items[:detail_count],
        start=1
    ):

        print(
            "Details",
            index,
            "/",
            detail_count,
            ":",
            item["title"]
        )

        try:

            extract_details(item)

        except Exception as error:

            print(
                "Detail extraction failed:",
                str(error)
            )

        time.sleep(DELAY)

    # Save safely only after successful collection.
    temporary = OUTPUT.with_suffix(".tmp")

    temporary.write_text(
        json.dumps(
            items,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    temporary.replace(OUTPUT)

    print("--------------------------------")
    print("Catalogue successfully updated.")
    print("Total titles:", len(items))

    print(
        "With posters:",
        sum(
            1 for item in items
            if item["poster"]
        )
    )

    print(
        "With servers:",
        sum(
            1 for item in items
            if item["servers"]
        )
    )

    print("Saved to:", OUTPUT)


if __name__ == "__main__":
    main()
