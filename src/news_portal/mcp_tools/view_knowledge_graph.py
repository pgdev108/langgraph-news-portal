#!/usr/bin/env python3
"""
View Knowledge Graph
====================

Utility to view the pre-built knowledge graph with nodes, edges, and statistics.
"""

import json
from pathlib import Path
from collections import defaultdict

def view_knowledge_graph():
    """Load and display the pre-built knowledge graph."""
    
    # Load the knowledge graph
    graph_file = Path(__file__).parent / "knowledge_graphs" / "cancer_health_care.json"
    
    if not graph_file.exists():
        print(f"❌ Knowledge graph not found at: {graph_file}")
        print("\nTo create it, run:")
        print("  uv run python src/news_portal/mcp_tools/build_knowledge_graph.py")
        return
    
    print(f"📊 Loading knowledge graph from: {graph_file}")
    with open(graph_file, 'r') as f:
        kg_data = json.load(f)
    
    # Display metadata
    print("\n" + "=" * 60)
    print("📋 Knowledge Graph Metadata")
    print("=" * 60)
    print(f"Domain: {kg_data.get('domain', 'N/A')}")
    print(f"Created: {kg_data.get('created_at', 'N/A')}")
    print(f"Version: {kg_data.get('version', 'N/A')}")
    
    # Display nodes
    nodes = kg_data.get('nodes', [])
    print("\n" + "=" * 60)
    print(f"📊 Nodes ({len(nodes)} total)")
    print("=" * 60)
    
    # Sort nodes by centrality
    sorted_nodes = sorted(nodes, key=lambda x: x.get('centrality_score', 0), reverse=True)
    
    print("\nTop Nodes (by Centrality):")
    for i, node in enumerate(sorted_nodes, 1):
        centrality = node.get('centrality_score', 0)
        node_id = node.get('id', 'N/A')
        node_type = node.get('node_type', 'N/A')
        print(f"  {i:2d}. {node_id:30s} (centrality: {centrality:.4f}, type: {node_type})")
    
    # Display edges
    edges = kg_data.get('edges', [])
    print("\n" + "=" * 60)
    print(f"🔗 Edges ({len(edges)} total)")
    print("=" * 60)
    
    # Count edges per source node
    edge_counts = defaultdict(int)
    for edge in edges:
        source = edge.get('source', 'N/A')
        edge_counts[source] += 1
    
    print("\nTop Connected Nodes:")
    sorted_connections = sorted(edge_counts.items(), key=lambda x: x[1], reverse=True)
    for node, count in sorted_connections:
        print(f"  {node:30s} ({count} connections)")
    
    # Show sample edges
    print("\n" + "-" * 60)
    print("Sample Edges (showing first 10):")
    print("-" * 60)
    for i, edge in enumerate(edges[:10], 1):
        source = edge.get('source', 'N/A')
        target = edge.get('target', 'N/A')
        edge_type = edge.get('edge_type', 'related_to')
        weight = edge.get('weight', 1.0)
        print(f"  {i:2d}. {source:25s} --[{edge_type}]--> {target:25s} (weight: {weight:.2f})")
    
    if len(edges) > 10:
        print(f"\n  ... and {len(edges) - 10} more edges")
    
    # Network statistics
    print("\n" + "=" * 60)
    print("📈 Network Statistics")
    print("=" * 60)
    
    # Calculate average degree
    if nodes:
        avg_degree = len(edges) * 2 / len(nodes)
        print(f"Average Degree (connections per node): {avg_degree:.2f}")
    
    # Find nodes with highest centrality
    centrality_scores = [node.get('centrality_score', 0) for node in nodes]
    if centrality_scores:
        print(f"Highest Centrality: {max(centrality_scores):.4f}")
        print(f"Lowest Centrality: {min(centrality_scores):.4f}")
        print(f"Average Centrality: {sum(centrality_scores)/len(centrality_scores):.4f}")
    
    # Find most connected nodes
    print(f"\nMost Connected Node: {sorted_connections[0][0]} ({sorted_connections[0][1]} connections)")
    
    # Edge type distribution
    edge_types = defaultdict(int)
    for edge in edges:
        edge_type = edge.get('edge_type', 'related_to')
        edge_types[edge_type] += 1
    
    print("\nEdge Type Distribution:")
    for edge_type, count in sorted(edge_types.items(), key=lambda x: x[1], reverse=True):
        print(f"  {edge_type:20s}: {count} edges")

if __name__ == "__main__":
    try:
        view_knowledge_graph()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
