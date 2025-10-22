#!/usr/bin/env python3
"""
Image Viewer for Generated Cover Images
=====================================

Simple script to download and display generated cover images from the FastMCP server.
"""

import asyncio
import sys
import os
import requests
import webbrowser
from pathlib import Path
from datetime import datetime

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

def download_and_display_image(image_url, filename=None):
    """Download image from URL and display it."""
    try:
        print(f"\n📥 Downloading image from: {image_url[:100]}...")
        
        # Download the image
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        
        # Create filename if not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"generated_cover_image_{timestamp}.png"
        
        # Save to images directory
        images_dir = Path(__file__).parent / "generated_images"
        images_dir.mkdir(exist_ok=True)
        
        filepath = images_dir / filename
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ Image saved to: {filepath}")
        print(f"📏 File size: {len(response.content)} bytes")
        
        # Try to open the image
        try:
            webbrowser.open(f"file://{filepath.absolute()}")
            print(f"🖼️  Image opened in default browser")
        except Exception as e:
            print(f"⚠️  Could not open image automatically: {e}")
            print(f"   You can manually open: {filepath}")
        
        return str(filepath)
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error downloading image: {e}")
        return None
    except Exception as e:
        print(f"❌ Error saving image: {e}")
        return None

async def generate_and_view_image():
    """Generate a cover image and display it."""
    print("\n🎯 Generating Cover Image and Displaying")
    print("=" * 50)
    
    # Connect to the FastMCP server
    client = Client("http://localhost:8002/mcp")
    
    try:
        async with client:
            print("✅ Connected to FastMCP server")
            
            # First, build a knowledge graph for precision_medicine domain
            print("\n🔧 Step 1: Building knowledge graph for precision_medicine domain...")
            kg_documents = [
                "Precision medicine uses genetic testing to personalize cancer treatment.",
                "Immunotherapy helps the immune system fight cancer cells effectively.",
                "Targeted therapies attack specific molecular pathways in cancer cells.",
                "Biomarkers predict treatment response and disease progression.",
                "Early detection improves cancer survival rates significantly.",
                "Liquid biopsies detect cancer DNA in blood samples non-invasively.",
                "Molecular profiling identifies specific mutations in cancer cells.",
                "Multidisciplinary approaches combine different treatment modalities."
            ]
            
            kg_result = await client.call_tool(
                "build_knowledge_graph",
                {
                    "domain": "precision_medicine",
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
                    "domain": "precision_medicine",
                    "style": "professional",
                    "dimensions": "1024x1024",
                    "image_engine": "dall-e-3"
                }
            )
            
            print("\n📊 Result:")
            result_dict = parse_fastmcp_result(result)
            print(f"Status: {result_dict.get('status', 'unknown')}")
            
            if result_dict.get('status') == 'success':
                image_url = result_dict.get('image_url')
                engine_used = result_dict.get('engine_used')
                dimensions = result_dict.get('dimensions')
                style = result_dict.get('style')
                
                print(f"✅ Image URL: {image_url}")
                print(f"✅ Engine Used: {engine_used}")
                print(f"✅ Dimensions: {dimensions}")
                print(f"✅ Style: {style}")
                
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
                
                # Download and display the image
                if image_url:
                    print(f"\n🖼️  Downloading and displaying image...")
                    filepath = download_and_display_image(image_url)
                    
                    if filepath:
                        print(f"\n🎉 Cover image generation and display successful!")
                        print(f"📁 Image saved to: {filepath}")
                    else:
                        print(f"\n❌ Failed to download image")
                else:
                    print(f"\n❌ No image URL in result")
            else:
                print(f"❌ Error: {result_dict.get('message', 'Unknown error')}")
                print(f"   Details: {result_dict.get('error_details', 'N/A')}")
                
    except Exception as e:
        print(f"❌ Error connecting to server: {e}")
        print("Make sure the FastMCP server is running:")
        print("  fastmcp run src/news_portal/mcp/fastmcp_server.py:mcp --transport http --port 8002")

async def generate_multiple_styles():
    """Generate images with different styles."""
    print("\n🎨 Generating Images with Different Styles")
    print("=" * 50)
    
    styles = ["professional", "artistic", "modern", "minimalist"]
    
    client = Client("http://localhost:8002/mcp")
    
    try:
        async with client:
            print("✅ Connected to FastMCP server")
            
            editorial_text = """
            Precision oncology represents a paradigm shift in cancer treatment, 
            moving from one-size-fits-all approaches to personalized therapies 
            based on individual genetic profiles and molecular characteristics.
            """
            
            for style in styles:
                print(f"\n🎨 Generating {style} style image...")
                
                result = await client.call_tool(
                    "generate_cover_image",
                    {
                        "editorial_text": editorial_text,
                        "domain": "precision_medicine",
                        "style": style,
                        "dimensions": "1024x1024",
                        "image_engine": "dall-e-3"
                    }
                )
                
                result_dict = parse_fastmcp_result(result)
                
                if result_dict.get('status') == 'success':
                    image_url = result_dict.get('image_url')
                    print(f"✅ {style.capitalize()} image generated")
                    
                    # Download with style-specific filename
                    filename = f"cover_image_{style}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    filepath = download_and_display_image(image_url, filename)
                    
                    if filepath:
                        print(f"📁 Saved: {filepath}")
                else:
                    print(f"❌ Failed to generate {style} image: {result_dict.get('message')}")
                
    except Exception as e:
        print(f"❌ Error: {e}")

async def main():
    """Main function."""
    print("🖼️  Cover Image Generator and Viewer")
    print("=" * 50)
    print("Make sure the server is running:")
    print("  fastmcp run src/news_portal/mcp/fastmcp_server.py:mcp --transport http --port 8002")
    print("=" * 50)
    
    # Generate and view a single image
    await generate_and_view_image()
    
    # Ask if user wants to generate multiple styles
    print("\n" + "=" * 50)
    response = input("Would you like to generate images with different styles? (y/n): ")
    if response.lower() in ['y', 'yes']:
        await generate_multiple_styles()
    
    print("\n✅ Image generation and viewing completed!")

if __name__ == "__main__":
    asyncio.run(main())
