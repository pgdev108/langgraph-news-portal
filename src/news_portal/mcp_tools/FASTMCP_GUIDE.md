# FastMCP Server Guide

## Overview

This guide shows how to use the FastMCP server for domain intelligence tools, including cover image generation, knowledge graph building, keyword extraction, and glossary building.

## Quick Start

### 1. Start the FastMCP Server

```bash
# In one terminal, start the server
fastmcp run src/news_portal/mcp_tools/fastmcp_server.py:mcp --transport http --port 8000
```

The server will start and listen on `http://localhost:8000`. You should see output like:

```
🚀 Starting FastMCP Domain Intelligence Server...
==================================================
Available tools:
  - generate_cover_image: Generate contextual cover images
  - build_knowledge_graph: Build domain knowledge graphs
  - extract_keywords: Extract high-centrality keywords
  - build_glossary: Build domain glossaries
==================================================
```

### 2. Test the Server

```bash
# In another terminal, run the test client
python src/news_portal/mcp/fastmcp_client.py
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

### 2. `build_knowledge_graph`

Build domain-specific knowledge graphs from documents.

**Parameters:**
- `domain` (str): The domain name
- `documents` (list): List of documents to analyze
- `max_nodes` (int, optional): Maximum nodes (default: 50)
- `min_centrality` (float, optional): Minimum centrality threshold (default: 0.05)

**Example:**
```python
result = await client.call_tool(
    "build_knowledge_graph",
    {
        "domain": "cancer_care",
        "documents": [
            "Precision oncology uses molecular profiling...",
            "Immunotherapy harnesses the immune system..."
        ],
        "max_nodes": 20,
        "min_centrality": 0.05
    }
)
```

### 3. `extract_keywords`

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

### 4. `build_glossary`

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
    client = Client("http://localhost:8000/mcp")
    
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

### Pre-loaded Test Knowledge Graph

The server comes with a pre-loaded test knowledge graph for the "cancer_care" domain, so you can test cover image generation immediately without building a knowledge graph first.

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
2. Make sure port 8000 is not already in use
3. Check that all dependencies are installed: `uv add fastmcp`

### Client Can't Connect

1. Make sure the server is running: `fastmcp run src/news_portal/mcp_tools/fastmcp_server.py:mcp --transport http --port 8000`
2. Check that the server is listening on `http://localhost:8000`
3. Verify the client URL matches: `Client("http://localhost:8000/mcp")`

### Tool Errors

1. Check the server logs for detailed error messages
2. Verify that the knowledge graph is built before using tools that depend on it
3. Make sure all required parameters are provided

## Advanced Usage

### Custom Knowledge Graph

```python
# First build a knowledge graph
kg_result = await client.call_tool("build_knowledge_graph", {
    "domain": "finance",
    "documents": ["Your financial documents..."],
    "max_nodes": 30
})

# Then use it for other tools
if kg_result.get('status') == 'success':
    keywords = await client.call_tool("extract_keywords", {
        "text": "Your text here...",
        "domain": "finance"
    })
```

### Multiple Domains

You can work with multiple domains by building separate knowledge graphs:

```python
# Build knowledge graphs for different domains
await client.call_tool("build_knowledge_graph", {
    "domain": "cancer_care",
    "documents": cancer_docs
})

await client.call_tool("build_knowledge_graph", {
    "domain": "finance", 
    "documents": finance_docs
})

# Use domain-specific tools
cancer_image = await client.call_tool("generate_cover_image", {
    "editorial_text": cancer_text,
    "domain": "cancer_care"
})

finance_image = await client.call_tool("generate_cover_image", {
    "editorial_text": finance_text,
    "domain": "finance"
})
```

## Benefits of FastMCP

1. **Simple Setup**: Just run `fastmcp run` command
2. **HTTP Transport**: Easy to connect to from any client
3. **Persistent Server**: Stays running until you stop it
4. **Clean API**: Simple tool calling interface
5. **Error Handling**: Built-in error handling and logging
6. **Scalable**: Can handle multiple concurrent clients

This approach is much simpler than the complex MCP stdio setup and provides the persistent server behavior you wanted!
