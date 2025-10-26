#!/usr/bin/env python3
"""
FastMCP Server for MCP Tools
=============================

MCP server using FastMCP for various domain intelligence tools.
"""

import asyncio
import sys
import os
from pathlib import Path

# Load environment variables
try:
    from dotenv import load_dotenv
    project_root = Path(__file__).parent.parent.parent.parent
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

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from fastmcp import FastMCP
from news_portal.mcp_tools import (
    CoverImageGeneratorTool,
    KnowledgeGraph,
    KnowledgeGraphNode,
    KnowledgeGraphEdge
)

# Create FastMCP server
mcp = FastMCP("Domain Intelligence MCP Server")

# Initialize the cover image tool
cover_image_tool = CoverImageGeneratorTool()

# Shared knowledge graph storage
shared_knowledge_graphs = {}

# Load pre-built knowledge graph at startup
def load_knowledge_graph():
    """Load the pre-built knowledge graph for 'cancer health care'."""
    try:
        graph_file = Path(__file__).parent / "knowledge_graphs" / "cancer_health_care.json"
        
        if graph_file.exists():
            print(f"📊 Loading knowledge graph from: {graph_file}")
            
            # Load JSON file
            import json
            with open(graph_file, 'r') as f:
                graph_data = json.load(f)
            
            # Restore nodes
            nodes = {}
            for node_data in graph_data.get("nodes", []):
                node = KnowledgeGraphNode(
                    id=node_data["id"],
                    label=node_data["label"],
                    node_type=node_data.get("node_type", "concept"),
                    centrality_score=node_data.get("centrality_score", 0.0)
                )
                nodes[node.id] = node
            
            # Restore edges
            edges = []
            for edge_data in graph_data.get("edges", []):
                edge = KnowledgeGraphEdge(
                    source=edge_data["source"],
                    target=edge_data["target"],
                    relation=edge_data.get("relation", ""),
                    weight=edge_data.get("weight", 1.0)
                )
                edges.append(edge)
            
            # Create knowledge graph
            from datetime import datetime
            kg = KnowledgeGraph(
                nodes=nodes,
                edges=edges,
                domain=graph_data.get("domain", "unknown"),
                created_at=graph_data.get("created_at", str(datetime.now()))
            )
            
            # Store in memory
            shared_knowledge_graphs["cancer health care"] = kg
            shared_knowledge_graphs["cancer_care"] = kg  # Backward compatibility
            
            # Set for the cover image tool
            cover_image_tool.set_knowledge_graphs({
                "cancer health care": kg,
                "cancer_care": kg
            })
            
            print(f"✅ Loaded knowledge graph: {len(kg.nodes)} nodes, {len(kg.edges)} edges")
            print(f"✅ Available domains: {list(shared_knowledge_graphs.keys())}")
            return True
        else:
            print(f"⚠️  Knowledge graph not found at: {graph_file}")
            print(f"   Run 'uv run python src/news_portal/mcp_tools/build_knowledge_graph.py' to create it")
            return False
    except Exception as e:
        print(f"⚠️  Error loading knowledge graph: {e}")
        import traceback
        traceback.print_exc()
        return False

# Load the knowledge graph at startup
load_knowledge_graph()

@mcp.tool
def generate_cover_image(
    editorial_text: str,
    domain: str = "cancer_care",
    style: str = "professional",
    dimensions: str = "1024x1024",
    image_engine: str = "dall-e-3"
) -> dict:
    """
    Generate a contextual cover image for editorial content using knowledge graph insights.
    
    Args:
        editorial_text: The editorial text to analyze and generate image for
        domain: The domain context (default: cancer_care)
        style: Image style (default: professional)
        dimensions: Image dimensions (default: 1024x1024)
        image_engine: Image generation engine (default: dall-e-3)
    
    Returns:
        Dictionary with image URL, metadata, and reasoning steps
    """
    try:
        print(f"🔍 Debug: generate_cover_image called with domain: {domain}")
        print(f"🔍 Debug: Available knowledge graphs: {list(cover_image_tool.knowledge_graphs.keys())}")
        
        # Run the async function in a new event loop
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an event loop, we need to use run_in_executor
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        lambda: asyncio.run(
                            cover_image_tool.execute(
                                editorial_text=editorial_text,
                                domain=domain,
                                style=style,
                                dimensions=dimensions,
                                image_engine=image_engine
                            )
                        )
                    )
                    result = future.result()
            else:
                result = loop.run_until_complete(
                    cover_image_tool.execute(
                        editorial_text=editorial_text,
                        domain=domain,
                        style=style,
                        dimensions=dimensions,
                        image_engine=image_engine
                    )
                )
        except RuntimeError:
            # No event loop running, create a new one
            result = asyncio.run(
                cover_image_tool.execute(
                    editorial_text=editorial_text,
                    domain=domain,
                    style=style,
                    dimensions=dimensions,
                    image_engine=image_engine
                )
            )
        return result
    except Exception as e:
        return {
            "status": "error",
            "message": f"Cover image generation failed: {str(e)}"
        }


@mcp.tool
def extract_keywords(
    text: str,
    domain: str = "cancer_care",
    max_keywords: int = 10,
    min_centrality: float = 0.05
) -> dict:
    """
    Extract high-centrality keywords from text using knowledge graph.
    
    Args:
        text: The text to extract keywords from
        domain: The domain context
        max_keywords: Maximum number of keywords to return
        min_centrality: Minimum centrality threshold
    
    Returns:
        Dictionary with extracted keywords and metadata
    """
    try:
        from news_portal.mcp_tools import KeywordExtractorTool
        
        kw_tool = KeywordExtractorTool()
        
        # Get the knowledge graph from shared storage
        if domain in shared_knowledge_graphs:
            kw_tool.set_knowledge_graphs({domain: shared_knowledge_graphs[domain]})
        else:
            # Fallback to cover_image_tool for backward compatibility
            try:
                kgs = cover_image_tool.get_knowledge_graphs()
                if domain in kgs:
                    kw_tool.set_knowledge_graphs({domain: kgs[domain]})
            except AttributeError:
                pass
        
        # Run the async function with proper event loop handling
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        lambda: asyncio.run(
                            kw_tool.execute(
                                text=text,
                                domain=domain,
                                max_keywords=max_keywords,
                                min_centrality=min_centrality
                            )
                        )
                    )
                    result = future.result()
            else:
                result = loop.run_until_complete(
                    kw_tool.execute(
                        text=text,
                        domain=domain,
                        max_keywords=max_keywords,
                        min_centrality=min_centrality
                    )
                )
        except RuntimeError:
            result = asyncio.run(
                kw_tool.execute(
                    text=text,
                    domain=domain,
                    max_keywords=max_keywords,
                    min_centrality=min_centrality
                )
            )
        return result
    except Exception as e:
        return {
            "status": "error",
            "message": f"Keyword extraction failed: {str(e)}"
        }

@mcp.tool
def build_glossary(
    domain: str = "cancer_care",
    max_terms: int = 20,
    min_centrality: float = 0.1
) -> dict:
    """
    Build a high-value glossary from knowledge graph nodes.
    
    Args:
        domain: The domain context
        max_terms: Maximum number of terms to include
        min_centrality: Minimum centrality threshold
    
    Returns:
        Dictionary with glossary terms and definitions
    """
    try:
        from news_portal.mcp_tools import GlossaryBuilderTool
        
        glossary_tool = GlossaryBuilderTool()
        
        # Get the knowledge graph from shared storage
        if domain in shared_knowledge_graphs:
            glossary_tool.set_knowledge_graphs({domain: shared_knowledge_graphs[domain]})
        else:
            # Fallback to cover_image_tool for backward compatibility
            try:
                kgs = cover_image_tool.get_knowledge_graphs()
                if domain in kgs:
                    glossary_tool.set_knowledge_graphs({domain: kgs[domain]})
            except AttributeError:
                pass
        
        # Run the async function with proper event loop handling
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        lambda: asyncio.run(
                            glossary_tool.execute(
                                domain=domain,
                                max_terms=max_terms,
                                min_centrality=min_centrality
                            )
                        )
                    )
                    result = future.result()
            else:
                result = loop.run_until_complete(
                    glossary_tool.execute(
                        domain=domain,
                        max_terms=max_terms,
                        min_centrality=min_centrality
                    )
                )
        except RuntimeError:
            result = asyncio.run(
                glossary_tool.execute(
                    domain=domain,
                    max_terms=max_terms,
                    min_centrality=min_centrality
                )
            )
        return result
    except Exception as e:
        return {
            "status": "error",
            "message": f"Glossary building failed: {str(e)}"
        }

if __name__ == "__main__":
    print("🚀 Starting FastMCP Domain Intelligence Server...")
    print("=" * 50)
    print("Available tools:")
    print("  - generate_cover_image: Generate contextual cover images")
    print("  - extract_keywords: Extract high-centrality keywords")
    print("  - build_glossary: Build domain glossaries")
    print("=" * 50)
    print("ℹ️  Note: Knowledge graph loaded at startup from JSON file")
    print("=" * 50)
    
    mcp.run()
