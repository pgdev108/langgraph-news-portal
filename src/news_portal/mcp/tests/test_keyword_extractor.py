#!/usr/bin/env python3
"""
Keyword Extractor Tool Test Suite
=================================

Comprehensive tests for the KeywordExtractorTool.
"""

import asyncio
import sys
import os
from pathlib import Path

# Load environment variables
try:
    from dotenv import load_dotenv
    project_root = Path(__file__).parent.parent.parent.parent.parent
    env_file = project_root / '.env'
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✅ Loaded environment variables from: {env_file}")
    else:
        print(f"⚠️  .env file not found at: {env_file}")
except ImportError:
    print("⚠️  python-dotenv not installed")

# Check API key
if not os.getenv("OPENAI_API_KEY"):
    print("❌ OPENAI_API_KEY not found!")
    sys.exit(1)
else:
    print("✅ OPENAI_API_KEY found")

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from news_portal.mcp import KeywordExtractorTool, KnowledgeGraphBuilderTool

async def test_keyword_extraction():
    """Test keyword extraction with various scenarios."""
    print("\n🔍 Keyword Extractor Tool Test Suite")
    print("=" * 60)
    
    kw_tool = KeywordExtractorTool()
    kg_tool = KnowledgeGraphBuilderTool()
    
    # Test 1: Build knowledge graph first, then extract keywords
    print("\n🧠 Test 1: With Knowledge Graph")
    print("-" * 40)
    
    # Build knowledge graph for cancer care
    cancer_documents = [
        "Precision oncology uses genetic testing to personalize cancer treatment.",
        "Immunotherapy helps the immune system fight cancer cells effectively.",
        "Targeted therapies attack specific molecular pathways in cancer cells.",
        "Biomarkers predict treatment response and disease progression.",
        "Early detection improves cancer survival rates significantly.",
        "Liquid biopsies detect cancer DNA in blood samples non-invasively.",
        "CAR-T cell therapy engineers immune cells to target cancer.",
        "Checkpoint inhibitors remove brakes on immune system responses."
    ]
    
    print("🔧 Building knowledge graph for cancer_care domain...")
    kg_result = await kg_tool.execute(
        domain="cancer_care",
        documents=cancer_documents,
        max_nodes=15,
        min_centrality=0.05
    )
    
    if kg_result.get('status') == 'success':
        print(f"✅ Knowledge graph built: {kg_result.get('nodes_count')} nodes, {kg_result.get('edges_count')} edges")
        
        # Set the knowledge graph for the keyword extractor
        kg = kg_tool.get_knowledge_graph("cancer_care")
        kw_tool.set_knowledge_graphs({"cancer_care": kg})
        
        # Test keyword extraction
        test_text = "Precision oncology and immunotherapy are revolutionizing cancer treatment through personalized approaches that target specific molecular pathways."
        
        print(f"\n📝 Extracting keywords from: {test_text}")
        
        result = await kw_tool.execute(
            text=test_text,
            domain="cancer_care",
            max_keywords=5,
            min_centrality=0.01
        )
        
        print(f"📊 Result: {result.get('status')}")
        if result.get('status') == 'success':
            keywords = result.get('keywords', [])
            print(f"✅ Extracted {len(keywords)} keywords:")
            for i, kw in enumerate(keywords, 1):
                print(f"  {i}. {kw.get('keyword')} (centrality: {kw.get('centrality_score', 0):.3f})")
        else:
            print(f"❌ Error: {result.get('message')}")
    else:
        print(f"❌ Failed to build knowledge graph: {kg_result.get('message')}")
    
    # Test 2: Without knowledge graph (should fail)
    print("\n❌ Test 2: Without Knowledge Graph (Expected Failure)")
    print("-" * 40)
    
    kw_tool_no_kg = KeywordExtractorTool()  # Fresh instance without KG
    
    test_text = "Machine learning algorithms are transforming healthcare through predictive analytics."
    
    print(f"📝 Extracting keywords from: {test_text}")
    
    result = await kw_tool_no_kg.execute(
        text=test_text,
        domain="healthcare",
        max_keywords=3,
        min_centrality=0.05
    )
    
    print(f"📊 Result: {result.get('status')}")
    if result.get('status') == 'error':
        print(f"✅ Expected failure: {result.get('message')}")
    else:
        print(f"❌ Unexpected success: {result.get('message')}")
    
    # Test 3: Different centrality thresholds
    print("\n📊 Test 3: Different Centrality Thresholds")
    print("-" * 40)
    
    test_text = "Precision oncology uses genetic testing, immunotherapy, and targeted therapies to treat cancer patients."
    
    thresholds = [0.05, 0.1, 0.15, 0.2]
    
    for threshold in thresholds:
        print(f"\n🔍 Testing threshold: {threshold}")
        
        # Debug: Check if knowledge graph is still available
        try:
            # Try to access the knowledge graph directly
            if hasattr(kw_tool, 'knowledge_graphs') and "cancer_care" in kw_tool.knowledge_graphs:
                kg = kw_tool.knowledge_graphs["cancer_care"]
                print(f"  📊 Knowledge graph available: {len(kg.nodes)} nodes")
                # Show top nodes
                sorted_nodes = sorted(kg.nodes.values(), key=lambda x: x.centrality_score, reverse=True)
                print(f"  📊 Top nodes: {[f'{n.label}({n.centrality_score:.3f})' for n in sorted_nodes[:3]]}")
            else:
                print(f"  ❌ Knowledge graph NOT available!")
                # Re-set the knowledge graph using kg_tool
                kg = kg_tool.get_knowledge_graph("cancer_care")
                if kg:
                    kw_tool.set_knowledge_graphs({"cancer_care": kg})
                    print(f"  🔧 Re-set knowledge graph: {len(kg.nodes)} nodes")
        except Exception as e:
            print(f"  ❌ Error checking knowledge graph: {e}")
            # Re-set the knowledge graph using kg_tool
            kg = kg_tool.get_knowledge_graph("cancer_care")
            if kg:
                kw_tool.set_knowledge_graphs({"cancer_care": kg})
                print(f"  🔧 Re-set knowledge graph: {len(kg.nodes)} nodes")
        
        result = await kw_tool.execute(
            text=test_text,
            domain="cancer_care",
            max_keywords=10,
            min_centrality=threshold
        )
        
        if result.get('status') == 'success':
            keywords = result.get('keywords', [])
            print(f"✅ Threshold {threshold}: {len(keywords)} keywords")
            if keywords:
                print(f"   Top keyword: {keywords[0].get('keyword')} ({keywords[0].get('centrality_score', 0):.3f})")
        else:
            print(f"❌ Threshold {threshold}: {result.get('message')}")
    
    # Test 4: Different domains
    print("\n🌐 Test 4: Different Domains")
    print("-" * 40)
    
    # Build knowledge graph for finance
    finance_documents = [
        "Cryptocurrency markets are highly volatile and speculative.",
        "Central banks use monetary policy to control inflation rates.",
        "Algorithmic trading uses computer programs to execute trades.",
        "Risk management protects portfolios from market downturns.",
        "Blockchain technology enables secure digital transactions."
    ]
    
    print("🔧 Building knowledge graph for finance domain...")
    kg_result = await kg_tool.execute(
        domain="finance",
        documents=finance_documents,
        max_nodes=10,
        min_centrality=0.05
    )
    
    if kg_result.get('status') == 'success':
        print(f"✅ Knowledge graph built: {kg_result.get('nodes_count')} nodes, {kg_result.get('edges_count')} edges")
        
        # Set the knowledge graph for the keyword extractor
        kg = kg_tool.get_knowledge_graph("finance")
        kw_tool.set_knowledge_graphs({"finance": kg})
        
        # Test keyword extraction
        finance_text = "Cryptocurrency trading and blockchain technology are revolutionizing financial markets through decentralized systems."
        
        print(f"\n📝 Extracting keywords from finance text: {finance_text}")
        
        result = await kw_tool.execute(
            text=finance_text,
            domain="finance",
            max_keywords=3,
            min_centrality=0.05
        )
        
        print(f"📊 Result: {result.get('status')}")
        if result.get('status') == 'success':
            keywords = result.get('keywords', [])
            print(f"✅ Extracted {len(keywords)} keywords:")
            for i, kw in enumerate(keywords, 1):
                print(f"  {i}. {kw.get('keyword')} (centrality: {kw.get('centrality_score', 0):.3f})")
        else:
            print(f"❌ Error: {result.get('message')}")
    else:
        print(f"❌ Failed to build finance knowledge graph: {kg_result.get('message')}")
    
    # Test 5: Edge cases
    print("\n🔍 Test 5: Edge Cases")
    print("-" * 40)
    
    # Empty text
    print("\n📝 Testing empty text...")
    result = await kw_tool.execute(
        text="",
        domain="cancer_care",
        max_keywords=5,
        min_centrality=0.05
    )
    print(f"📊 Empty text result: {result.get('status')}")
    
    # Very short text
    print("\n📝 Testing very short text...")
    result = await kw_tool.execute(
        text="AI",
        domain="cancer_care",
        max_keywords=5,
        min_centrality=0.05
    )
    print(f"📊 Short text result: {result.get('status')}")
    
    # High centrality threshold
    print("\n📝 Testing high centrality threshold...")
    result = await kw_tool.execute(
        text="Precision oncology uses genetic testing to personalize cancer treatment.",
        domain="cancer_care",
        max_keywords=5,
        min_centrality=0.5  # Very high threshold
    )
    print(f"📊 High threshold result: {result.get('status')}")
    if result.get('status') == 'success':
        keywords = result.get('keywords', [])
        print(f"✅ High threshold: {len(keywords)} keywords")
    
    print(f"\n🎉 Keyword Extractor testing completed!")
    print(f"💡 Tested scenarios: with KG, without KG, different thresholds, different domains, edge cases")

async def main():
    await test_keyword_extraction()

if __name__ == "__main__":
    asyncio.run(main())
