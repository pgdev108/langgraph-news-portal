#!/usr/bin/env python3
"""
FastMCP Client for Testing Cover Image Generation
===============================================

Simple client to test the FastMCP server for cover image generation.
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

from fastmcp import Client
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

async def test_cover_image_generation():
    """Test the cover image generation tool."""
    print("\n🎯 Testing Cover Image Generation with FastMCP")
    print("=" * 60)
    
    # Connect to the FastMCP server
    client = Client("http://localhost:8002/mcp")
    
    try:
        async with client:
            print("✅ Connected to FastMCP server")
            
            # First, build a knowledge graph for cancer_care domain
            print("\n🔧 Step 1: Building knowledge graph for cancer_care domain...")
            kg_documents = [
                "Precision oncology uses genetic testing to personalize cancer treatment.",
                "Immunotherapy helps the immune system fight cancer cells effectively.",
                "Targeted therapies attack specific molecular pathways in cancer cells.",
                "Biomarkers predict treatment response and disease progression.",
                "Early detection improves cancer survival rates significantly."
            ]
            
            kg_result = await client.call_tool(
                "build_knowledge_graph",
                {
                    "domain": "cancer_care",
                    "documents": kg_documents,
                    "max_nodes": 20,
                    "min_centrality": 0.05
                }
            )
            
            kg_result_dict = parse_fastmcp_result(kg_result)
            print(f"📊 Knowledge Graph Result: {kg_result_dict.get('status')}")
            
            if kg_result_dict.get('status') != 'success':
                print(f"❌ Failed to build knowledge graph: {kg_result_dict.get('message')}")
                return
            
            print(f"✅ Knowledge graph built: {kg_result_dict.get('nodes_count')} nodes, {kg_result_dict.get('edges_count')} edges")
            
            # Test editorial text
            editorial_text = """
            The future of cancer care is being transformed by precision oncology approaches 
            that combine advanced diagnostics like molecular profiling and liquid biopsies 
            with innovative treatments such as immunotherapy. Early detection remains paramount, 
            and multidisciplinary approaches are key to improving patient outcomes and addressing 
            previously untreatable or metastatic cancers.
            """
            
            print(f"\n🖼️ Step 2: Generating cover image...")
            print(f"Editorial text: {editorial_text[:100]}...")
            
            # Call the generate_cover_image tool
            result = await client.call_tool(
                "generate_cover_image",
                {
                    "editorial_text": editorial_text,
                    "domain": "cancer_care",
                    "style": "professional",
                    "dimensions": "1024x1024",
                    "image_engine": "dall-e-3"
                }
            )
            
            print("\n📊 Result:")
            result_dict = parse_fastmcp_result(result)
            print(f"Status: {result_dict.get('status', 'unknown')}")
            
            if result_dict.get('status') == 'success':
                print(f"✅ Image URL: {result_dict.get('image_url')}")
                print(f"✅ Engine Used: {result_dict.get('engine_used')}")
                print(f"✅ Dimensions: {result_dict.get('dimensions')}")
                print(f"✅ Style: {result_dict.get('style')}")
                
                # Show reasoning steps
                reasoning_steps = result_dict.get('reasoning_steps', [])
                if reasoning_steps:
                    print(f"\n🧠 Reasoning Steps ({len(reasoning_steps)} steps):")
                    for i, step in enumerate(reasoning_steps, 1):
                        print(f"  {i}. {step}")
                
                # Show keywords
                keywords = result_dict.get('keywords_extracted', [])
                if keywords:
                    print(f"\n🔍 Keywords Extracted ({len(keywords)} keywords):")
                    for kw in keywords[:5]:  # Show first 5
                        print(f"  - {kw.get('keyword', 'N/A')} (centrality: {kw.get('centrality_score', 0):.3f})")
                
                print("\n🎉 Cover image generation successful!")
            else:
                print(f"❌ Error: {result_dict.get('message', 'Unknown error')}")
                print(f"   Details: {result_dict.get('error_details', 'N/A')}")
                
    except Exception as e:
        print(f"❌ Error connecting to server: {e}")
        print("Make sure the FastMCP server is running:")
        print("  fastmcp run src/news_portal/mcp_tools/fastmcp_server.py:mcp --transport http --port 8002")

async def test_knowledge_graph_building():
    """Test the knowledge graph building tool."""
    print("\n🧠 Testing Knowledge Graph Building")
    print("=" * 40)
    
    client = Client("http://localhost:8002/mcp")
    
    try:
        async with client:
            print("✅ Connected to FastMCP server")
            
            # Test documents
            documents = [
                "Precision oncology uses molecular profiling to identify specific mutations in cancer cells.",
                "Immunotherapy harnesses the body's immune system to fight cancer more effectively.",
                "Early detection through liquid biopsies can identify cancer before symptoms appear.",
                "Personalized medicine tailors treatments based on individual genetic profiles."
            ]
            
            print("\n🔧 Building knowledge graph...")
            
            result = await client.call_tool(
                "build_knowledge_graph",
                {
                    "domain": "oncology_research",
                    "documents": documents,
                    "max_nodes": 20,
                    "min_centrality": 0.05
                }
            )
            
            result_dict = parse_fastmcp_result(result)
            print(f"\n📊 Result: {result_dict.get('status', 'unknown')}")
            if result_dict.get('status') == 'success':
                print(f"✅ Nodes created: {result_dict.get('nodes_created', 0)}")
                print(f"✅ Edges created: {result_dict.get('edges_created', 0)}")
                print(f"✅ Domain: {result_dict.get('domain', 'N/A')}")
            else:
                print(f"❌ Error: {result_dict.get('message', 'Unknown error')}")
                
    except Exception as e:
        print(f"❌ Error: {e}")

async def test_keyword_extraction():
    """Test the keyword extraction tool."""
    print("\n🔍 Testing Keyword Extraction")
    print("=" * 35)
    
    client = Client("http://localhost:8002/mcp")
    
    try:
        async with client:
            print("✅ Connected to FastMCP server")
            
            text = "Precision oncology and immunotherapy are revolutionizing cancer treatment through personalized approaches."
            
            print(f"\n📝 Extracting keywords from: {text}")
            
            result = await client.call_tool(
                "extract_keywords",
                {
                    "text": text,
                    "domain": "cancer_care",
                    "max_keywords": 5,
                    "min_centrality": 0.05
                }
            )
            
            result_dict = parse_fastmcp_result(result)
            print(f"\n📊 Result: {result_dict.get('status', 'unknown')}")
            if result_dict.get('status') == 'success':
                keywords = result_dict.get('keywords', [])
                print(f"✅ Extracted {len(keywords)} keywords:")
                for kw in keywords:
                    print(f"  - {kw.get('keyword', 'N/A')} (centrality: {kw.get('centrality_score', 0):.3f})")
            else:
                print(f"❌ Error: {result_dict.get('message', 'Unknown error')}")
                
    except Exception as e:
        print(f"❌ Error: {e}")

async def main():
    """Run all tests."""
    print("🚀 FastMCP Client Test Suite")
    print("=" * 50)
    print("Make sure the server is running:")
    print("  fastmcp run src/news_portal/mcp_tools/fastmcp_server.py:mcp --transport http --port 8002")
    print("=" * 50)
    
    # Test cover image generation (this should work with the mock KG)
    await test_cover_image_generation()
    
    # Test knowledge graph building
    await test_knowledge_graph_building()
    
    # Test keyword extraction
    await test_keyword_extraction()
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
