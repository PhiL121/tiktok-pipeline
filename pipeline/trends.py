"""Fetch today's trending searches from the public Google Trends RSS feed."""
import xml.etree.ElementTree as ET

import requests

from . import config

NS = {"ht": "https://trends.google.com/trending/rss"}


def fetch_trends(limit: int = 25) -> list[dict]:
    url = f"https://trends.google.com/trending/rss?geo={config.TRENDS_GEO}"
    resp = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    root = ET.fromstring(resp.content)
    trends = []
    for item in root.iter("item"):
        news = [
            {
                "title": (n.findtext("ht:news_item_title", "", NS) or "").strip(),
                "url": (n.findtext("ht:news_item_url", "", NS) or "").strip(),
                "source": (n.findtext("ht:news_item_source", "", NS) or "").strip(),
            }
            for n in item.findall("ht:news_item", NS)
        ]
        trends.append(
            {
                "keyword": (item.findtext("title") or "").strip(),
                "traffic": (item.findtext("ht:approx_traffic", "", NS) or "").strip(),
                "news": news,
            }
        )
        if len(trends) >= limit:
            break
    return trends
