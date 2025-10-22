#!/usr/bin/env python3
"""
Glossary Builder MCP Tool
=========================

Tool for building high-value glossaries using knowledge graph centrality measures.
"""

import logging
from typing import Dict, Any, List

from .mcp_tools_base import (
    BaseMCPTool, KnowledgeGraph, KnowledgeGraphNode, LLMProcessor, Config
)

logger = logging.getLogger(__name__)

class GlossaryBuilderTool(BaseMCPTool):
    """MCP Tool for building high-value glossaries using knowledge graph centrality."""
    
    def __init__(self, openai_client=None):
        super().__init__(openai_client)
        self.llm_processor = LLMProcessor(self.openai_client)
    
    def get_tool_definition(self) -> Dict[str, Any]:
        """Return the MCP tool definition."""
        return {
            "name": "build_glossary",
            "description": "Build high-value glossary using knowledge graph centrality measures",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "Domain name for knowledge graph lookup"
                    },
                    "max_terms": {
                        "type": "integer",
                        "default": Config.DEFAULT_MAX_GLOSSARY_TERMS,
                        "description": "Maximum number of glossary terms"
                    },
                    "min_centrality": {
                        "type": "number",
                        "default": Config.DEFAULT_MIN_CENTRALITY,
                        "description": "Minimum centrality threshold"
                    },
                    "include_definitions": {
                        "type": "boolean",
                        "default": True,
                        "description": "Include AI-generated definitions"
                    }
                },
                "required": ["domain"]
            }
        }
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the glossary building tool."""
        domain = kwargs["domain"]
        max_terms = kwargs.get("max_terms", Config.DEFAULT_MAX_GLOSSARY_TERMS)
        min_centrality = kwargs.get("min_centrality", Config.DEFAULT_MIN_CENTRALITY)
        include_definitions = kwargs.get("include_definitions", True)
        
        logger.info(f"Building glossary for domain: {domain}")
        
        try:
            # Check if knowledge graph exists
            if domain not in self.knowledge_graphs:
                return {
                    "status": "error",
                    "message": f"No knowledge graph found for domain: {domain}"
                }
            
            kg = self.knowledge_graphs[domain]
            
            # Step 1: Get top nodes by centrality
            top_nodes = sorted(
                [(k, v) for k, v in kg.nodes.items()],
                key=lambda x: x[1].centrality_score,
                reverse=True
            )[:max_terms]
            
            # Step 2: Filter by centrality threshold
            filtered_nodes = [
                (k, v) for k, v in top_nodes 
                if v.centrality_score >= min_centrality
            ]
            
            # Step 3: Generate definitions if requested
            glossary_terms = []
            for node_id, node in filtered_nodes:
                term_data = {
                    "term": node.label,
                    "centrality_score": node.centrality_score,
                    "node_type": node.node_type
                }
                
                if include_definitions:
                    definition = await self.llm_processor.generate_definition(
                        node.label, domain, kg
                    )
                    term_data["definition"] = definition
                
                glossary_terms.append(term_data)
            
            return {
                "status": "success",
                "domain": domain,
                "glossary_terms": glossary_terms,
                "total_terms": len(glossary_terms),
                "centrality_range": {
                    "min": min([t["centrality_score"] for t in glossary_terms]) if glossary_terms else 0,
                    "max": max([t["centrality_score"] for t in glossary_terms]) if glossary_terms else 0
                },
                "definition_count": len([t for t in glossary_terms if "definition" in t])
            }
            
        except Exception as e:
            logger.error(f"Glossary building failed: {e}")
            return {
                "status": "error",
                "message": f"Glossary building failed: {str(e)}"
            }
    
    def analyze_glossary_quality(
        self, 
        glossary_terms: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze the quality and distribution of glossary terms."""
        if not glossary_terms:
            return {"status": "error", "message": "No glossary terms provided"}
        
        centrality_scores = [term["centrality_score"] for term in glossary_terms]
        
        return {
            "total_terms": len(glossary_terms),
            "centrality_stats": {
                "min": min(centrality_scores),
                "max": max(centrality_scores),
                "mean": sum(centrality_scores) / len(centrality_scores),
                "median": sorted(centrality_scores)[len(centrality_scores) // 2]
            },
            "high_centrality_terms": len([s for s in centrality_scores if s >= 0.2]),
            "medium_centrality_terms": len([s for s in centrality_scores if 0.1 <= s < 0.2]),
            "low_centrality_terms": len([s for s in centrality_scores if s < 0.1]),
            "terms_with_definitions": len([t for t in glossary_terms if "definition" in t]),
            "definition_coverage": len([t for t in glossary_terms if "definition" in t]) / len(glossary_terms) * 100
        }
    
    def export_glossary_formats(
        self, 
        glossary_terms: List[Dict[str, Any]], 
        format_type: str = "json"
    ) -> str:
        """Export glossary in different formats."""
        if format_type == "json":
            import json
            return json.dumps(glossary_terms, indent=2)
        
        elif format_type == "markdown":
            markdown = "# Domain Glossary\n\n"
            for term in glossary_terms:
                markdown += f"## {term['term']}\n"
                markdown += f"**Centrality Score:** {term['centrality_score']:.3f}\n"
                if "definition" in term:
                    markdown += f"**Definition:** {term['definition']}\n"
                markdown += "\n"
            return markdown
        
        elif format_type == "csv":
            import csv
            import io
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["Term", "Centrality Score", "Definition"])
            for term in glossary_terms:
                writer.writerow([
                    term["term"],
                    term["centrality_score"],
                    term.get("definition", "")
                ])
            return output.getvalue()
        
        else:
            return "Unsupported format. Use 'json', 'markdown', or 'csv'."
