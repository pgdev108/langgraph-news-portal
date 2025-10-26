# Testing Guide for MCP Tools

This guide explains how to test the MCP tools (Keyword Extractor, Cover Image Generator, and Glossary Builder).

## Prerequisites

1. **Pre-built Knowledge Graph**: The server requires a pre-built knowledge graph for "cancer health care" domain.

   To create it, run:
   ```bash
   uv run python src/news_portal/mcp_tools/build_knowledge_graph.py
   ```

   This creates: `src/news_portal/mcp_tools/knowledge_graphs/cancer_health_care.json`

2. **Environment Variables**: Ensure you have a `.env` file with:
   ```
   OPENAI_API_KEY=your-key-here
   CLOUDINARY_CLOUD_NAME=your-cloud-name
   CLOUDINARY_API_KEY=your-api-key
   CLOUDINARY_API_SECRET=your-api-secret
   ```

## Testing Options

### Option 1: Test via FastMCP Server (Recommended)

This tests the tools as they would be used in production, through the FastMCP server.

#### Step 1: Start the FastMCP Server

In one terminal, run:

```bash
fastmcp run src/news_portal/mcp_tools/fastmcp_server.py:mcp --transport http --port 8002
```

You should see output like:
```
🚀 Starting FastMCP Domain Intelligence Server...
==================================================
Available tools:
  - generate_cover_image: Generate contextual cover images
  - extract_keywords: Extract high-centrality keywords
  - build_glossary: Build domain glossaries
==================================================
ℹ️  Note: Knowledge graph is pre-built and loaded at startup
📊 Loading pre-built knowledge graph from: ...
✅ Loaded knowledge graph with X nodes and Y edges
```

#### Step 2: Run Tests

In another terminal, run any of these tests:

**Keyword Extractor:**
```bash
python test_keyword_extractor_mcp.py
```

**Glossary Builder:**
```bash
uv run python src/news_portal/mcp_tools/tests/test_glossary_builder.py
```

**Cover Image Generator:**
```bash
# Use the cover image generation integration with the news portal
```

### Option 2: Test Tools Directly

You can also test tools directly without the FastMCP server.

#### Keyword Extractor Test:

```bash
uv run python src/news_portal/mcp_tools/tests/test_keyword_extractor.py
```

This test:
- Loads the pre-built knowledge graph
- Tests keyword extraction with various scenarios
- Tests different centrality thresholds
- Tests edge cases

#### Glossary Builder Test:

```bash
uv run python src/news_portal/mcp_tools/tests/test_glossary_builder.py
```

This test:
- Loads the pre-built knowledge graph
- Builds glossaries with different parameters
- Tests via FastMCP server
- Tests different centrality thresholds

## Available Tools

### 1. `extract_keywords`

Extract high-centrality keywords from text using the knowledge graph.

**Example via FastMCP Client:**
```python
result = await client.call_tool("extract_keywords", {
    "text": "Your text here...",
    "domain": "cancer health care",
    "max_keywords": 10,
    "min_centrality": 0.05
})
```

### 2. `build_glossary`

Build a glossary from the knowledge graph.

**Example via FastMCP Client:**
```python
result = await client.call_tool("build_glossary", {
    "domain": "cancer health care",
    "max_terms": 20,
    "min_centrality": 0.1,
    "include_definitions": True
})
```

### 3. `generate_cover_image`

Generate contextual cover images (requires OpenAI API).

**Example via FastMCP Client:**
```python
result = await client.call_tool("generate_cover_image", {
    "editorial_text": "Your editorial text...",
    "domain": "cancer health care",
    "style": "professional",
    "dimensions": "1792x1024",
    "image_engine": "dall-e-3"
})
```

## Troubleshooting

### Server Won't Start

1. Check that `OPENAI_API_KEY` is set in your `.env` file
2. Check that port 8002 is not already in use
3. Verify the pre-built knowledge graph exists

### Graph Not Found

If you see "Knowledge graph not found", run:

```bash
uv run python src/news_portal/mcp_tools/build_knowledge_graph.py
```

### Connection Errors

If you get connection errors when testing:

1. Make sure the FastMCP server is running in another terminal
2. Verify the server URL: `http://localhost:8002/mcp`
3. Check that the server is listening on the correct port

### No Keywords Extracted

If the keyword extractor returns 0 keywords:

1. The test text might not match nodes in the knowledge graph
2. Try lowering the `min_centrality` threshold
3. Make sure you're using the correct domain ("cancer health care" or "cancer_care")

## Test Data

The pre-built knowledge graph for "cancer health care" includes nodes and edges covering:
- Cancer treatment options (surgery, chemotherapy, radiation, etc.)
- Precision medicine and personalized treatment
- Early detection and screening
- Immunotherapy and targeted therapies
- Oncology specialties (medical, surgical, radiation)
- Care types (palliative, supportive, hospice)
- Research and drug development
- Biomarkers and genetic testing

## Integration with News Portal

The MCP tools are integrated with the news portal via:

1. **`mcp_client_service.py`**: Service for calling MCP tools from agents
2. **`graph.py`**: Chief Editor agent calls `generate_portal_cover_image`
3. **`main.py`**: Streamlit UI displays the generated cover image

To test the full integration:

```bash
streamlit run src/news_portal/main.py
```

Then trigger the news generation workflow from the UI.
