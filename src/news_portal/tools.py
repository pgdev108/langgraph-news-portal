import re
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from langchain_community.utilities.google_serper import GoogleSerperAPIWrapper
from langchain_community.document_loaders import WebBaseLoader


def _serper() -> GoogleSerperAPIWrapper:
    # Reads SERPER_API_KEY from env.
    # k=20 fetches a larger pool; we dedupe & trim later.
    return GoogleSerperAPIWrapper(type="news", k=20, gl="us", hl="en")


def _iso_date_from_result(obj: dict) -> Optional[str]:
    dt = obj.get("date") or obj.get("publishedDate")
    if not dt:
        return None
    if isinstance(dt, str) and re.match(r"^\d{4}-\d{2}-\d{2}", dt):
        return dt[:10]
    try:
        m = re.match(r"(\d+)\s+(day|hour|minute)s?\s+ago", (dt or "").lower())
        if m:
            val, unit = int(m.group(1)), m.group(2)
            delta = {"minute": timedelta(minutes=val), "hour": timedelta(hours=val), "day": timedelta(days=val)}[unit]
            return (datetime.utcnow() - delta).strftime("%Y-%m-%d")
    except Exception:
        pass
    return None


def news_search(query: str, days_hint: int = 21) -> List[Dict]:
    """Search recent news via Serper and return normalized items."""
    wrapper = _serper()
    # Use more specific time-based queries and add randomization
    import random
    from datetime import datetime
    
    # Add current date and randomization to make queries more unique
    current_date = datetime.now().strftime("%Y-%m-%d")
    random_suffix = random.randint(1, 1000)
    
    # Try multiple query variations for better results
    query_variations = [
        f"{query} {current_date}",
        f"{query} latest news",
        f"{query} recent developments",
        f"{query} breaking news"
    ]
    
    all_items = []
    for q in query_variations[:2]:  # Use first 2 variations to avoid rate limits
        try:
            raw = wrapper.results(q)
            items = []
            for obj in raw.get("news", []) + raw.get("organic", []):
                items.append({
                    "title": (obj.get("title") or "").strip(),
                    "url": (obj.get("link") or obj.get("url") or "").strip(),
                    "source": (obj.get("source") or obj.get("publisher") or "").strip(),
                    "published_date": _iso_date_from_result(obj),
                })
            all_items.extend(items)
        except Exception as e:
            print(f"⚠️ Search query failed: {q} - {e}")
            continue
    
    # Deduplicate by (title,url)
    out, seen = [], set()
    for it in all_items:
        key = (it["title"].lower(), it["url"].lower())
        if it["title"] and it["url"] and key not in seen:
            seen.add(key)
            out.append(it)
    return out


def scrape_article(url: str) -> str:
    """Scrape article text; returns '' on failure."""
    try:
        loader = WebBaseLoader([url])
        docs = loader.load()
        return "\n\n".join(d.page_content for d in docs)[:20000]  # cap safety
    except Exception:
        return ""


def fetch_articles_with_content(queries: List[str], want: int, days_first=21, days_second=60) -> List[Dict]:
    """Multi-pass: fresh window then extended; returns items with 'content' field."""
    # PASS 1
    found = []
    for q in queries:
        found.extend(news_search(q, days_hint=days_first))
    # PASS 2 if needed
    if len(found) < want:
        for q in queries:
            found.extend(news_search(q, days_hint=days_second))

    # de-dupe, build a pool
    pool, seen = [], set()
    for it in found:
        key = (it["title"].lower(), it["url"].lower())
        if it["title"] and it["url"] and key not in seen:
            seen.add(key)
            pool.append(it)
        if len(pool) >= max(want * 3, want):
            break

    # scrape top pool
    out = []
    for it in pool[:max(want * 2, want)]:
        content = scrape_article(it["url"])
        it2 = dict(it)
        it2["content"] = content
        out.append(it2)
    return out
