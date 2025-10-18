import re
import json
import os
import requests
import feedparser
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from langchain_community.utilities.google_serper import GoogleSerperAPIWrapper
from langchain_community.document_loaders import WebBaseLoader


def _serper() -> GoogleSerperAPIWrapper:
    # Reads SERPER_API_KEY from env.
    # k=20 fetches a larger pool; we dedupe & trim later.
    return GoogleSerperAPIWrapper(type="news", k=20, gl="us", hl="en")


# ---------- Alternative News Sources ----------
def fetch_rss_articles(query: str) -> List[Dict]:
    """Fetch articles from RSS feeds"""
    try:
        # Medical/Health RSS feeds
        rss_feeds = [
            "https://feeds.feedburner.com/medicalnewstoday",
            "https://www.healthline.com/rss",
            "https://feeds.webmd.com/rss/rss.aspx?RSSSource=RSS_PUBLIC",
            "https://www.nih.gov/news-events/news-releases/rss",
            "https://www.cancer.gov/news-events/rss",
        ]
        
        articles = []
        for feed_url in rss_feeds:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:5]:  # Limit per feed
                    # Check if article matches query
                    title_lower = entry.get("title", "").lower()
                    summary_lower = entry.get("summary", "").lower()
                    query_lower = query.lower()
                    
                    if any(term in title_lower or term in summary_lower for term in query_lower.split()):
                        articles.append({
                            "title": entry.get("title", "").strip(),
                            "url": entry.get("link", "").strip(),
                            "source": feed.feed.get("title", "RSS Feed"),
                            "published_date": datetime(*entry.get("published_parsed", (2024, 1, 1, 0, 0, 0, 0, 1, 0))[:6]).strftime("%Y-%m-%d") if entry.get("published_parsed") else None,
                        })
            except Exception as e:
                print(f"⚠️ RSS feed {feed_url} failed: {e}")
                continue
        
        return articles
    except Exception as e:
        print(f"⚠️ RSS fetching failed: {e}")
        return []


def fetch_reddit_articles(query: str) -> List[Dict]:
    """Fetch articles from Reddit (discussions about news)"""
    try:
        # Reddit doesn't require API key for basic requests
        subreddits = ["science", "medicine", "cancer", "oncology", "healthcare"]
        articles = []
        
        for subreddit in subreddits:
            try:
                url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit=10"
                headers = {"User-Agent": "NewsPortal/1.0"}
                
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                for post in data.get("data", {}).get("children", []):
                    post_data = post.get("data", {})
                    title = post_data.get("title", "")
                    
                    # Check if post matches query
                    if any(term in title.lower() for term in query.lower().split()):
                        articles.append({
                            "title": f"[Reddit] {title}",
                            "url": f"https://reddit.com{post_data.get('permalink', '')}",
                            "source": f"r/{subreddit}",
                            "published_date": datetime.fromtimestamp(post_data.get("created_utc", 0)).strftime("%Y-%m-%d"),
                        })
            except Exception as e:
                print(f"⚠️ Reddit r/{subreddit} failed: {e}")
                continue
        
        return articles
    except Exception as e:
        print(f"⚠️ Reddit fetching failed: {e}")
        return []


def fetch_multiple_sources(query: str) -> List[Dict]:
    """Fetch articles from multiple sources as fallback"""
    print(f"🔄 Trying multiple news sources for: {query}")
    
    all_articles = []
    
    # Try RSS feeds
    rss_articles = fetch_rss_articles(query)
    all_articles.extend(rss_articles)
    print(f"📰 RSS Feeds: {len(rss_articles)} articles")
    
    # Try Reddit
    reddit_articles = fetch_reddit_articles(query)
    all_articles.extend(reddit_articles)
    print(f"📰 Reddit: {len(reddit_articles)} articles")
    
    # Deduplicate
    seen = set()
    unique_articles = []
    for article in all_articles:
        key = (article["title"].lower(), article["url"].lower())
        if key not in seen and article["title"] and article["url"]:
            seen.add(key)
            unique_articles.append(article)
    
    print(f"📊 Total unique articles: {len(unique_articles)}")
    return unique_articles


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
    """Search recent news via multiple sources with fallback."""
    all_items = []
    
    # Try Serper first (if API key available)
    try:
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
                print(f"⚠️ Serper query failed: {q} - {e}")
                continue
                
        if all_items:
            print(f"✅ Serper found {len(all_items)} articles")
        else:
            print("⚠️ Serper failed, trying alternative sources...")
            all_items = fetch_multiple_sources(query)
            
    except Exception as e:
        print(f"⚠️ Serper completely failed: {e}")
        print("🔄 Using alternative news sources...")
        all_items = fetch_multiple_sources(query)
    
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
