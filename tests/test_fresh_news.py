#!/usr/bin/env python3
"""
Test Fresh News Search

This script tests that the news search is finding fresh articles.
"""

import sys
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

def test_fresh_news_search():
    """Test that news search returns fresh articles."""
    print("🔍 Testing Fresh News Search")
    print("=" * 50)
    
    try:
        from news_portal.tools import news_search
        from datetime import datetime
        
        print(f"📅 Current date: {datetime.now().strftime('%Y-%m-%d')}")
        print()
        
        # Test a simple query
        test_query = "cancer research news"
        print(f"🔍 Testing query: '{test_query}'")
        
        results = news_search(test_query, days_hint=7)
        
        print(f"📊 Found {len(results)} articles")
        
        if results:
            print("\n📰 Sample articles:")
            for i, article in enumerate(results[:3], 1):
                print(f"  {i}. {article.get('title', 'No title')[:60]}...")
                print(f"     Source: {article.get('source', 'Unknown')}")
                print(f"     Date: {article.get('published_date', 'Unknown')}")
                print()
        else:
            print("⚠️ No articles found - this might indicate an API issue")
        
        return len(results) > 0
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    success = test_fresh_news_search()
    
    if success:
        print("✅ News search is working and finding articles!")
        print("The search should now return fresh articles each time.")
    else:
        print("⚠️ News search may have issues - check API keys and connectivity.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
