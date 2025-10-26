#!/usr/bin/env python3
"""
Knowledge Graph Builder Tool Test Suite (Fixed)
===============================================

Fixed version that creates fresh tool instances for each test.
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

from news_portal.mcp_tools import KnowledgeGraphBuilderTool

async def test_knowledge_graph_building_fixed():
    """Test knowledge graph building with fresh tool instances for each test."""
    print("\n🧠 Knowledge Graph Builder Tool Test Suite (Fixed)")
    print("=" * 60)
    
    # Test 1: Cancer Care Domain
    print("\n🔬 Test 1: Cancer Care Domain")
    print("-" * 40)
    
    kg_tool_1 = KnowledgeGraphBuilderTool()  # Fresh instance
    
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
    
    result = await kg_tool_1.execute(
        domain="cancer_care_test",
        documents=cancer_documents,
        max_nodes=15,
        min_centrality=0.05
    )
    
    print(f"📊 Result: {result.get('status')}")
    if result.get('status') == 'success':
        print(f"✅ Nodes created: {result.get('nodes_count', 0)}")
        print(f"✅ Edges created: {result.get('edges_count', 0)}")
        print(f"✅ Domain: {result.get('domain')}")
        
        # Get the knowledge graph to show sample nodes
        kg = kg_tool_1.get_knowledge_graph("cancer_care_test")
        if kg and kg.nodes:
            print(f"\n📋 Sample nodes (top 5 by centrality):")
            sorted_nodes = sorted(kg.nodes.values(), key=lambda x: x.centrality_score, reverse=True)
            for i, node in enumerate(sorted_nodes[:5]):
                print(f"  {i+1}. {node.label} (centrality: {node.centrality_score:.3f})")
    else:
        print(f"❌ Error: {result.get('message')}")
    
    # Test 2: Finance Domain
    print("\n💰 Test 2: Finance Domain")
    print("-" * 40)
    
    kg_tool_2 = KnowledgeGraphBuilderTool()  # Fresh instance
    
    finance_documents = [
        "Cryptocurrency markets are highly volatile and speculative.",
        "Central banks use monetary policy to control inflation rates.",
        "Algorithmic trading uses computer programs to execute trades.",
        "Blockchain technology enables secure digital transactions.",
        "Interest rates affect borrowing costs and investment decisions.",
        "Diversification spreads risk across different asset classes."
    ]
    
    result = await kg_tool_2.execute(
        domain="finance_test",
        documents=finance_documents,
        max_nodes=10,
        min_centrality=0.1
    )
    
    print(f"📊 Result: {result.get('status')}")
    if result.get('status') == 'success':
        print(f"✅ Nodes created: {result.get('nodes_count', 0)}")
        print(f"✅ Edges created: {result.get('edges_count', 0)}")
        print(f"✅ Domain: {result.get('domain')}")
        
        # Get the knowledge graph to show sample nodes
        kg = kg_tool_2.get_knowledge_graph("finance_test")
        if kg and kg.nodes:
            print(f"\n📋 Sample nodes (top 3 by centrality):")
            sorted_nodes = sorted(kg.nodes.values(), key=lambda x: x.centrality_score, reverse=True)
            for i, node in enumerate(sorted_nodes[:3]):
                print(f"  {i+1}. {node.label} (centrality: {node.centrality_score:.3f})")
    else:
        print(f"❌ Error: {result.get('message')}")
    
    # Test 3: Technology Domain
    print("\n💻 Test 3: Technology Domain")
    print("-" * 40)
    
    kg_tool_3 = KnowledgeGraphBuilderTool()  # Fresh instance
    
    tech_documents = [
        "Artificial intelligence transforms industries through automation.",
        "Machine learning algorithms improve with more data training.",
        "Cloud computing provides scalable infrastructure services.",
        "Cybersecurity protects systems from digital threats.",
        "Data analytics drives business decision making processes.",
        "Quantum computing promises exponential processing power.",
        "Edge computing processes data closer to the source.",
        "5G networks enable faster wireless communication."
    ]
    
    result = await kg_tool_3.execute(
        domain="technology_test",
        documents=tech_documents,
        max_nodes=12,
        min_centrality=0.01
    )
    
    print(f"📊 Result: {result.get('status')}")
    if result.get('status') == 'success':
        print(f"✅ Nodes created: {result.get('nodes_count', 0)}")
        print(f"✅ Edges created: {result.get('edges_count', 0)}")
        print(f"✅ Domain: {result.get('domain')}")
        
        # Get the knowledge graph to show sample nodes
        kg = kg_tool_3.get_knowledge_graph("technology_test")
        if kg and kg.nodes:
            print(f"\n📋 Sample nodes (top 3 by centrality):")
            sorted_nodes = sorted(kg.nodes.values(), key=lambda x: x.centrality_score, reverse=True)
            for i, node in enumerate(sorted_nodes[:3]):
                print(f"  {i+1}. {node.label} (centrality: {node.centrality_score:.3f})")
    else:
        print(f"❌ Error: {result.get('message')}")
    
    # Test 4: Edge Case - Single Document
    print("\n🔍 Test 4: Edge Case - Single Document")
    print("-" * 40)
    
    kg_tool_4 = KnowledgeGraphBuilderTool()  # Fresh instance
    
    single_doc = ["Machine learning is a subset of artificial intelligence that enables computers to learn without explicit programming."]
    
    result = await kg_tool_4.execute(
        domain="single_test_unique",
        documents=single_doc,
        max_nodes=5,
        min_centrality=0.01
    )
    
    print(f"📊 Result: {result.get('status')}")
    if result.get('status') == 'success':
        print(f"✅ Nodes created: {result.get('nodes_count', 0)}")
        print(f"✅ Edges created: {result.get('edges_count', 0)}")
        print(f"✅ Domain: {result.get('domain')}")
    else:
        print(f"❌ Error: {result.get('message')}")
    
    print("\n🎉 Knowledge Graph Builder testing completed!")
    print("💡 Built knowledge graphs for domains: cancer_care_test, finance_test, technology_test, single_test_unique")

async def main():
    await test_knowledge_graph_building_fixed()

if __name__ == "__main__":
    asyncio.run(main())
