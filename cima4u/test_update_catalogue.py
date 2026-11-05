# -*- coding: utf-8 -*-
"""Regression tests for Cima4U's separate /watch/ player route."""

import unittest
from unittest.mock import patch

from cima4u import update_catalogue as scraper


class WatchPageExtractionTests(unittest.TestCase):

    def test_arabic_anime_category_is_classified(self):
        self.assertEqual(scraper.detect_type("Sample title", "انمى"), "anime")

    def test_watch_now_link_is_resolved(self):
        html = '''
            <a href="/sample-film/">Title</a>
            <a href="/sample-film/watch/">مشاهدة الآن</a>
        '''
        parser = scraper.parse_page(html)
        self.assertEqual(
            scraper.find_watch_url(
                parser,
                "https://cimafu.live/sample-film/",
            ),
            "https://cimafu.live/sample-film/watch/",
        )

    def test_canonical_watch_route_is_fallback(self):
        parser = scraper.parse_page('<html><body>No Watch Now anchor</body></html>')
        self.assertEqual(
            scraper.find_watch_url(
                parser,
                "https://cimafu.live/sample-film/",
            ),
            "https://cimafu.live/sample-film/watch/",
        )

    def test_iframes_and_labeled_server_links_are_extracted(self):
        html = '''
            <div class="servers">
              <iframe src="https://mixdrop.example/e/abc123"></iframe>
              <a href="https://cybervynx.example/embed/xyz">iframe</a>
              <a href="https://ads.example/landing">تحميل مباشر</a>
              <a href="https://download.example/file/abc">سيرفر 1</a>
              <iframe src="https://cimafu.live/sample-film/"></iframe>
            </div>
        '''
        parser = scraper.parse_page(html)
        urls = scraper.extract_server_urls(
            html,
            parser,
            "https://cimafu.live/sample-film/watch/",
        )
        self.assertIn("https://mixdrop.example/e/abc123", urls)
        self.assertIn("https://cybervynx.example/embed/xyz", urls)
        self.assertNotIn("https://ads.example/landing", urls)
        self.assertNotIn("https://download.example/file/abc", urls)
        self.assertFalse(any("cimafu.live" in url for url in urls))

    def test_real_watch_page_shape_ignores_download_servers(self):
        rows = []
        for number, host in enumerate((
            "mixdrop.ps", "mixdrop.ps", "mixdrop.ps",
            "cybervynx.com", "cybervynx.com", "1vid.xyz",
            "vidspeed.org", "hgcloud.to",
        ), start=1):
            rows.append(
                '<li>سيرفر %d <a href="https://%s/embed/%d">iframe</a></li>'
                % (number, host, number)
            )
        rows.append('<a href="https://download.example/file">سيرفر 1</a>')
        html = '<div class="servers">' + ''.join(rows) + '</div>'
        parser = scraper.parse_page(html)
        urls = scraper.extract_server_urls(
            html,
            parser,
            "https://cimafu.live/sample/watch/",
        )
        self.assertEqual(len(urls), 8)
        self.assertFalse(any("download.example" in url for url in urls))

    def test_extract_details_fetches_the_watch_page(self):
        post_html = '''
            <html>
              <head>
                <meta property="og:title" content="Sample episode" />
                <meta property="og:image" content="https://img.example/poster.jpg" />
                <meta property="og:description" content="Episode description" />
              </head>
              <body><a href="/sample-episode/watch/">مشاهدة الآن</a></body>
            </html>
        '''
        watch_html = '''
            <html><body>
              <div class="server-list">
                <iframe src="https://mixdrop.example/e/episode1"></iframe>
                <a href="https://vidspeed.example/embed/episode1">iframe</a>
              </div>
            </body></html>
        '''
        item = {
            "title": "Sample episode",
            "url": "https://cimafu.live/sample-episode/",
            "type": "series",
            "category": "مسلسلات عربية",
            "description": "",
            "poster": "",
            "watch_url": "",
            "servers": [],
        }
        with patch.object(scraper, "fetch", side_effect=[post_html, watch_html]) as fetch_mock:
            scraper.extract_details(item)

        self.assertEqual(fetch_mock.call_count, 2)
        self.assertEqual(
            item["watch_url"],
            "https://cimafu.live/sample-episode/watch/",
        )
        self.assertEqual(item["poster"], "https://img.example/poster.jpg")
        self.assertEqual(item["description"], "Episode description")
        self.assertEqual(len(item["servers"]), 2)


if __name__ == "__main__":
    unittest.main()
