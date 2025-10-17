#!/usr/bin/env python3
"""
Test script to verify featured articles fix

This script tests that we get 5 featured articles (one from each subtopic)
instead of being limited by news_article_count.
"""

import sys
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

def test_featured_articles():
    """Test that we get 5 featured articles."""
    print("🧪 Testing Featured Articles Fix")
    print("=" * 50)
    
    try:
        from news_portal.graph import run_graph
        
        print("🚀 Running optimized graph with news_article_count=1...")
        result = run_graph(news_article_count=1)  # Use minimal articles per subtopic
        
        # Check featured articles
        featured_articles = result.get("final", {}).get("home", {}).get("best_articles", [])
        
        print(f"\n📊 Results:")
        print(f"Featured articles count: {len(featured_articles)}")
        print(f"Expected: 5 (one from each subtopic)")
        
        if len(featured_articles) == 5:
            print("✅ SUCCESS: Got 5 featured articles as expected!")
            
            print(f"\n📰 Featured Articles:")
            for i, article in enumerate(featured_articles, 1):
                print(f"{i}. {article.get('subtopic', 'Unknown')}: {article.get('title', 'No title')[:60]}...")
            
            return True
        else:
            print(f"❌ FAILED: Expected 5 featured articles, got {len(featured_articles)}")
            
            if featured_articles:
                print(f"\n📰 Featured Articles found:")
                for i, article in enumerate(featured_articles, 1):
                    print(f"{i}. {article.get('subtopic', 'Unknown')}: {article.get('title', 'No title')[:60]}...")
            
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    success = test_featured_articles()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 FEATURED ARTICLES FIX VERIFIED!")
        print("You should now see 5 featured articles on the home page.")
    else:
        print("⚠️ Featured articles fix needs more investigation.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
