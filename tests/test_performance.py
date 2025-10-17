#!/usr/bin/env python3
"""
Performance Comparison Script

This script compares the performance between the original and optimized versions
of the news portal processing.
"""

import time
import sys
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

def test_original_performance():
    """Test the original graph performance."""
    print("=" * 60)
    print("🐌 Testing ORIGINAL Performance")
    print("=" * 60)
    
    try:
        from news_portal.graph import run_graph
        
        start_time = time.time()
        result = run_graph(news_article_count=1)  # Use minimal articles for testing
        end_time = time.time()
        
        duration = end_time - start_time
        print(f"✅ Original processing completed in {duration:.2f} seconds")
        
        # Count articles processed
        total_articles = 0
        for subtopic_data in result.get("final", {}).get("per_subtopic", {}).values():
            total_articles += len(subtopic_data.get("articles", []))
        
        print(f"📊 Processed {total_articles} articles")
        print(f"⏱️  Average time per article: {duration/max(total_articles, 1):.2f} seconds")
        
        return duration, total_articles
        
    except Exception as e:
        print(f"❌ Original test failed: {e}")
        return None, 0

def test_optimized_performance():
    """Test the optimized graph performance."""
    print("\n" + "=" * 60)
    print("🚀 Testing OPTIMIZED Performance")
    print("=" * 60)
    
    try:
        from news_portal.graph_optimized import run_optimized_graph
        
        start_time = time.time()
        result = run_optimized_graph(news_article_count=1)  # Use minimal articles for testing
        end_time = time.time()
        
        duration = end_time - start_time
        print(f"✅ Optimized processing completed in {duration:.2f} seconds")
        
        # Count articles processed
        total_articles = 0
        for subtopic_data in result.get("final", {}).get("per_subtopic", {}).values():
            total_articles += len(subtopic_data.get("articles", []))
        
        print(f"📊 Processed {total_articles} articles")
        print(f"⏱️  Average time per article: {duration/max(total_articles, 1):.2f} seconds")
        
        return duration, total_articles
        
    except Exception as e:
        print(f"❌ Optimized test failed: {e}")
        return None, 0

def main():
    """Main performance comparison."""
    print("Performance Comparison: Original vs Optimized")
    print("This will test both versions with minimal article count for speed")
    
    # Test original
    original_time, original_articles = test_original_performance()
    
    # Test optimized
    optimized_time, optimized_articles = test_optimized_performance()
    
    # Compare results
    print("\n" + "=" * 60)
    print("📊 PERFORMANCE COMPARISON")
    print("=" * 60)
    
    if original_time and optimized_time:
        speedup = original_time / optimized_time
        time_saved = original_time - optimized_time
        
        print(f"Original Time:    {original_time:.2f} seconds")
        print(f"Optimized Time:   {optimized_time:.2f} seconds")
        print(f"Time Saved:       {time_saved:.2f} seconds")
        print(f"Speedup:          {speedup:.1f}x faster")
        print(f"Articles (Orig):  {original_articles}")
        print(f"Articles (Opt):   {optimized_articles}")
        
        if speedup > 1:
            print(f"\n🎉 SUCCESS: Optimized version is {speedup:.1f}x faster!")
        else:
            print(f"\n⚠️  Optimized version is {1/speedup:.1f}x slower")
            
        # Estimate full processing time
        estimated_original_full = original_time * 2  # Assuming 2 articles per subtopic
        estimated_optimized_full = optimized_time * 2
        
        print(f"\n📈 ESTIMATED FULL PROCESSING TIME:")
        print(f"Original (2 articles/subtopic):  {estimated_original_full:.1f} seconds ({estimated_original_full/60:.1f} minutes)")
        print(f"Optimized (2 articles/subtopic):  {estimated_optimized_full:.1f} seconds ({estimated_optimized_full/60:.1f} minutes)")
        
        if estimated_optimized_full < 60:
            print("🎯 GOAL ACHIEVED: Optimized version completes in under 1 minute!")
        else:
            print("🎯 GOAL: Still working towards under 1 minute completion")
    
    else:
        print("❌ Could not complete performance comparison")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
