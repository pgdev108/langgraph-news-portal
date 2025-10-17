#!/usr/bin/env python3
"""
Summary Length Test Script

This script tests that summaries meet the minimum 200-word requirement.
"""

import sys
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

def test_summary_lengths():
    """Test that all summaries meet the minimum word count."""
    print("📝 Testing Summary Length Requirements")
    print("=" * 60)
    
    try:
        from news_portal.graph import run_graph
        
        print("🚀 Running optimized graph to test summary lengths...")
        result = run_graph(news_article_count=1)  # Use minimal articles for testing
        
        print("\n📊 Summary Length Analysis:")
        print("-" * 40)
        
        total_summaries = 0
        short_summaries = 0
        valid_summaries = 0
        
        # Check summaries in each subtopic
        for subtopic, data in result.get("final", {}).get("per_subtopic", {}).items():
            articles = data.get("articles", [])
            print(f"\n📰 {subtopic}:")
            
            for i, article in enumerate(articles, 1):
                summary = article.get("summary", "")
                word_count = len(summary.split())
                total_summaries += 1
                
                if word_count >= 150:
                    valid_summaries += 1
                    status = "✅"
                else:
                    short_summaries += 1
                    status = "❌"
                
                print(f"  {status} Article {i}: {word_count} words")
                if word_count < 150:
                    print(f"    Preview: {summary[:100]}...")
        
        # Check featured articles
        featured_articles = result.get("final", {}).get("home", {}).get("best_articles", [])
        print(f"\n🏠 Featured Articles:")
        
        for i, article in enumerate(featured_articles, 1):
            summary = article.get("summary", "")
            word_count = len(summary.split())
            
            if word_count >= 150:
                status = "✅"
            else:
                status = "❌"
                short_summaries += 1
            
            print(f"  {status} Featured {i}: {word_count} words")
        
        # Summary statistics
        print("\n" + "=" * 60)
        print("📊 SUMMARY LENGTH STATISTICS")
        print("=" * 60)
        print(f"Total summaries analyzed: {total_summaries + len(featured_articles)}")
        print(f"Summaries ≥ 150 words: {valid_summaries}")
        print(f"Summaries < 150 words: {short_summaries}")
        
        if short_summaries == 0:
            print("🎉 SUCCESS: All summaries meet the 150-word minimum!")
            return True
        else:
            print(f"⚠️  {short_summaries} summaries are too short and need improvement.")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    success = test_summary_lengths()
    
    if success:
        print("\n✅ Summary length requirements are being met!")
    else:
        print("\n⚠️ Some summaries are still too short. Check the implementation.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
