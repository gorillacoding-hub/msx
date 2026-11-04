import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from html import unescape
from pathlib import Path

FEED_URL = "https://cimafu.live/feed/"
OUTPUT = Path(__file__).parent / "catalogue.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 Cima4U-TV-Catalogue"
}

def clean(value):
    value = re.sub(r"<[^>]+>", " ", value or "")
    value = unescape(value)
    return re.sub(r"\s+", " ", value).strip()

def detect_type(title, description):
    text = (title + " " + description).lower()

    if any(word in text for word in [
        "anime", "demon slayer", "naruto", "one piece"
    ]):
        return "anime"

    if any(word in text for word in [
        "season", "episode", "مسلسل", "الحلقة", "الموسم"
    ]):
        return "series"

    return "movie"

request = urllib.request.Request(
    FEED_URL,
    headers=HEADERS
)

with urllib.request.urlopen(request, timeout=30) as response:
    xml_data = response.read()

root = ET.fromstring(xml_data)

items = []
seen = set()

for item in root.findall(".//item"):
    title = clean(item.findtext("title", default=""))
    link = item.findtext("link", default="").strip()
    description = clean(
        item.findtext("description", default="")
    )

    if not title or not link or link in seen:
        continue

    seen.add(link)

    items.append({
        "title": title,
        "url": link,
        "description": description[:500],
        "type": detect_type(title, description)
    })

OUTPUT.write_text(
    json.dumps(items, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print("Catalogue entries:", len(items))
print("Movies:", sum(1 for x in items if x["type"] == "movie"))
print("Series:", sum(1 for x in items if x["type"] == "series"))
print("Anime:", sum(1 for x in items if x["type"] == "anime"))
print("Saved:", OUTPUT)
