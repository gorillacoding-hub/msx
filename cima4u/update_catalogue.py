import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from html import unescape
from pathlib import Path

FEED_URL = "https://cimafu.live/feed/"
OUTPUT = Path(__file__).parent / "catalogue.json"

request = urllib.request.Request(
    FEED_URL,
    headers={"User-Agent": "Mozilla/5.0 Cima4U-TV-Catalogue"}
)

with urllib.request.urlopen(request, timeout=30) as response:
    xml_data = response.read()

root = ET.fromstring(xml_data)
items = []

for item in root.findall(".//item"):
    title = item.findtext("title", default="")
    link = item.findtext("link", default="")
    description = item.findtext("description", default="")

    title = unescape(re.sub("<[^>]+>", "", title)).strip()
    description = unescape(
        re.sub("<[^>]+>", " ", description)
    ).strip()

    if not title or not link:
        continue

    items.append({
        "title": title,
        "url": link.strip(),
        "description": description[:500]
    })

OUTPUT.write_text(
    json.dumps(items, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print("Catalogue entries:", len(items))
print("Saved:", OUTPUT)
