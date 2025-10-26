# FastMCP Domain Intelligence Server

A clean, modular FastMCP server providing intelligent domain analysis tools.

## 🚀 Quick Start

### 1. Start the FastMCP Server
```bash
fastmcp run src/news_portal/mcp_tools/fastmcp_server.py:mcp --transport http --port 8002
```

### 2. Build the Knowledge Graph
```bash
# Build the pre-built knowledge graph (one-time setup)
python src/news_portal/mcp_tools/build_knowledge_graph.py

# View the knowledge graph
python src/news_portal/mcp_tools/view_knowledge_graph.py
```

### 3. Test the Tools
```bash
# Test all tools via client
python src/news_portal/mcp_tools/tests/fastmcp_client.py

# Test individual tools
python src/news_portal/mcp_tools/tests/test_keyword_extractor.py
python src/news_portal/mcp_tools/tests/test_glossary_builder.py

# Generate and view cover images
python src/news_portal/mcp_tools/tests/view_generated_images.py
```

## 📁 File Structure

### Core Files
- **`fastmcp_server.py`** - Main FastMCP server with all tools
- **`fastmcp_client.py`** - Client for testing all tools
- **`requirements_mcp.txt`** - Python dependencies

### MCP Tools
- **`mcp_tools_base.py`** - Base classes and shared utilities
- **`knowledge_graph_builder.py`** - Knowledge graph builder
- **`mcp_tools_keyword_extractor.py`** - Keyword extraction tool
- **`mcp_tools_glossary_builder.py`** - Glossary builder tool
- **`mcp_tools_cover_image_generator.py`** - Cover image generator

### Testing & Examples
- **`tests/`** - Test suite folder
  - **`fastmcp_client.py`** - Complete test suite for all FastMCP tools
  - **`test_keyword_extractor.py`** - Keyword extractor tests
  - **`test_glossary_builder.py`** - Comprehensive glossary builder tests
  - **`view_generated_images.py`** - Generate and view cover images
- **`generated_images/`** - Folder for generated images
- **`build_knowledge_graph.py`** - One-time utility to build and save knowledge graphs
- **`view_knowledge_graph.py`** - Utility to view knowledge graph structure

### Documentation
- **`FASTMCP_GUIDE.md`** - Detailed usage guide
- **`README.md`** - This file

## 🛠️ Available MCP Tools

1. **`extract_keywords`** - Extract high-centrality keywords using knowledge graphs
2. **`build_glossary`** - Create domain glossaries from knowledge graphs
3. **`generate_cover_image`** - Generate contextual cover images

Note: Knowledge graphs are pre-built using `build_knowledge_graph.py` and loaded at server startup.

## 🔧 Requirements

Install dependencies:
```bash
uv add fastmcp openai python-dotenv networkx scipy matplotlib requests
```

## 📝 Usage

The server provides 3 intelligent MCP tools that work together:
1. Extract important keywords based on graph centrality
2. Build a glossary of key terms with definitions
3. Generate contextual cover images using the knowledge graph

All tools share a pre-built knowledge graph loaded at server startup. The knowledge graph is built once using `build_knowledge_graph.py` and stored as JSON.
