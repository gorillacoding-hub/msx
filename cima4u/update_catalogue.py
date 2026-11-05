# -*- coding: utf-8 -*-
# Cima4U catalogue updater for GitHub Actions
# Compatible with the existing MSX index.html, catalogue.js and player.js

import json
import re
import time
import os
import tempfile
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET

from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

BASE = "https://cimafu.live"
OUTPUT = Path(__file__).resolve().parent / "catalogue.json"

MAX_CATEGORIES = 80
MAX_PAGES = 15
MAX_DETAILS = 500
MAX_SERVERS = 8
DELAY = 0.20
TIMEOUT = 25

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml,"
              "application/rss+xml,*/*",
    "Accept-Language": "ar,en-US,en;q=0.9",
}

BLOCKED_PATHS = (
    "/category/",
    "/tag/",
    "/author/",
    "/page/",
    "/feed/",
    "/wp-",
    "/search/",
    "/privacy",
    "/contact",
    "/login",
    "/register",
)

VIDEO_EXTENSIONS = (
    ".mp4", ".m3u8", ".mpd", ".webm"
)


def clean(value):
    value = unescape(value or "")
    value = re.sub(r"<[^>]*>", " ", value)
    value = re.sub(r"[\r\n\t]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def fetch(url):
    try:
        request = urllib.request.Request(
            url,
            headers=HEADERS
        )

        with urllib.request.urlopen(
            request,
            timeout=TIMEOUT
        ) as response:

            if response.status != 200:
                return ""

            content_type = response.headers.get(
                "Content-Type", ""
            )

            if "image/" in content_type:
                return ""

            return response.read().decode(
                "utf-8",
                errors="replace"
            )

    except (
        urllib.error.URLError,
        urllib.error.HTTPError,
        TimeoutError,
        OSError,
        ValueError
    ) as error:

        print("Fetch failed:", url, str(error))
        return ""


def normalize_url(value, base=BASE):
    if not value:
        return ""

    value = unescape(str(value).strip())
    value = value.replace("\\/", "/")
    value = value.replace("&amp;", "&")

    if value.startswith("//"):
        value = "https:" + value

    value = urljoin(base, value)

    parsed = urlparse(value)

    if parsed.scheme not in ("http", "https"):
        return ""

    if not parsed.hostname:
        return ""

    return value


def local_url(value):
    value = normalize_url(value)

    if not value:
        return ""

    parsed = urlparse(value)

    host = (parsed.hostname or "").lower()

    if host not in (
        "cimafu.live",
        "www.cimafu.live",
    ):
        return ""

    return "https://cimafu.live" + parsed.path.rstrip("/") + (
        "/" if parsed.path.endswith("/") else ""
    )


def is_post(url):
    if not url:
        return False

    path = urlparse(url).path.lower()

    if not path or path == "/":
        return False

    if any(part in path for part in BLOCKED_PATHS):
        return False

    return True


def is_category(url):
    path = urlparse(url).path.lower()

    return (
        "/category/" in path
        or "/genre/" in path
    )


def detect_type(title, category=""):
    value = (title + " " + category).lower()

    anime_words = (
        "anime",
        "انمي",
        "أنمي",
        "انمى",
        "naruto",
        "one piece",
        "bleach",
        "attack on titan",
        "demon slayer",
        "jujutsu",
        "dragon ball",
    )

    series_words = (
        "مسلسل",
        "الموسم",
        "الحلقة",
        "حلقه",
        "الحلقه",
        "episode",
        "season",
        "series",
        "مسلسلات",
    )

    if any(word in value for word in anime_words):
        return "anime"

    if any(word in value for word in series_words):
        return "series"

    return "movie"


class PageParser(HTMLParser):

    def __init__(self):
        HTMLParser.__init__(self, convert_charrefs=True)

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
                "text": [],
            })

        elif tag == "img":

            src = (
                attrs.get("data-src")
                or attrs.get("data-lazy-src")
                or attrs.get("data-original")
                or attrs.get("data-lazy")
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

        # Actual Cima4U server selectors use data-server.
        for key in (
            "data-server",
            "data-url",
            "data-embed",
            "data-src",
            "data-iframe",
            "data-link",
        ):

            value = attrs.get(key)

            if value:
                self.servers.append(value)

        if tag == "iframe":

            src = (
                attrs.get("data-src")
                or attrs.get("src")
            )

            if src:
                self.servers.append(src)

        if tag == "source":

            src = attrs.get("src")

            if src:
                self.servers.append(src)

    def handle_data(self, data):

        if self.anchors:
            self.anchors[-1]["text"].append(data)

    def handle_endtag(self, tag):

        if tag != "a" or not self.anchors:
            return

        anchor = self.anchors.pop()

        self.links.append({
            "url": anchor["url"],
            "title": clean(
                " ".join(anchor["text"])
            ),
        })

    def close(self):

        HTMLParser.close(self)

        while self.anchors:

            anchor = self.anchors.pop()

            self.links.append({
                "url": anchor["url"],
                "title": clean(
                    " ".join(anchor["text"])
                ),
            })


def parse_page(html):

    parser = PageParser()

    try:
        parser.feed(html)
        parser.close()

    except Exception as error:
        print("HTML parsing warning:", str(error))

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

    if not url or not title:
        return

    if not is_post(url):
        return

    if url in seen:
        return

    seen.add(url)

    items.append({
        "title": title,
        "url": url,
        "description": clean(description)[:1500],
        "type": detect_type(title, category),
        "category": clean(category),
        "poster": "",
        "watch_url": url.rstrip("/") + "/watch/",
        "servers": [],
    })


def collect_feed(items, seen):

    feed_urls = (
        BASE + "/feed/",
        BASE + "/?feed=rss2",
    )

    for feed_url in feed_urls:

        print("Reading RSS:", feed_url)

        xml_data = fetch(feed_url)

        if not xml_data:
            continue

        try:
            root = ET.fromstring(xml_data)

        except ET.ParseError as error:
            print("RSS XML error:", str(error))
            continue

        entries = root.findall(".//item")

        if not entries:
            entries = root.findall(
                ".//{http://www.w3.org/2005/Atom}entry"
            )

        for entry in entries:

            title = entry.findtext("title", "")

            link = entry.findtext("link", "")

            if not link:

                atom_link = entry.find(
                    "{http://www.w3.org/2005/Atom}link"
                )

                if atom_link is not None:
                    link = atom_link.attrib.get("href", "")

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
                description=description,
            )

        if entries:
            print("RSS entries:", len(entries))
            return

    print("RSS feeds unavailable; continuing with homepage.")


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
        return -1

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
                category,
            )

    return len(items) - before


# --------------------------------------------------
# Extract actual video servers from Cima4U episode HTML
# --------------------------------------------------

def find_watch_url(parser, item_url):
    """Return the actual Cima4U watch route for a title/episode page."""
    for link in parser.links:
        label = clean(link.get("title", "")).lower()
        candidate = normalize_url(link.get("url", ""), item_url)

        if not candidate:
            continue

        path = urlparse(candidate).path.lower()

        if (
            path.rstrip("/").endswith("/watch")
            or "مشاهدة الآن" in label
            or "مشاهدة الان" in label
            or "watch now" in label
        ):
            local = local_url(candidate)
            if local:
                return local.rstrip("/") + "/"

    # Cima4U uses the same /watch/ suffix where the visible link is absent.
    return item_url.rstrip("/") + "/watch/"


def extract_server_urls(html, parser=None, base_url=BASE):
    """Extract external player embeds from a Cima4U /watch/ page."""
    found = []
    seen = set()

    def add(value):
        value = normalize_url(value, base_url)
        if not value:
            return

        parsed = urlparse(value)
        host = (parsed.hostname or "").lower()

        # Internal Cima4U pages are not video servers.
        if host in ("cimafu.live", "www.cimafu.live"):
            return
        if not host or "." not in host:
            return

        path = parsed.path.lower()
        if path.endswith((
            ".jpg", ".jpeg", ".png", ".gif", ".webp",
            ".svg", ".css", ".js", ".woff", ".woff2", ".ttf",
        )):
            return

        normalized = value.rstrip("/")
        if normalized not in seen:
            seen.add(normalized)
            found.append(value)

    if parser is not None:
        # Prioritize the site's explicit iframe anchors. On the live /watch/
        # page these are the actual playback choices; separate download links
        # are labelled "سيرفر 1", "سيرفر 2", etc. and must be ignored.
        for link in parser.links:
            label = clean(link.get("title", "")).lower()
            if "iframe" in label:
                add(link.get("url", ""))

        # Keep iframe/data attributes as a fallback for theme variations,
        # after the explicit playback links have already been added.
        for value in parser.servers:
            add(value)

    patterns = (

        r'data-server\s*=\s*["\']([^"\']+)',

        r'data-url\s*=\s*["\']([^"\']+)',

        r'data-embed\s*=\s*["\']([^"\']+)',

        r'data-src\s*=\s*["\']([^"\']+)',

        r'data-iframe\s*=\s*["\']([^"\']+)',

        r'data-link\s*=\s*["\']([^"\']+)',

        r'<iframe[^>]+src\s*=\s*["\']([^"\']+)',

        r'["\'](?:url|embed|src|link)["\']'
        r'\s*:\s*["\']([^"\']+)',

        r'player\s*:\s*["\']([^"\']+)',

        r'file\s*:\s*["\']([^"\']+)',
    )

    for pattern in patterns:
        try:
            matches = re.findall(pattern, html, re.I)
        except re.error:
            continue

        for match in matches:
            add(match)

    return found[:MAX_SERVERS]


def extract_details(item):
    # First fetch the title/episode page for its poster, description,
    # and Watch Now destination.
    html = fetch(item["url"])
    if not html:
        print("No details downloaded:", item["url"])
        return

    parser = parse_page(html)

    description = (
        parser.meta.get("og:description")
        or parser.meta.get("description")
        or parser.meta.get("twitter:description")
    )
    if description:
        item["description"] = clean(description)[:1500]

    poster = (
        parser.meta.get("og:image")
        or parser.meta.get("twitter:image")
        or parser.meta.get("twitter:image:src")
    )
    if poster:
        poster_url = normalize_url(poster, item["url"])
        if poster_url:
            item["poster"] = poster_url
    else:
        for image in parser.images:
            image_url = normalize_url(image, item["url"])
            if image_url:
                item["poster"] = image_url
                break

    # Critical fix: streaming servers live on the separate /watch/ route,
    # not on the regular title/episode page.
    watch_url = find_watch_url(parser, item["url"])
    item["watch_url"] = watch_url
    watch_html = fetch(watch_url)

    if watch_html:
        watch_parser = parse_page(watch_html)
        item["servers"] = extract_server_urls(
            watch_html,
            watch_parser,
            watch_url,
        )
    else:
        item["servers"] = []

    page_title = parser.meta.get("og:title", "")
    if page_title:
        item["type"] = detect_type(
            clean(page_title),
            item.get("category", ""),
        )

    print(
        "  Watch page:", watch_url,
        "| servers:", len(item.get("servers", [])),
    )


# --------------------------------------------------
# Save JSON safely
# --------------------------------------------------

def save_catalogue(items):

    if not items:
        raise RuntimeError(
            "Catalogue is empty. Existing JSON was NOT overwritten."
        )

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    data = json.dumps(
        items,
        ensure_ascii=False,
        indent=2,
    )

    # Validate generated JSON before writing.
    json.loads(data)

    fd, temporary_path = tempfile.mkstemp(
        prefix="catalogue_",
        suffix=".tmp",
        dir=str(OUTPUT.parent),
    )

    try:

        with os.fdopen(
            fd,
            "w",
            encoding="utf-8"
        ) as temporary_file:

            temporary_file.write(data)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())

        # Replace the catalogue only after successful validation.
        os.replace(
            temporary_path,
            str(OUTPUT)
        )

    except Exception:

        try:
            os.unlink(temporary_path)

        except OSError:
            pass

        raise


# --------------------------------------------------
# Main
# --------------------------------------------------

def main():

    items = []
    seen = set()

    print("================================")
    print("Cima4U Catalogue Update Started")
    print("================================")

    print("Fetching Cima4U homepage...")

    home = fetch(BASE + "/")

    if not home:

        raise RuntimeError(
            "Cima4U homepage unavailable. "
            "Catalogue has NOT been overwritten."
        )

    homepage_parser = parse_page(home)

    # Homepage content.
    for link in homepage_parser.links:

        url = local_url(link["url"])

        if url and link["title"] and is_post(url):

            add_title(
                items,
                seen,
                link["title"],
                url,
            )

    print("Homepage titles:", len(items))

    # RSS may contain additional titles.
    collect_feed(items, seen)

    # Category pages.
    categories = collect_categories(home)

    print("Categories discovered:", len(categories))

    for category_index, (
        category_url,
        category_name
    ) in enumerate(categories, start=1):

        print(
            "Category",
            category_index,
            "/",
            len(categories),
            ":",
            category_name,
        )

        empty_pages = 0

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
                seen,
            )

            if count < 0:

                print("  Page fetch failed:", page)
                empty_pages += 1

            else:

                print(
                    "  Page",
                    page,
                    "- new titles:",
                    count,
                )

                if count == 0:
                    empty_pages += 1

                else:
                    empty_pages = 0

            # Stop when pagination no longer provides titles.
            if page > 1 and empty_pages >= 2:
                break

            time.sleep(DELAY)

    print("Total titles discovered:", len(items))

    if not items:

        raise RuntimeError(
            "No titles discovered. "
            "Catalogue has NOT been overwritten."
        )

    # Extract metadata and servers for the first MAX_DETAILS items.
    detail_count = min(
        len(items),
        MAX_DETAILS
    )

    print(
        "Extracting posters, descriptions and servers:",
        detail_count,
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
            item["title"],
        )

        try:

            extract_details(item)

        except Exception as error:

            print(
                "Details extraction error:",
                item["url"],
                str(error),
            )

        time.sleep(DELAY)

    # Preserve the established JSON schema.
    # index.html and player.js expect these fields.
    for item in items:

        item.setdefault("title", "")
        item.setdefault("url", "")
        item.setdefault("description", "")
        item.setdefault("type", "movie")
        item.setdefault("category", "")
        item.setdefault("poster", "")
        item.setdefault(
            "watch_url",
            item.get("url", "").rstrip("/") + "/watch/"
        )
        item.setdefault("servers", [])

    save_catalogue(items)

    print("================================")
    print("Catalogue generated successfully.")
    print("Total titles:", len(items))
    print(
        "Titles with posters:",
        sum(1 for item in items if item["poster"]),
    )
    print(
        "Titles with video servers:",
        sum(1 for item in items if item["servers"]),
    )
    print("Output:", OUTPUT)
    print("================================")


if __name__ == "__main__":
    main()
