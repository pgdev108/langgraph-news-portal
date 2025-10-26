#!/usr/bin/env python3
"""
Test MCP Client Integration
==========================

Test the MCP client service for cover image generation.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from news_portal.mcp_client_service import MCPClientService

async def test_mcp_client():
    """Test the MCP client service."""
    print("🧪 Testing MCP Client Service")
    print("=" * 50)
    
    # Test editorial text
    editorial_text = """
    Cancer research continues to make significant breakthroughs in 2025. 
    New immunotherapy treatments are showing promising results in clinical trials, 
    while precision medicine approaches are revolutionizing how we treat different 
    types of cancer. Early detection technologies are also advancing rapidly, 
    offering hope for better patient outcomes.
    """
    
    try:
        async with MCPClientService() as service:
            print("🖼️ Testing portal cover generation...")
            result = await service.generate_portal_cover_image(editorial_text, "cancer_care", dimensions="1792x1024")
            
            if result:
                print(f"✅ Portal cover generation successful!")
                print(f"   Status: {result.get('status')}")
                print(f"   Cloudinary URL: {result.get('cloudinary_url')}")
                print(f"   Original URL: {result.get('original_url')}")
                print(f"   Local Path: {result.get('local_path')}")
                
                # Check if local file exists
                local_path = result.get('local_path')
                if local_path and os.path.exists(local_path):
                    print(f"✅ Local image file exists: {local_path}")
                    print(f"   File size: {os.path.getsize(local_path)} bytes")
                else:
                    print(f"⚠️ Local image file not found: {local_path}")
                
                # Check if Cloudinary URL is accessible
                cloudinary_url = result.get('cloudinary_url')
                if cloudinary_url and cloudinary_url.startswith('https://'):
                    print(f"✅ Cloudinary URL: {cloudinary_url}")
                else:
                    print(f"⚠️ Cloudinary URL not available: {cloudinary_url}")
            else:
                print("❌ Portal cover generation failed")
                
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Make sure the FastMCP server is running on http://localhost:8002")
    print("Command: fastmcp run src/news_portal/mcp/fastmcp_server.py:mcp --transport http --port 8002")
    print()
    
    asyncio.run(test_mcp_client())
