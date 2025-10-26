#!/usr/bin/env python3
"""
Knowledge Graph Builder Utility
================================

Utility class for building and managing domain-specific knowledge graphs
from documents using LLM + graph theory. This is NOT an MCP tool.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime
import networkx as nx
import json
from pathlib import Path

from .mcp_tools_base import (
    BaseMCPTool, KnowledgeGraph, KnowledgeGraphNode, KnowledgeGraphEdge,
    GraphProcessor, LLMProcessor, Config
)

# Note: This class extends BaseMCPTool for infrastructure but is NOT exposed as an MCP tool
# It's used internally by build_knowledge_graph.py for one-time knowledge graph construction

logger = logging.getLogger(__name__)

class KnowledgeGraphBuilderTool(BaseMCPTool):
    """
    Utility class for building knowledge graphs from domain documents.
    
    Note: This is NOT exposed as an MCP tool. It extends BaseMCPTool for 
    infrastructure (OpenAI client, processors) but is used only by the 
    build_knowledge_graph.py utility script.
    """
    
    def __init__(self, openai_client=None):
        super().__init__(openai_client)
        self.graph_processor = GraphProcessor()
        self.llm_processor = LLMProcessor(self.openai_client)
    
    def get_tool_definition(self) -> Dict[str, Any]:
        """Return the MCP tool definition."""
        return {
            "name": "build_knowledge_graph",
            "description": "Build a domain-specific knowledge graph from documents using LLM",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "Domain name (e.g., 'oncology', 'finance', 'law')"
                    },
                    "documents": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of documents to analyze"
                    },
                    "max_nodes": {
                        "type": "integer",
                        "default": Config.DEFAULT_MAX_NODES,
                        "description": "Maximum number of nodes to generate"
                    },
                    "min_centrality": {
                        "type": "number",
                        "default": Config.DEFAULT_MIN_CENTRALITY,
                        "description": "Minimum centrality threshold for node inclusion"
                    }
                },
                "required": ["domain", "documents"]
            }
        }
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the knowledge graph building tool."""
        domain = kwargs["domain"]
        documents = kwargs["documents"]
        max_nodes = kwargs.get("max_nodes", Config.DEFAULT_MAX_NODES)
        min_centrality = kwargs.get("min_centrality", Config.DEFAULT_MIN_CENTRALITY)
        
        logger.info(f"Building knowledge graph for domain: {domain}")
        
        try:
            # Step 1: Generate triplets using LLM
            triplets = await self.llm_processor.generate_triplets_from_documents(
                domain, documents, max_nodes
            )
            
            # Step 2: Build NetworkX graph
            G = self.graph_processor.build_graph_from_triplets(triplets)
            nodes = {}
            edges = []
            
            for source, relation, target in triplets:
                # Add nodes
                if source not in nodes:
                    nodes[source] = KnowledgeGraphNode(
                        id=source, label=source, node_type="concept"
                    )
                if target not in nodes:
                    nodes[target] = KnowledgeGraphNode(
                        id=target, label=target, node_type="concept"
                    )
                
                # Add edge
                edges.append(KnowledgeGraphEdge(
                    source=source, target=target, relation=relation, weight=1.0
                ))
            
            # Step 3: Calculate centrality measures
            centrality_scores = await self.graph_processor.calculate_centrality_measures(G)
            
            # Step 4: Update nodes with centrality scores
            for node_id, score in centrality_scores.items():
                if node_id in nodes:
                    nodes[node_id].centrality_score = score
            
            # Step 5: Filter by centrality threshold
            filtered_nodes = {
                k: v for k, v in nodes.items() 
                if v.centrality_score >= min_centrality
            }
            
            # Step 6: Create knowledge graph
            kg = KnowledgeGraph(
                nodes=filtered_nodes,
                edges=edges,
                domain=domain,
                created_at=str(datetime.now())
            )
            
            # Step 7: Store knowledge graph
            self.knowledge_graphs[domain] = kg
            
            return {
                "status": "success",
                "domain": domain,
                "nodes_count": len(filtered_nodes),
                "edges_count": len(edges),
                "top_nodes": sorted(
                    [(k, v.centrality_score) for k, v in filtered_nodes.items()],
                    key=lambda x: x[1], reverse=True
                )[:10],
                "message": f"Knowledge graph built with {len(filtered_nodes)} nodes and {len(edges)} edges"
            }
            
        except Exception as e:
            logger.error(f"Knowledge graph building failed: {e}")
            return {
                "status": "error",
                "message": f"Knowledge graph building failed: {str(e)}"
            }
    
    def get_knowledge_graph(self, domain: str) -> KnowledgeGraph:
        """Get knowledge graph for a domain."""
        return self.knowledge_graphs.get(domain)
    
    def list_domains(self) -> List[str]:
        """List all available domains."""
        return list(self.knowledge_graphs.keys())
    
    def get_graph_stats(self, domain: str) -> Dict[str, Any]:
        """Get statistics for a knowledge graph."""
        kg = self.knowledge_graphs.get(domain)
        if not kg:
            return {"status": "error", "message": f"No knowledge graph found for domain: {domain}"}
        
        centrality_scores = [node.centrality_score for node in kg.nodes.values()]
        
        return {
            "domain": domain,
            "nodes_count": len(kg.nodes),
            "edges_count": len(kg.edges),
            "centrality_stats": {
                "min": min(centrality_scores) if centrality_scores else 0,
                "max": max(centrality_scores) if centrality_scores else 0,
                "mean": sum(centrality_scores) / len(centrality_scores) if centrality_scores else 0
            },
            "created_at": kg.created_at,
            "version": kg.version
        }
    
    def save_graph(self, domain: str, output_path: str) -> bool:
        """Save knowledge graph to JSON file."""
        kg = self.knowledge_graphs.get(domain)
        if not kg:
            logger.error(f"No knowledge graph found for domain: {domain}")
            return False
        
        try:
            # Convert to dictionary
            graph_data = {
                "domain": kg.domain,
                "created_at": kg.created_at,
                "version": kg.version,
                "nodes": [
                    {
                        "id": node.id,
                        "label": node.label,
                        "node_type": node.node_type,
                        "centrality_score": node.centrality_score
                    }
                    for node in kg.nodes.values()
                ],
                "edges": [
                    {
                        "source": edge.source,
                        "target": edge.target,
                        "relation": edge.relation,
                        "weight": edge.weight
                    }
                    for edge in kg.edges
                ]
            }
            
            # Ensure output directory exists
            output_path_obj = Path(output_path)
            output_path_obj.parent.mkdir(parents=True, exist_ok=True)
            
            # Write to JSON file
            with open(output_path, 'w') as f:
                json.dump(graph_data, f, indent=2)
            
            logger.info(f"Knowledge graph saved to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save knowledge graph: {e}")
            return False
    
    def load_graph(self, input_path: str) -> bool:
        """Load knowledge graph from JSON file."""
        try:
            with open(input_path, 'r') as f:
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
            kg = KnowledgeGraph(
                nodes=nodes,
                edges=edges,
                domain=graph_data.get("domain", "unknown"),
                created_at=graph_data.get("created_at", str(datetime.now()))
            )
            
            # Store in memory
            self.knowledge_graphs[kg.domain] = kg
            
            logger.info(f"Knowledge graph loaded from {input_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load knowledge graph: {e}")
            return False
