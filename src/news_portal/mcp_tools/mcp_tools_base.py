#!/usr/bin/env python3
"""
Base MCP Tool Classes and Shared Utilities
==========================================

Common base classes and utilities for all Domain Intelligence MCP tools.
"""

import json
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod
import networkx as nx
import numpy as np
from openai import AsyncOpenAI
import requests

logger = logging.getLogger(__name__)

@dataclass
class KnowledgeGraphNode:
    """Represents a node in the knowledge graph."""
    id: str
    label: str
    centrality_score: float = 0.0
    node_type: str = "concept"
    metadata: Dict[str, Any] = None

@dataclass
class KnowledgeGraphEdge:
    """Represents an edge in the knowledge graph."""
    source: str
    target: str
    relation: str
    weight: float = 1.0
    metadata: Dict[str, Any] = None

@dataclass
class KnowledgeGraph:
    """Complete knowledge graph structure."""
    nodes: Dict[str, KnowledgeGraphNode]
    edges: List[KnowledgeGraphEdge]
    domain: str
    created_at: str
    version: str = "1.0"

class BaseMCPTool(ABC):
    """Base class for all MCP tools."""
    
    def __init__(self, openai_client: AsyncOpenAI = None):
        self.openai_client = openai_client or AsyncOpenAI()
        self.knowledge_graphs: Dict[str, KnowledgeGraph] = {}
    
    @abstractmethod
    def get_tool_definition(self) -> Dict[str, Any]:
        """Return the MCP tool definition."""
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool with given parameters."""
        pass
    
    def set_knowledge_graphs(self, knowledge_graphs: Dict[str, KnowledgeGraph]):
        """Set the knowledge graphs for this tool."""
        self.knowledge_graphs = knowledge_graphs

class GraphProcessor:
    """Utility class for graph processing operations."""
    
    @staticmethod
    async def calculate_centrality_measures(G: nx.DiGraph) -> Dict[str, float]:
        """Calculate centrality measures for graph nodes."""
        
        # Calculate multiple centrality measures with error handling
        try:
            eigenvector_centrality = nx.eigenvector_centrality(G, max_iter=1000)
        except nx.PowerIterationFailedConvergence:
            # Fallback to degree centrality if eigenvector fails
            eigenvector_centrality = nx.degree_centrality(G)
        
        betweenness_centrality = nx.betweenness_centrality(G)
        closeness_centrality = nx.closeness_centrality(G)
        pagerank = nx.pagerank(G)
        
        # Combine measures (weighted average)
        combined_scores = {}
        for node in G.nodes():
            combined_scores[node] = (
                0.4 * eigenvector_centrality.get(node, 0) +
                0.3 * betweenness_centrality.get(node, 0) +
                0.2 * closeness_centrality.get(node, 0) +
                0.1 * pagerank.get(node, 0)
            )
        
        return combined_scores
    
    @staticmethod
    def build_graph_from_triplets(triplets: List[tuple]) -> nx.DiGraph:
        """Build NetworkX graph from triplets."""
        G = nx.DiGraph()
        for source, relation, target in triplets:
            G.add_edge(source, target, relation=relation, weight=1.0)
        return G

class LLMProcessor:
    """Utility class for LLM operations."""
    
    def __init__(self, openai_client: AsyncOpenAI):
        self.client = openai_client
    
    async def generate_triplets_from_documents(
        self, 
        domain: str, 
        documents: List[str], 
        max_nodes: int
    ) -> List[tuple]:
        """Generate knowledge graph triplets from documents using LLM."""
        
        prompt = f"""
        You are a domain expert in {domain}. Analyze the following documents and extract knowledge graph triplets.
        
        Format: <entity1, relation, entity2>
        
        Examples:
        - <cancer, is_a, disease>
        - <chemotherapy, treats, cancer>
        - <tumor, located_in, lung>
        
        Extract {max_nodes} high-quality triplets that represent the core knowledge in this domain.
        Focus on:
        1. Hierarchical relationships (is_a, part_of, contains)
        2. Causal relationships (causes, treats, prevents)
        3. Spatial relationships (located_in, adjacent_to)
        4. Temporal relationships (precedes, follows)
        5. Functional relationships (enables, inhibits)
        
        Documents:
        {chr(10).join(documents[:5])}  # Limit to first 5 docs for prompt size
        
        Return only the triplets, one per line, in the format: <entity1, relation, entity2>
        """
        
        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=Config.MAX_PROMPT_TOKENS
        )
        
        # Parse triplets from response
        triplets = []
        for line in response.choices[0].message.content.split('\n'):
            line = line.strip()
            # Handle numbered format: "1. <entity, relation, object>"
            if line and '.' in line and '<' in line and '>' in line:
                # Extract the triplet part after the number
                triplet_part = line.split('.', 1)[1].strip()
                line = triplet_part
            
            if line.startswith('<') and line.endswith('>'):
                try:
                    content = line[1:-1]
                    parts = [p.strip() for p in content.split(',')]
                    if len(parts) == 3:
                        triplets.append((parts[0], parts[1], parts[2]))
                except:
                    continue
        
        return triplets[:max_nodes]
    
    async def extract_candidate_keywords(self, text: str) -> List[str]:
        """Extract candidate keywords using LLM."""
        
        prompt = f"""
        Extract the most important keywords and key phrases from the following text.
        Focus on:
        1. Technical terms and concepts
        2. Proper nouns (people, places, organizations)
        3. Domain-specific terminology
        4. Important concepts and ideas
        
        Text: {text[:Config.MAX_TEXT_LENGTH_FOR_ANALYSIS]}  # Limit text length
        
        Return only the keywords, one per line, without explanations.
        """
        
        response = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=500
        )
        
        keywords = [
            line.strip() for line in response.choices[0].message.content.split('\n')
            if line.strip() and len(line.strip()) > 2
        ]
        
        return keywords
    
    async def generate_definition(
        self, 
        term: str, 
        domain: str, 
        kg: KnowledgeGraph
    ) -> str:
        """Generate definition for a term using knowledge graph context."""
        
        # Find related nodes
        related_nodes = []
        for edge in kg.edges:
            if edge.source == term or edge.target == term:
                related_nodes.append(edge)
        
        prompt = f"""
        Generate a concise, accurate definition for the term "{term}" in the context of {domain}.
        
        Related concepts from knowledge graph:
        {chr(10).join([f"- {e.source} {e.relation} {e.target}" for e in related_nodes[:5]])}
        
        Provide a clear, professional definition suitable for a glossary.
        Keep it under 100 words.
        """
        
        response = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=150
        )
        
        return response.choices[0].message.content.strip()

class ImageProcessor:
    """Utility class for image processing operations."""
    
    @staticmethod
    async def download_and_encode_image(image_url: str) -> str:
        """Download image and encode as base64."""
        try:
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            
            # Convert to base64
            import base64
            image_base64 = base64.b64encode(response.content).decode('utf-8')
            return image_base64
            
        except Exception as e:
            logger.error(f"Image download failed: {e}")
            return ""
    
    @staticmethod
    def apply_content_guardrails(
        editorial_text: str, 
        domain: str, 
        context_analysis: Dict[str, Any]
    ) -> str:
        """Apply content guardrails for sensitive medical topics."""
        
        sensitive_keywords = [
            'death', 'dying', 'terminal', 'fatal', 'mortality',
            'pain', 'suffering', 'distress', 'trauma',
            'crisis', 'emergency', 'urgent'
        ]
        
        has_sensitive_content = any(
            keyword in editorial_text.lower() 
            for keyword in sensitive_keywords
        )
        
        if has_sensitive_content:
            return """
            IMPORTANT GUARDRAILS:
            - Use hopeful, supportive visual tone
            - Avoid dark or depressing imagery
            - Focus on treatment, care, and hope
            - Use warm, professional colors
            - Emphasize healing and progress
            """
        else:
            return """
            Standard Guidelines:
            - Professional, clean aesthetic
            - Appropriate for healthcare domain
            - Focus on innovation and progress
            """
    
    @staticmethod
    def generate_visual_elements(
        domain: str, 
        context_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate domain-specific visual elements."""
        
        domain_visuals = {
            "oncology": [
                "molecular structures", "DNA helix", "cell division", 
                "medical research", "laboratory equipment", "treatment symbols"
            ],
            "medicine": [
                "medical symbols", "stethoscope", "cross", 
                "healthcare professionals", "medical equipment"
            ],
            "research": [
                "microscopes", "laboratory", "data visualization", 
                "scientific charts", "research equipment"
            ],
            "technology": [
                "circuit patterns", "digital elements", "network connections",
                "innovation symbols", "tech interfaces"
            ]
        }
        
        base_elements = domain_visuals.get(domain, ["professional symbols", "domain-specific imagery"])
        
        # Add context-specific elements
        if context_analysis.get('mood') == 'hopeful':
            base_elements.extend(["light rays", "growth symbols", "positive imagery"])
        elif context_analysis.get('mood') == 'innovative':
            base_elements.extend(["innovation symbols", "breakthrough imagery", "future concepts"])
        
        return base_elements[:4]  # Limit to 4 elements

class Config:
    """Configuration constants for all tools."""
    
    # Default values
    DEFAULT_MAX_NODES = 1000
    DEFAULT_MIN_CENTRALITY = 0.1
    DEFAULT_MAX_KEYWORDS = 10
    DEFAULT_MAX_GLOSSARY_TERMS = 50
    DEFAULT_MAX_CANDIDATE_KEYWORDS = 15
    DEFAULT_MIN_CENTRALITY_THRESHOLD = 0.05
    
    # Centrality weights
    CENTRALITY_WEIGHTS = {
        "eigenvector": 0.4,
        "betweenness": 0.3,
        "closeness": 0.2,
        "pagerank": 0.1
    }
    
    # Image generation settings
    DEFAULT_IMAGE_SIZE = "1024x1024"
    DEFAULT_IMAGE_QUALITY = "standard"
    SUPPORTED_ENGINES = ["dall-e-3"]  # Only implemented engines
    
    # Style options
    SUPPORTED_STYLES = ["professional", "academic", "modern", "minimalist"]
    
    # Text processing limits
    MAX_TEXT_LENGTH_FOR_ANALYSIS = 2000
    MAX_CONTENT_LENGTH_FOR_SUMMARY = 4000
    MAX_PROMPT_TOKENS = 4000
