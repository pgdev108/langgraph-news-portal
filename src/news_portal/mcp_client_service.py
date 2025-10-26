#!/usr/bin/env python3
"""
MCP Client Service for News Portal
==================================

Service to interact with MCP tools for cover image generation.
The MCP tool handles:
- Image generation via DALL-E
- Local saving to generated_images/ folder
- Cloudinary upload
"""

import asyncio
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Use the fastmcp client directly since we know it works
from fastmcp import Client

logger = logging.getLogger(__name__)

class MCPClientService:
    """Service to interact with MCP tools for cover image generation."""
    
    def __init__(self, mcp_server_url: str = "http://localhost:8002"):
        self.mcp_server_url = mcp_server_url
        self.client = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        # Use the fastmcp client directly
        self.client = Client(f"{self.mcp_server_url}/mcp")
        await self.client.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.client:
            await self.client.__aexit__(exc_type, exc_val, exc_tb)
    
    async def generate_glossary(
        self,
        domain: str = "cancer_care",
        max_terms: int = 20,
        min_centrality: float = 0.1
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a glossary using the pre-built knowledge graph.
        
        Args:
            domain: Domain context (default: cancer_care)
            max_terms: Maximum number of terms to include
            min_centrality: Minimum centrality threshold
            
        Returns:
            Dictionary with glossary data or None if failed
        """
        try:
            if not self.client:
                logger.error("MCP client not initialized")
                return None
            
            logger.info(f"Generating glossary for domain: {domain}")
            
            # Call the MCP tool using fastmcp client
            result = await self.client.call_tool(
                "build_glossary",
                {
                    "domain": domain,
                    "max_terms": max_terms,
                    "min_centrality": min_centrality
                }
            )
            
            # Parse the result exactly like the cover image generation
            if hasattr(result, 'content') and result.content:
                result_data = result.content[0].text
                try:
                    parsed_result = json.loads(result_data)
                    
                    if parsed_result.get('status') == 'success':
                        logger.info(f"✅ Glossary generated with {parsed_result.get('total_terms', 0)} terms")
                        return parsed_result
                    else:
                        logger.error(f"❌ Glossary generation failed: {parsed_result.get('message')}")
                        return None
                        
                except json.JSONDecodeError:
                    logger.error(f"❌ Failed to parse MCP result: {result_data}")
                    return None
            else:
                logger.error("❌ No content in MCP result")
                return None
                
        except Exception as e:
            logger.error(f"❌ Glossary generation error: {e}")
            return None
    
    async def generate_portal_cover_image(
        self, 
        editorial_text: str, 
        domain: str = "cancer_care",
        style: str = "professional",
        dimensions: str = "1792x1024"
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a portal cover image for the main editorial.
        
        Args:
            editorial_text: The main editorial text
            domain: Domain context (default: cancer_care)
            style: Image style (default: professional)
            dimensions: Image dimensions (default: 1792x1024 for portal cover)
            
        Returns:
            Dictionary with image data or None if failed
        """
        try:
            if not self.client:
                logger.error("MCP client not initialized")
                return None
            
            logger.info(f"Generating portal cover for domain: {domain} with dimensions: {dimensions}")
            
            # Call the MCP tool using fastmcp client
            result = await self.client.call_tool(
                "generate_cover_image",
                {
                    "editorial_text": editorial_text,
                    "domain": domain,
                    "style": style,
                    "dimensions": dimensions,
                    "image_engine": "dall-e-3"
                }
            )
            
            # Parse the result exactly like the test script
            if hasattr(result, 'content') and result.content:
                result_data = result.content[0].text
                try:
                    parsed_result = json.loads(result_data)
                    
                    if parsed_result.get('status') == 'success':
                        # The MCP tool now handles everything:
                        # - Generates image via DALL-E
                        # - Saves locally to generated_images/ folder
                        # - Uploads to Cloudinary
                        # - Returns Cloudinary URL as primary URL
                        
                        cloudinary_url = parsed_result.get('image_url')
                        local_path = parsed_result.get('local_path')
                        
                        logger.info(f"✅ Portal cover generated")
                        logger.info(f"   Cloudinary URL: {cloudinary_url}")
                        logger.info(f"   Local path: {local_path}")
                        
                        # Add explicit fields for clarity
                        parsed_result['cloudinary_url'] = cloudinary_url
                        parsed_result['local_image_path'] = local_path
                        
                        return parsed_result
                    else:
                        logger.error(f"❌ Portal cover generation failed: {parsed_result.get('message')}")
                        return None
                        
                except json.JSONDecodeError:
                    logger.error(f"❌ Failed to parse MCP result: {result_data}")
                    return None
            else:
                logger.error("❌ No content in MCP result")
                return None
                
        except Exception as e:
            logger.error(f"❌ Portal cover generation error: {e}")
            return None

# Convenience functions for easy integration
async def generate_portal_cover_image(editorial_text: str, domain: str = "cancer_care", dimensions: str = "1792x1024") -> Optional[Dict[str, Any]]:
    """
    Convenience function to generate a portal cover image.
    
    Args:
        editorial_text: The main editorial text
        domain: Domain context (default: cancer_care)
        dimensions: Image dimensions (default: 1792x1024 for portal cover)
        
    Returns:
        Dictionary with image data or None if failed
    """
    async with MCPClientService() as service:
        return await service.generate_portal_cover_image(editorial_text, domain, dimensions=dimensions)

async def generate_glossary(domain: str = "cancer_care", max_terms: int = 20, min_centrality: float = 0.1) -> Optional[Dict[str, Any]]:
    """
    Convenience function to generate a glossary.
    
    Args:
        domain: Domain context (default: cancer_care)
        max_terms: Maximum number of terms (default: 20)
        min_centrality: Minimum centrality threshold (default: 0.1)
        
    Returns:
        Dictionary with glossary data or None if failed
    """
    async with MCPClientService() as service:
        return await service.generate_glossary(domain, max_terms, min_centrality)
