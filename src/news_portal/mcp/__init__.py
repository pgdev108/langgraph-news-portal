#!/usr/bin/env python3
"""
Domain Intelligence MCP Package
===============================

A comprehensive MCP package providing:
1. Knowledge Graph Builder
2. Smart Keyword Extractor  
3. Glossary Builder
4. Cover Image Generator

Built for domain-aware content intelligence using graph theory and centrality measures.
"""

from .mcp_tools_base import (
    BaseMCPTool,
    KnowledgeGraph,
    KnowledgeGraphNode,
    KnowledgeGraphEdge,
    GraphProcessor,
    LLMProcessor,
    ImageProcessor,
    Config
)

from .mcp_tools_knowledge_graph import KnowledgeGraphBuilderTool
from .mcp_tools_keyword_extractor import KeywordExtractorTool
from .mcp_tools_glossary_builder import GlossaryBuilderTool
from .mcp_tools_cover_image_generator import CoverImageGeneratorTool

__version__ = "1.0.0"
__author__ = "Domain Intelligence Team"

__all__ = [
    # Base classes
    "BaseMCPTool",
    "KnowledgeGraph",
    "KnowledgeGraphNode", 
    "KnowledgeGraphEdge",
    "GraphProcessor",
    "LLMProcessor",
    "ImageProcessor",
    "Config",
    
    # Tools
    "KnowledgeGraphBuilderTool",
    "KeywordExtractorTool", 
    "GlossaryBuilderTool",
    "CoverImageGeneratorTool",
]
