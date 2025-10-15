import os
import re
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from langchain_community.utilities.google_serper import GoogleSerperAPIWrapper
from langchain_community.document_loaders import WebBaseLoader

# Serper setup (expects SERPER_API_KEY in env)
def _serper() -> GoogleSerperAPIWrapper:
    # We bias to news and ask for more results than we need
    return GoogleSerperAPIWrapper(
        type="news",  # use news vertical
        k=20,         # request many; we'll dedupe/trim
        gl="us",
        hl="en",
    )

def _iso_date_from_result(obj: dict) -> Optional[str]:
    # Serper news often has 'date' like '2 days ago' or an ISO
    dt = obj.get("date") or obj.get("publishedDate")
    if not dt:
        return None
    # Try ISO first
    if isinstance(dt, str) and re.match(r"^\d{4}-\d{2}-\d{2}", dt):
        return dt[:10]
    # Handle 'X days ago'
    try:
        m = re.match(r"(\d+)\s+(day|hour|minute)s?\s+ago", dt.lower())
        if m:
            val, unit = int(m.group(1)), m.group(2)
            delta = {"minute": timedelta(minutes=val), "hour": timedelta(hours=val), "day": timedelta(days=val)}[unit]
            return (datetime.utcnow() - delta).strftime("%Y-%m-%d")
    except Exception:
        pass
    return None

def news_search(query: str, days: int = 21) -> List[Dict]:
    """Search recent news via Serper and return normalized items."""
    wrapper = _serper()
    # GoogleSerperAPIWrapper uses q param only; include recency hint in query text
    q = f"{query} newer than last {days} days"
    raw = wrapper.results(q)
    items = []
    # LangChain returns dict: {'news': [ { 'title','link','snippet','date','source'} ], ...}
    for obj in raw.get("news", []) + raw.get("organic", []):
        items.append({
            "title": (obj.get("title") or "").strip(),
            "url": (obj.get("link") or obj.get("url") or "").strip(),
            "source": (obj.get("source") or obj.get("publisher") or "").strip(),
            "published_date": _iso_date_from_result(obj),
        })
    # Deduplicate by (title,url)
    out, seen = [], set()
    for it in items:
        key = (it["title"].lower(), it["url"].lower())
        if it["title"] and it["url"] and key not in seen:
            seen.add(key)
            out.append(it)
    return out

def scrape_article(url: str) -> str:
    """Scrape article text via WebBaseLoader."""
    try:
        loader = WebBaseLoader([url])
        docs = loader.load()
        text = "\n\n".join([d.page_content for d in docs])[:15000]  # cap
        return text
    except Exception:
        return ""

def fetch_articles_with_content(queries: List[str], want: int, days_first=21, days_second=60) -> List[Dict]:
    """Multi-pass: fresh window then extended; returns items with 'content' field."""
    # PASS 1
    found = []
    for q in queries:
        found.extend(news_search(q, days=days_first))
    # PASS 2 if needed
    if len(found) < want:
        for q in queries:
            found.extend(news_search(q, days=days_second))
    # De-dupe and trim
    unique, seen = [], set()
    for it in found:
        key = (it["title"].lower(), it["url"].lower())
        if it["title"] and it["url"] and key not in seen:
            seen.add(key)
            unique.append(it)
        if len(unique) >= max(want * 3, want):  # keep a pool
            break
    # Scrape top-N pool
    out = []
    for it in unique[: max(want * 2, want) ]:
        content = scrape_article(it["url"])
        it2 = dict(it)
        it2["content"] = content
        out.append(it2)
    return out
