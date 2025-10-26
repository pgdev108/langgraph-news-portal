#!/usr/bin/env python3
"""
FastMCP Server for Cover Image Generation
========================================

Simple MCP server using FastMCP for cover image generation.
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
from news_portal.mcp import (
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

# Create a knowledge graph for testing
def create_test_knowledge_graph():
    """Create a test knowledge graph."""
    mock_nodes = {
        "cancer_care": KnowledgeGraphNode(id="cancer_care", label="cancer care", centrality_score=0.95),
        "precision_oncology": KnowledgeGraphNode(id="precision_oncology", label="precision oncology", centrality_score=0.90),
        "early_detection": KnowledgeGraphNode(id="early_detection", label="early detection", centrality_score=0.85),
        "immunotherapy": KnowledgeGraphNode(id="immunotherapy", label="immunotherapy", centrality_score=0.80),
        "personalized_medicine": KnowledgeGraphNode(id="personalized_medicine", label="personalized medicine", centrality_score=0.75)
    }
    
    mock_edges = [
        KnowledgeGraphEdge(source="cancer_care", target="precision_oncology", relation="includes"),
        KnowledgeGraphEdge(source="precision_oncology", target="personalized_medicine", relation="enables"),
        KnowledgeGraphEdge(source="early_detection", target="cancer_care", relation="improves"),
        KnowledgeGraphEdge(source="immunotherapy", target="cancer_care", relation="treats")
    ]
    
    mock_kg = KnowledgeGraph(
        nodes=mock_nodes,
        edges=mock_edges,
        domain="cancer_care",
        created_at="2024-01-01"
    )
    
    return mock_kg

# Set up the knowledge graph
test_kg = create_test_knowledge_graph()
print(f"✅ Created test knowledge graph with {len(test_kg.nodes)} nodes")
cover_image_tool.set_knowledge_graphs({"cancer_care": test_kg})
print(f"✅ Set knowledge graphs for cover image tool")
print(f"✅ Available domains: {list(cover_image_tool.knowledge_graphs.keys())}")

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
def build_knowledge_graph(
    domain: str,
    documents: list,
    max_nodes: int = 50,
    min_centrality: float = 0.05
) -> dict:
    """
    Build a domain-specific knowledge graph from documents.
    
    Args:
        domain: The domain name (e.g., 'cancer_care', 'finance', 'law')
        documents: List of documents to analyze
        max_nodes: Maximum number of nodes to generate
        min_centrality: Minimum centrality threshold
    
    Returns:
        Dictionary with knowledge graph metadata
    """
    try:
        from news_portal.mcp import KnowledgeGraphBuilderTool
        
        kg_tool = KnowledgeGraphBuilderTool()
        
        # Run the async function with proper event loop handling
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        lambda: asyncio.run(
                            kg_tool.execute(
                                domain=domain,
                                documents=documents,
                                max_nodes=max_nodes,
                                min_centrality=min_centrality
                            )
                        )
                    )
                    result = future.result()
            else:
                result = loop.run_until_complete(
                    kg_tool.execute(
                        domain=domain,
                        documents=documents,
                        max_nodes=max_nodes,
                        min_centrality=min_centrality
                    )
                )
        except RuntimeError:
            result = asyncio.run(
                kg_tool.execute(
                    domain=domain,
                    documents=documents,
                    max_nodes=max_nodes,
                    min_centrality=min_centrality
                )
            )
        
        # If successful, store the knowledge graph in shared storage
        if result.get("status") == "success":
            kg = kg_tool.get_knowledge_graph(domain)
            shared_knowledge_graphs[domain] = kg
            cover_image_tool.set_knowledge_graphs({domain: kg})
        
        return result
    except Exception as e:
        return {
            "status": "error",
            "message": f"Knowledge graph building failed: {str(e)}"
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
        from news_portal.mcp import KeywordExtractorTool
        
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
        from news_portal.mcp import GlossaryBuilderTool
        
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
    print("  - build_knowledge_graph: Build domain knowledge graphs")
    print("  - extract_keywords: Extract high-centrality keywords")
    print("  - build_glossary: Build domain glossaries")
    print("=" * 50)
    
    mcp.run()
