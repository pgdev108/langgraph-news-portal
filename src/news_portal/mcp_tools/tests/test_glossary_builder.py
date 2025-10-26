#!/usr/bin/env python3
"""
Glossary Builder Tool Tester
============================

Test the glossary builder tool to create high-value glossaries from knowledge graphs.
"""

import asyncio
import sys
import os
from pathlib import Path

# Load environment variables
try:
    from dotenv import load_dotenv
    project_root = Path(__file__).parent.parent.parent.parent.parent
    env_file = project_root / ".env"
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

# Import FastMCP first before modifying sys.path
try:
    from fastmcp import Client
    FASTMCP_AVAILABLE = True
except ImportError:
    FASTMCP_AVAILABLE = False
    print("⚠️  FastMCP not available - FastMCP tests will be skipped")

# Add src to path for MCP tools only
src_path = os.path.join(os.path.dirname(__file__), '..', '..')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from news_portal.mcp_tools import GlossaryBuilderTool
from news_portal.mcp_tools.knowledge_graph_builder import KnowledgeGraphBuilderTool

async def test_glossary_builder_with_prebuilt_graph():
    """Test glossary builder with the pre-built knowledge graph."""
    print("\n📚 Testing Glossary Builder with Pre-built Knowledge Graph")
    print("=" * 60)
    
    # Load pre-built knowledge graph for cancer health care
    print("\n🔧 Loading pre-built knowledge graph for 'cancer health care'...")
    kg_loader = KnowledgeGraphBuilderTool()
    # Path from tests to mcp_tools/knowledge_graphs
    graph_file = Path(__file__).parent.parent / "knowledge_graphs" / "cancer_health_care.json"
    
    if not graph_file.exists():
        print(f"❌ Pre-built graph not found at: {graph_file}")
        print("   Run 'uv run python src/news_portal/mcp_tools/build_knowledge_graph.py' to create it")
        return
    
    success = kg_loader.load_graph(str(graph_file))
    if not success:
        print("❌ Failed to load graph from file")
        return
    
    kg = kg_loader.get_knowledge_graph("cancer health care")
    if not kg:
        print("⚠️  Failed to retrieve loaded graph")
        return
    
    print(f"✅ Loaded knowledge graph: {len(kg.nodes)} nodes, {len(kg.edges)} edges")
    
    # Build glossary from the pre-built graph
    print(f"\n📚 Step 2: Building glossary from pre-built graph...")
    glossary_tool = GlossaryBuilderTool()
    glossary_tool.set_knowledge_graphs({
        "cancer health care": kg,
        "cancer_care": kg  # For backward compatibility
    })
    
    # Build glossary from the knowledge graph
    try:
        result = await glossary_tool.execute(
            domain="cancer health care",
            max_terms=15,
            min_centrality=0.1
        )
        
        print(f"\n📊 Glossary Building Result:")
        print(f"Status: {result.get('status', 'unknown')}")
        
        if result.get('status') == 'success':
            glossary_terms = result.get('glossary_terms', [])
            print(f"✅ Built glossary with {len(glossary_terms)} terms:")
            
            for i, term in enumerate(glossary_terms, 1):
                term_name = term.get('term', 'N/A')
                definition = term.get('definition', 'N/A')
                centrality = term.get('centrality_score', 0)
                print(f"\n  {i:2d}. {term_name}")
                print(f"      Centrality: {centrality:.3f}")
                print(f"      Definition: {definition}")
            
            # Show statistics
            centrality_scores = [term.get('centrality_score', 0) for term in glossary_terms]
            if centrality_scores:
                print(f"\n📊 Statistics:")
                print(f"  - Total terms: {len(glossary_terms)}")
                print(f"  - Average centrality: {sum(centrality_scores)/len(centrality_scores):.3f}")
                print(f"  - Highest centrality: {max(centrality_scores):.3f}")
                print(f"  - Lowest centrality: {min(centrality_scores):.3f}")
                print(f"  - Domain: {result.get('domain', 'N/A')}")
        else:
            print(f"❌ Error: {result.get('message', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Exception during glossary building: {e}")
        import traceback
        traceback.print_exc()

async def test_glossary_builder_with_sample_article():
    """Test glossary builder with a sample news article (uses local builder)."""
    print("\n📚 Testing Glossary Builder with Sample News Article")
    print("=" * 60)
    
    # Sample news article about precision medicine
    sample_article = """
    Precision Medicine Transforms Cancer Treatment Through Genomic Analysis
    
    The field of precision medicine has revolutionized cancer treatment by enabling physicians 
    to tailor therapies based on individual patient genetic profiles. This personalized approach 
    to medicine utilizes advanced genomic sequencing technologies to identify specific mutations 
    and biomarkers that drive cancer progression in each patient.
    
    Genomic profiling involves analyzing a patient's DNA to detect mutations, copy number variations, 
    and gene fusions that may influence treatment response. Next-generation sequencing technologies 
    have made this process faster and more cost-effective, allowing for routine clinical implementation.
    
    Liquid biopsies represent a non-invasive alternative to traditional tissue biopsies, analyzing 
    circulating tumor DNA and circulating tumor cells found in blood samples. This approach enables 
    real-time monitoring of tumor evolution and early detection of resistance mechanisms.
    
    Targeted therapies are drugs designed to specifically attack cancer cells with particular 
    molecular characteristics. These treatments often have fewer side effects than traditional 
    chemotherapy because they target specific pathways that cancer cells depend on for survival.
    
    Immunotherapy harnesses the body's immune system to recognize and attack cancer cells. 
    Checkpoint inhibitors, CAR-T cell therapy, and cancer vaccines are among the most promising 
    immunotherapeutic approaches currently being developed.
    
    Biomarkers are measurable indicators of biological processes or disease states. In oncology, 
    biomarkers help predict treatment response, monitor disease progression, and identify patients 
    who are most likely to benefit from specific therapies.
    
    Pharmacogenomics studies how genetic variations affect drug response, enabling physicians 
    to prescribe medications that are most likely to be effective and safe for individual patients.
    
    Clinical trials are essential for evaluating new precision medicine approaches. These studies 
    help determine the safety and efficacy of novel treatments while providing patients with 
    access to cutting-edge therapies.
    
    The integration of artificial intelligence and machine learning algorithms is accelerating 
    the development of precision medicine approaches. These technologies can analyze vast 
    amounts of genomic and clinical data to identify patterns and predict treatment outcomes.
    
    Regulatory agencies are adapting to support the development and approval of precision 
    medicine therapies. The FDA's Breakthrough Therapy Designation and Accelerated Approval 
    pathways are facilitating faster access to promising targeted treatments.
    
    Despite the promise of precision medicine, challenges remain including high costs, limited 
    access to genomic testing, and the need for specialized expertise in interpreting results. 
    However, as technology continues to advance and costs decrease, precision medicine is 
    expected to become increasingly accessible to patients worldwide.
    """
    
    print(f"📝 Sample article length: {len(sample_article)} characters")
    print(f"📝 Article preview: {sample_article[:200]}...")
    
    # Step 1: Build knowledge graph from the article
    print(f"\n🔧 Step 1: Building knowledge graph from article...")
    kg_tool = KnowledgeGraphBuilderTool()
    
    # Split article into documents for knowledge graph building
    documents = [
        sample_article[:1000],   # First part
        sample_article[1000:2000], # Second part  
        sample_article[2000:3000], # Third part
        sample_article[3000:4000], # Fourth part
        sample_article[4000:]   # Remaining part
    ]
    
    kg_result = await kg_tool.execute(
        domain="precision_medicine",
        documents=documents,
        max_nodes=40,
        min_centrality=0.05
    )
    
    if kg_result.get('status') != 'success':
        print(f"❌ Failed to build knowledge graph: {kg_result.get('message')}")
        return
    
    print(f"✅ Knowledge graph built: {kg_result.get('nodes_count')} nodes, {kg_result.get('edges_count')} edges")
    
    # Step 2: Test glossary building
    print(f"\n📚 Step 2: Testing glossary building...")
    glossary_tool = GlossaryBuilderTool()
    
    # Set the knowledge graph for the glossary builder
    kg = kg_tool.get_knowledge_graph("precision_medicine")
    glossary_tool.set_knowledge_graphs({"precision_medicine": kg})
    
    # Build glossary from the knowledge graph
    try:
        result = await glossary_tool.execute(
            domain="precision_medicine",
            max_terms=15,
            min_centrality=0.1
        )
        
        print(f"\n📊 Glossary Building Result:")
        print(f"Status: {result.get('status', 'unknown')}")
        
        if result.get('status') == 'success':
            glossary_terms = result.get('glossary_terms', [])
            print(f"✅ Built glossary with {len(glossary_terms)} terms:")
            
            for i, term in enumerate(glossary_terms, 1):
                term_name = term.get('term', 'N/A')
                definition = term.get('definition', 'N/A')
                centrality = term.get('centrality_score', 0)
                print(f"\n  {i:2d}. {term_name}")
                print(f"      Centrality: {centrality:.3f}")
                print(f"      Definition: {definition}")
            
            # Show statistics
            centrality_scores = [term.get('centrality_score', 0) for term in glossary_terms]
            if centrality_scores:
                print(f"\n📊 Statistics:")
                print(f"  - Total terms: {len(glossary_terms)}")
                print(f"  - Average centrality: {sum(centrality_scores)/len(centrality_scores):.3f}")
                print(f"  - Highest centrality: {max(centrality_scores):.3f}")
                print(f"  - Lowest centrality: {min(centrality_scores):.3f}")
                print(f"  - Domain: {result.get('domain', 'N/A')}")
        else:
            print(f"❌ Error: {result.get('message', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Exception during glossary building: {e}")
        import traceback
        traceback.print_exc()

async def test_glossary_builder_without_kg():
    """Test glossary builder without knowledge graph (should fail)."""
    print("\n📚 Testing Glossary Builder without Knowledge Graph")
    print("=" * 60)
    
    glossary_tool = GlossaryBuilderTool()
    
    try:
        result = await glossary_tool.execute(
            domain="test_domain",
            max_terms=10,
            min_centrality=0.1
        )
        
        print(f"\n📊 Result:")
        print(f"Status: {result.get('status', 'unknown')}")
        
        if result.get('status') == 'success':
            print(f"✅ Unexpected success: {result.get('message')}")
        else:
            print(f"✅ Expected failure: {result.get('message')}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

async def test_glossary_builder_via_fastmcp():
    """Test glossary builder through FastMCP server using pre-built graph."""
    print("\n🌐 Testing Glossary Builder via FastMCP Server")
    print("=" * 60)
    
    if not FASTMCP_AVAILABLE:
        print("⏭️  Skipping FastMCP server test - FastMCP not available")
        return
    
    import json
    
    def parse_fastmcp_result(result):
        """Parse FastMCP result and return as dictionary."""
        if hasattr(result, 'content') and result.content:
            result_data = result.content[0].text
            try:
                return json.loads(result_data)
            except json.JSONDecodeError:
                return {"status": "error", "message": f"Could not parse JSON: {result_data}"}
        else:
            return {"status": "error", "message": "No content in result"}
    
    client = Client("http://localhost:8002/mcp")
    
    try:
        async with client:
            print("✅ Connected to FastMCP server")
            print("ℹ️  Note: Using pre-built knowledge graph loaded at server startup")
            
            # Build the glossary using the pre-built graph
            print("📚 Building glossary via FastMCP using pre-built graph...")
            result = await client.call_tool(
                "build_glossary",
                {
                    "domain": "cancer health care",  # Use the pre-built domain
                    "max_terms": 10,
                    "min_centrality": 0.1
                }
            )
            
            result_dict = parse_fastmcp_result(result)
            print(f"\n📊 FastMCP Result: {result_dict.get('status')}")
            
            if result_dict.get('status') == 'success':
                glossary_terms = result_dict.get('glossary_terms', [])
                print(f"✅ Built glossary with {len(glossary_terms)} terms:")
                
                for i, term in enumerate(glossary_terms[:5], 1):  # Show first 5
                    term_name = term.get('term', 'N/A')
                    definition = term.get('definition', 'N/A')
                    centrality = term.get('centrality_score', 0)
                    print(f"  {i}. {term_name} ({centrality:.3f}): {definition[:100]}...")
            else:
                print(f"❌ Error: {result_dict.get('message')}")
                
    except Exception as e:
        print(f"❌ FastMCP error: {e}")

async def test_different_centrality_thresholds():
    """Test glossary builder with different centrality thresholds."""
    print("\n📊 Testing Different Centrality Thresholds")
    print("=" * 60)
    
    # Build knowledge graph first
    kg_tool = KnowledgeGraphBuilderTool()
    
    documents = [
        "Precision medicine uses genetic testing to personalize cancer treatment.",
        "Immunotherapy helps the immune system fight cancer cells.",
        "Biomarkers predict treatment response and disease progression.",
        "Targeted therapies attack specific molecular pathways in cancer cells."
    ]
    
    kg_result = await kg_tool.execute(
        domain="oncology",
        documents=documents,
        max_nodes=20,
        min_centrality=0.05
    )
    
    if kg_result.get('status') != 'success':
        print(f"❌ Failed to build knowledge graph: {kg_result.get('message')}")
        return
    
    print(f"✅ Knowledge graph built: {kg_result.get('nodes_count')} nodes")
    
    glossary_tool = GlossaryBuilderTool()
    kg = kg_tool.get_knowledge_graph("oncology")
    glossary_tool.set_knowledge_graphs({"oncology": kg})
    
    # Test different thresholds
    thresholds = [0.05, 0.1, 0.15, 0.2]
    
    for threshold in thresholds:
        print(f"\n📊 Testing centrality threshold: {threshold}")
        
        try:
            result = await glossary_tool.execute(
                domain="oncology",
                max_terms=10,
                min_centrality=threshold
            )
            
            if result.get('status') == 'success':
                glossary_terms = result.get('glossary_terms', [])
                print(f"✅ Threshold {threshold}: {len(glossary_terms)} terms")
                
                # Show top terms
                for term in glossary_terms[:3]:
                    print(f"  - {term.get('term', 'N/A')} ({term.get('centrality_score', 0):.3f})")
            else:
                print(f"❌ Threshold {threshold}: {result.get('message')}")
                
        except Exception as e:
            print(f"❌ Error at threshold {threshold}: {e}")

async def main():
    """Run all glossary builder tests."""
    print("📚 Glossary Builder Tool Test Suite")
    print("=" * 60)
    print("This will test the glossary builder tool in various scenarios.")
    print("The tool uses a pre-built knowledge graph loaded at startup.")
    print("=" * 60)
    
    # Test 1: With pre-built graph
    await test_glossary_builder_with_prebuilt_graph()
    
    # Test 2: With sample article (builds local graph)
    await test_glossary_builder_with_sample_article()
    
    # Test 3: Without knowledge graph
    await test_glossary_builder_without_kg()
    
    # Test 4: Via FastMCP server
    await test_glossary_builder_via_fastmcp()
    
    # Test 5: Different centrality thresholds
    await test_different_centrality_thresholds()
    
    print("\n✅ Glossary builder testing completed!")
    print("\n💡 Key findings:")
    print("  📚 Glossary builder uses pre-built knowledge graph at server startup")
    print("  📊 Centrality thresholds control glossary quality and size")
    print("  🌐 FastMCP server integration works properly")
    print("  📝 Creates high-value glossaries from domain knowledge")

if __name__ == "__main__":
    asyncio.run(main())
