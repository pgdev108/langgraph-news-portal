#!/usr/bin/env python3
"""
Smart Keyword Extractor MCP Tool
================================

Tool for extracting high-centrality keywords from text using knowledge graph centrality measures.
"""

import logging
from typing import Dict, Any, List

from .mcp_tools_base import (
    BaseMCPTool, KnowledgeGraph, LLMProcessor, Config
)

logger = logging.getLogger(__name__)

class KeywordExtractorTool(BaseMCPTool):
    """MCP Tool for extracting high-centrality keywords from text."""
    
    def __init__(self, openai_client=None):
        super().__init__(openai_client)
        self.llm_processor = LLMProcessor(self.openai_client)
    
    def get_tool_definition(self) -> Dict[str, Any]:
        """Return the MCP tool definition."""
        return {
            "name": "extract_keywords",
            "description": "Extract high-centrality keywords from text using knowledge graph",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to extract keywords from"
                    },
                    "domain": {
                        "type": "string",
                        "description": "Domain name for knowledge graph lookup"
                    },
                    "max_keywords": {
                        "type": "integer",
                        "default": Config.DEFAULT_MAX_KEYWORDS,
                        "description": "Maximum number of keywords to return"
                    },
                    "min_centrality": {
                        "type": "number",
                        "default": 0.05,
                        "description": "Minimum centrality threshold"
                    }
                },
                "required": ["text", "domain"]
            }
        }
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the keyword extraction tool."""
        text = kwargs["text"]
        domain = kwargs["domain"]
        max_keywords = kwargs.get("max_keywords", Config.DEFAULT_MAX_KEYWORDS)
        min_centrality = kwargs.get("min_centrality", 0.05)
        
        logger.info(f"Extracting keywords from text for domain: {domain}")
        
        try:
            # Check if knowledge graph exists
            if domain not in self.knowledge_graphs:
                return {
                    "status": "error",
                    "message": f"No knowledge graph found for domain: {domain}. Please build a knowledge graph first using the build_knowledge_graph tool."
                }
            
            kg = self.knowledge_graphs[domain]
            
            # Step 1: Extract candidate keywords from text
            candidate_keywords = await self.llm_processor.extract_candidate_keywords(text)
            
            # Step 2: Match against knowledge graph nodes
            matched_keywords = []
            for keyword in candidate_keywords:
                keyword_lower = keyword.lower()
                for node_id, node in kg.nodes.items():
                    if (keyword_lower in node.label.lower() or 
                        node.label.lower() in keyword_lower):
                        matched_keywords.append({
                            "keyword": keyword,
                            "node_id": node_id,
                            "centrality_score": node.centrality_score,
                            "node_label": node.label
                        })
                        break
            
            # Step 3: Sort by centrality and filter
            matched_keywords.sort(key=lambda x: x["centrality_score"], reverse=True)
            filtered_keywords = [
                kw for kw in matched_keywords 
                if kw["centrality_score"] >= min_centrality
            ][:max_keywords]
            
            return {
                "status": "success",
                "domain": domain,
                "keywords": filtered_keywords,
                "total_candidates": len(candidate_keywords),
                "matched_keywords": len(filtered_keywords),
                "method": "knowledge_graph",
                "centrality_range": {
                    "min": min([kw["centrality_score"] for kw in filtered_keywords]) if filtered_keywords else 0,
                    "max": max([kw["centrality_score"] for kw in filtered_keywords]) if filtered_keywords else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Keyword extraction failed: {e}")
            return {
                "status": "error",
                "message": f"Keyword extraction failed: {str(e)}"
            }
    
    def match_keywords_against_graph(
        self, 
        keywords: List[str], 
        kg: KnowledgeGraph
    ) -> List[Dict[str, Any]]:
        """Match keywords against knowledge graph nodes."""
        matched_keywords = []
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            for node_id, node in kg.nodes.items():
                if (keyword_lower in node.label.lower() or 
                    node.label.lower() in keyword_lower):
                    matched_keywords.append({
                        "keyword": keyword,
                        "node_id": node_id,
                        "centrality_score": node.centrality_score,
                        "node_label": node.label
                    })
                    break
        
        return matched_keywords
    
    def get_high_centrality_keywords(
        self, 
        matched_keywords: List[Dict[str, Any]], 
        min_centrality: float = 0.1
    ) -> List[Dict[str, Any]]:
        """Get keywords with high centrality scores."""
        return [
            kw for kw in matched_keywords 
            if kw["centrality_score"] >= min_centrality
        ]
    
    def analyze_keyword_distribution(
        self, 
        keywords: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze the distribution of keyword centrality scores."""
        if not keywords:
            return {"status": "error", "message": "No keywords provided"}
        
        centrality_scores = [kw["centrality_score"] for kw in keywords]
        
        return {
            "total_keywords": len(keywords),
            "centrality_stats": {
                "min": min(centrality_scores),
                "max": max(centrality_scores),
                "mean": sum(centrality_scores) / len(centrality_scores),
                "median": sorted(centrality_scores)[len(centrality_scores) // 2]
            },
            "high_centrality_count": len([s for s in centrality_scores if s >= 0.1]),
            "medium_centrality_count": len([s for s in centrality_scores if 0.05 <= s < 0.1]),
            "low_centrality_count": len([s for s in centrality_scores if s < 0.05])
        }
