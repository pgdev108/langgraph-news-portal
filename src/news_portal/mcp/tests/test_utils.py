#!/usr/bin/env python3
"""
Test Utilities for MCP Tools
============================

Common utilities for MCP tool testing.
"""

import os
import sys
import logging
from pathlib import Path

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_test_environment():
    """Set up test environment and load variables."""
    try:
        from dotenv import load_dotenv
        project_root = Path(__file__).parent.parent.parent.parent.parent
        env_file = project_root / ".env"
        if env_file.exists():
            load_dotenv(env_file)
            logger.info(f"Loaded environment variables from: {env_file}")
        else:
            logger.warning(f".env file not found at: {env_file}")
    except ImportError:
        logger.warning("python-dotenv not installed")

    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY not found!")
        sys.exit(1)
    else:
        logger.info("OPENAI_API_KEY found")

def log_test_result(test_name: str, result: dict):
    """Log test results in a consistent format."""
    status = result.get('status', 'unknown')
    logger.info(f"Test '{test_name}': {status}")
    
    if status == 'success':
        logger.info(f"✅ Success: {result.get('message', 'No message')}")
    else:
        logger.error(f"❌ Error: {result.get('message', 'Unknown error')}")

def log_knowledge_graph_stats(result: dict):
    """Log knowledge graph statistics."""
    if result.get('status') == 'success':
        logger.info(f"📊 KG Stats: {result.get('nodes_count', 0)} nodes, {result.get('edges_count', 0)} edges")
        
        top_nodes = result.get('top_nodes', [])
        if top_nodes:
            logger.info("📋 Top nodes by centrality:")
            for i, (node_id, score) in enumerate(top_nodes[:5], 1):
                logger.info(f"  {i}. {node_id} (centrality: {score:.3f})")

def log_keywords(keywords: list, max_show: int = 5):
    """Log extracted keywords."""
    if keywords:
        logger.info(f"🔍 Extracted {len(keywords)} keywords:")
        for i, kw in enumerate(keywords[:max_show], 1):
            logger.info(f"  {i}. {kw.get('keyword', 'N/A')} (centrality: {kw.get('centrality_score', 0):.3f})")

def log_glossary_terms(terms: list, max_show: int = 3):
    """Log glossary terms."""
    if terms:
        logger.info(f"📚 Built glossary with {len(terms)} terms:")
        for i, term in enumerate(terms[:max_show], 1):
            term_name = term.get('term', 'N/A')
            centrality = term.get('centrality_score', 0)
            definition = term.get('definition', 'No definition')
            logger.info(f"  {i}. {term_name} (centrality: {centrality:.3f})")
            logger.info(f"     Definition: {definition[:100]}...")
