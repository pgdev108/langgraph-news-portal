#!/usr/bin/env python3
"""
LangGraph PNG Generator

Simple script to generate LangGraph structure and save as PNG file
using the built-in draw_mermaid_png() method.
"""

import sys
from pathlib import Path

# Add the current directory to the Python path (since we're now in src/news_portal)
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def main():
    """Generate LangGraph structure and save as PNG."""
    try:
        from graph import build_graph
        
        # Build the graph
        graph = build_graph()
        
        # Generate PNG using LangGraph's built-in method
        png_data = graph.get_graph().draw_mermaid_png()
        
        # Save PNG file in current directory (src/news_portal)
        png_path = current_dir / "langgraph_structure.png"
        
        with open(png_path, "wb") as f:
            f.write(png_data)
        
        print(f"✅ LangGraph structure saved as PNG: {png_path}")
        print("🎉 Done!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
