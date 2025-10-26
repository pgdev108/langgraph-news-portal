#!/usr/bin/env python3
"""
Build Knowledge Graph
====================

One-time utility to build and save a knowledge graph for the 'cancer health care' domain.
This is NOT an MCP tool - it's a standalone utility script.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from news_portal.mcp_tools.knowledge_graph_builder import KnowledgeGraphBuilderTool

# Load environment variables
load_dotenv()

def build_and_save_knowledge_graph():
    """Build and save the knowledge graph for cancer health care."""
    
    print("Building knowledge graph for 'cancer health care' domain...")
    
    # Domain documents for cancer health care
    documents = [
        """
        Cancer is a group of diseases characterized by uncontrolled growth and spread of abnormal cells.
        Cancer cells can invade surrounding tissues and metastasize to distant parts of the body.
        Early detection and treatment significantly improve patient outcomes.
        Treatment options include surgery, chemotherapy, radiation therapy, immunotherapy, targeted therapy, and hormone therapy.
        """,
        """
        Cancer screening tests help detect cancer before symptoms appear.
        Common screening tests include mammograms for breast cancer, colonoscopies for colorectal cancer,
        and PSA tests for prostate cancer. Genetic testing can identify inherited cancer risk.
        Lifestyle factors like smoking, diet, and exercise influence cancer risk.
        """,
        """
        Oncology is the branch of medicine that deals with cancer diagnosis, treatment, and research.
        Medical oncologists specialize in chemotherapy and immunotherapy treatments.
        Surgical oncologists perform cancer-related surgeries.
        Radiation oncologists administer radiation therapy.
        """,
        """
        Palliative care focuses on improving quality of life for patients with serious illnesses.
        Supportive care addresses symptoms and side effects of cancer and its treatment.
        Hospice care provides end-of-life support for terminal cancer patients.
        Mental health support is crucial for cancer patients and their families.
        """,
        """
        Research in cancer includes clinical trials, biomarker discovery, and drug development.
        Precision medicine tailors treatment based on individual genetic profiles.
        Immunotherapy harnesses the immune system to fight cancer.
        CAR-T cell therapy is an emerging treatment for certain blood cancers.
        """
    ]
    
    # Initialize the builder
    from news_portal.mcp_tools.knowledge_graph_builder import KnowledgeGraphBuilderTool
    builder = KnowledgeGraphBuilderTool()
    
    # Build the knowledge graph
    import asyncio
    result = asyncio.run(builder.execute(
        domain="cancer health care",
        documents=documents,
        max_nodes=50,
        min_centrality=0.01
    ))
    
    if result.get("status") == "success":
        print(f"\n✓ Knowledge graph built successfully!")
        print(f"  Nodes: {result['nodes_count']}")
        print(f"  Edges: {result['edges_count']}")
        print(f"\nTop nodes:")
        for node, score in result['top_nodes']:
            print(f"  - {node} (centrality: {score:.3f})")
        
        # Save the graph
        output_dir = Path(__file__).parent / "knowledge_graphs"
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / "cancer_health_care.json"
        
        success = builder.save_graph("cancer health care", str(output_path))
        
        if success:
            print(f"\n✓ Graph saved to: {output_path}")
            print(f"\nTo use this graph, restart the FastMCP server:")
            print(f"  fastmcp run src/news_portal/mcp_tools/fastmcp_server.py:mcp --transport http --port 8002")
        else:
            print("\n✗ Failed to save graph")
            sys.exit(1)
    else:
        print(f"\n✗ Failed to build knowledge graph: {result.get('message')}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        import os
        if not os.getenv("OPENAI_API_KEY"):
            print("❌ OPENAI_API_KEY not found in environment variables!")
            sys.exit(1)
        
        build_and_save_knowledge_graph()
    except Exception as e:
        print(f"\n✗ Failed to build knowledge graph: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
