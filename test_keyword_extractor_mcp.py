#!/usr/bin/env python3
"""
Test Keyword Extractor via FastMCP Server
=========================================

Tests the keyword extractor tool through the FastMCP server.
"""

import asyncio
import json
import sys
from pathlib import Path

from dotenv import load_dotenv
from fastmcp import Client

# Load environment variables
load_dotenv()

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

async def test_keyword_extractor():
    """Test keyword extraction via FastMCP server."""
    print("🔍 Keyword Extractor Test via FastMCP Server")
    print("=" * 60)
    
    client = Client("http://localhost:8002/mcp")
    
    try:
        async with client:
            print("✅ Connected to FastMCP server")
            print("ℹ️  Using pre-built knowledge graph loaded at server startup\n")
            
            # Test text about cancer care
            test_text = """
            Precision oncology and immunotherapy are revolutionizing cancer treatment. 
            These personalized approaches target specific molecular pathways in cancer cells.
            Early detection significantly improves patient outcomes and survival rates.
            Biomarkers help predict treatment response and guide clinical decisions.
            Targeted therapies offer more effective treatment options with fewer side effects.
            """
            
            print(f"📝 Extracting keywords from text:")
            print(f"   {test_text[:100]}...\n")
            
            # Extract keywords
            result = await client.call_tool(
                "extract_keywords",
                {
                    "text": test_text,
                    "domain": "cancer health care",  # Use the pre-built domain
                    "max_keywords": 10,
                    "min_centrality": 0.05
                }
            )
            
            result_dict = parse_fastmcp_result(result)
            print(f"📊 Result: {result_dict.get('status')}")
            
            if result_dict.get('status') == 'success':
                keywords = result_dict.get('keywords', [])
                print(f"✅ Extracted {len(keywords)} keywords:\n")
                
                for i, kw in enumerate(keywords, 1):
                    print(f"  {i:2d}. {kw.get('keyword', 'N/A'):<30} (centrality: {kw.get('centrality_score', 0):.3f})")
                
                print(f"\n📊 Summary:")
                print(f"   Total candidates: {result_dict.get('total_candidates', 0)}")
                print(f"   Matched keywords: {result_dict.get('matched_keywords', 0)}")
                
                if keywords:
                    centrality_range = result_dict.get('centrality_range', {})
                    print(f"   Centrality range: {centrality_range.get('min', 0):.3f} - {centrality_range.get('max', 0):.3f}")
            else:
                print(f"❌ Error: {result_dict.get('message')}")
                
    except Exception as e:
        print(f"❌ Connection error: {e}")
        print(f"\n💡 Make sure the FastMCP server is running:")
        print(f"   fastmcp run src/news_portal/mcp_tools/fastmcp_server.py:mcp --transport http --port 8002")

if __name__ == "__main__":
    asyncio.run(test_keyword_extractor())
