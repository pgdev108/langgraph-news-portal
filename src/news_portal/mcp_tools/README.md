# FastMCP Domain Intelligence Server

A clean, modular FastMCP server providing intelligent domain analysis tools.

## 🚀 Quick Start

### 1. Start the FastMCP Server
```bash
fastmcp run src/news_portal/mcp_tools/fastmcp_server.py:mcp --transport http --port 8002
```

### 2. Test the Tools
```bash
# Test all tools via client
python src/news_portal/mcp/tests/fastmcp_client.py

# Test individual tools
python src/news_portal/mcp/tests/test_knowledge_graph_builder.py
python src/news_portal/mcp/tests/test_keyword_extractor.py
python src/news_portal/mcp/tests/test_glossary_builder.py

# Generate and view cover images
python src/news_portal/mcp/tests/view_generated_images.py
```

## 📁 File Structure

### Core Files
- **`fastmcp_server.py`** - Main FastMCP server with all tools
- **`fastmcp_client.py`** - Client for testing all tools
- **`requirements_mcp.txt`** - Python dependencies

### MCP Tools
- **`mcp_tools_base.py`** - Base classes and shared utilities
- **`mcp_tools_knowledge_graph.py`** - Knowledge graph builder
- **`mcp_tools_keyword_extractor.py`** - Keyword extraction tool
- **`mcp_tools_glossary_builder.py`** - Glossary builder tool
- **`mcp_tools_cover_image_generator.py`** - Cover image generator

### Testing & Examples
- **`tests/`** - Test suite folder
  - **`fastmcp_client.py`** - Complete test suite for all FastMCP tools
  - **`test_knowledge_graph_builder.py`** - Knowledge graph builder tests
  - **`test_keyword_extractor.py`** - Keyword extractor tests
  - **`test_glossary_builder.py`** - Comprehensive glossary builder tests
  - **`view_generated_images.py`** - Generate and view cover images
- **`generated_images/`** - Folder for generated images

### Documentation
- **`FASTMCP_GUIDE.md`** - Detailed usage guide
- **`README.md`** - This file

## 🛠️ Available Tools

1. **`build_knowledge_graph`** - Build domain knowledge graphs from documents
2. **`extract_keywords`** - Extract high-centrality keywords using knowledge graphs
3. **`build_glossary`** - Create domain glossaries from knowledge graphs
4. **`generate_cover_image`** - Generate contextual cover images

## 🔧 Requirements

Install dependencies:
```bash
uv add fastmcp openai python-dotenv networkx scipy matplotlib requests
```

## 📝 Usage

The server provides 4 intelligent tools that work together:
1. Build a knowledge graph from your documents
2. Extract important keywords based on graph centrality
3. Build a glossary of key terms with definitions
4. Generate contextual cover images using the knowledge graph

All tools share knowledge graphs automatically through the FastMCP server.
