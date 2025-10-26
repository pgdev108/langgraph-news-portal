# FastMCP Server Guide

## Overview

This guide shows how to use the FastMCP server for domain intelligence tools, including cover image generation, knowledge graph building, keyword extraction, and glossary building.

## Quick Start

### 1. Start the FastMCP Server

```bash
# In one terminal, start the server
fastmcp run src/news_portal/mcp_tools/fastmcp_server.py:mcp --transport http --port 8002
```

The server will start and listen on `http://localhost:8002`. You should see output like:

```
🚀 Starting FastMCP Domain Intelligence Server...
==================================================
Available tools:
  - generate_cover_image: Generate contextual cover images
  - extract_keywords: Extract high-centrality keywords
  - build_glossary: Build domain glossaries
==================================================
ℹ️  Note: Knowledge graph is pre-built and loaded at startup
==================================================
```

### 2. Test the Server

```bash
# In another terminal, run the test client
python src/news_portal/mcp_tools/tests/test_article_cover.py
```

## Available Tools

### 1. `generate_cover_image`

Generate contextual cover images using knowledge graph insights.

**Parameters:**
- `editorial_text` (str): The editorial text to analyze
- `domain` (str, optional): Domain context (default: "cancer_care")
- `style` (str, optional): Image style (default: "professional")
- `dimensions` (str, optional): Image dimensions (default: "1024x1024")
- `image_engine` (str, optional): Image engine (default: "dall-e-3")

**Example:**
```python
result = await client.call_tool(
    "generate_cover_image",
    {
        "editorial_text": "The future of cancer care is being transformed...",
        "domain": "cancer_care",
        "style": "professional",
        "dimensions": "1024x1024",
        "image_engine": "dall-e-3"
    }
)
```

### 2. `extract_keywords`

Extract high-centrality keywords from text using knowledge graph.

**Parameters:**
- `text` (str): The text to analyze
- `domain` (str, optional): Domain context (default: "cancer_care")
- `max_keywords` (int, optional): Maximum keywords (default: 10)
- `min_centrality` (float, optional): Minimum centrality threshold (default: 0.05)

**Example:**
```python
result = await client.call_tool(
    "extract_keywords",
    {
        "text": "Precision oncology and immunotherapy...",
        "domain": "cancer_care",
        "max_keywords": 5,
        "min_centrality": 0.05
    }
)
```

### 3. `build_glossary`

Build high-value glossaries from knowledge graph nodes.

**Parameters:**
- `domain` (str, optional): Domain context (default: "cancer_care")
- `max_terms` (int, optional): Maximum terms (default: 20)
- `min_centrality` (float, optional): Minimum centrality threshold (default: 0.1)

**Example:**
```python
result = await client.call_tool(
    "build_glossary",
    {
        "domain": "cancer_care",
        "max_terms": 20,
        "min_centrality": 0.1
    }
)
```

## Client Usage

### Basic Client Setup

```python
from fastmcp import Client

async def test_tool():
    client = Client("http://localhost:8002/mcp")
    
    async with client:
        result = await client.call_tool("generate_cover_image", {
            "editorial_text": "Your editorial text here...",
            "domain": "cancer_care"
        })
        
        print(f"Result: {result}")

# Run the test
import asyncio
asyncio.run(test_tool())
```

### Error Handling

```python
try:
    result = await client.call_tool("generate_cover_image", params)
    if result.get('status') == 'success':
        print(f"✅ Success: {result.get('image_url')}")
    else:
        print(f"❌ Error: {result.get('message')}")
except Exception as e:
    print(f"❌ Connection error: {e}")
```

## Server Features

### Pre-built Knowledge Graph

The server comes with a pre-built knowledge graph for the "cancer health care" domain. This graph is loaded automatically at server startup from `src/news_portal/mcp_tools/knowledge_graphs/cancer_health_care.json`.

To rebuild the knowledge graph (e.g., after updating domain documents), run:

```bash
uv run python src/news_portal/mcp_tools/build_knowledge_graph.py
```

This generates a fresh knowledge graph and saves it to the JSON file for future use.

### Environment Variables

Make sure you have `OPENAI_API_KEY` set in your `.env` file:

```bash
OPENAI_API_KEY=your-openai-api-key-here
```

### Logging

The server logs all operations to stderr, so it won't interfere with the MCP protocol.

## Troubleshooting

### Server Won't Start

1. Check that `OPENAI_API_KEY` is set in your `.env` file
2. Make sure port 8002 is not already in use
3. Check that all dependencies are installed: `uv add fastmcp`
4. Verify that the pre-built knowledge graph exists at `src/news_portal/mcp_tools/knowledge_graphs/cancer_health_care.json`

### Client Can't Connect

1. Make sure the server is running: `fastmcp run src/news_portal/mcp_tools/fastmcp_server.py:mcp --transport http --port 8002`
2. Check that the server is listening on `http://localhost:8002`
3. Verify the client URL matches: `Client("http://localhost:8002/mcp")`

### Tool Errors

1. Check the server logs for detailed error messages
2. Verify that the pre-built knowledge graph file exists at `src/news_portal/mcp_tools/knowledge_graphs/cancer_health_care.json`
3. Make sure all required parameters are provided

## Advanced Usage

### Using the Pre-built Graph

The knowledge graph is automatically loaded at server startup. The current implementation supports the "cancer health care" domain, which is also accessible via the "cancer_care" alias for backward compatibility.

### Extending to Multiple Domains

To add support for additional domains, you would need to:

1. Update `build_knowledge_graph.py` with documents for the new domain
2. Run the build script to generate a new JSON file
3. Update the `load_knowledge_graph()` function in `fastmcp_server.py` to load the new domain's graph

Example for adding a finance domain:

```python
# In build_knowledge_graph.py, add finance documents and build:
finance_docs = ["..."]

# Build the graph
kg = build_knowledge_graph_for_domain("finance", finance_docs)

# Save it
save_graph_to_json(kg, "knowledge_graphs/finance.json")
```

## Benefits of FastMCP

1. **Simple Setup**: Just run `fastmcp run` command
2. **HTTP Transport**: Easy to connect to from any client
3. **Persistent Server**: Stays running until you stop it
4. **Clean API**: Simple tool calling interface
5. **Error Handling**: Built-in error handling and logging
6. **Scalable**: Can handle multiple concurrent clients

This approach is much simpler than the complex MCP stdio setup and provides the persistent server behavior you wanted!
