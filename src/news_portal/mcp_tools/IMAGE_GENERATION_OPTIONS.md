# Image Generation Options - DALL-E Alternatives

## Overview
This document outlines alternative image generation engines you can use instead of DALL-E.

## Available Options

### 1. Stability AI API (Recommended)
**SDK:** `stability-sdk`  
**API:** https://platform.stability.ai  
**Pros:** Excellent quality, reasonable pricing, easy integration  
**Cons:** Requires API key  

**Installation:**
```bash
uv add stability-sdk
```

**Configuration:**
Add to `.env`:
```
STABILITY_API_KEY=sk-your-key-here
```

**Usage:**
The tool supports `engine="stability-ai"` parameter.

### 2. Replicate API
**SDK:** `replicate`  
**Models:** stability-ai/sdxl, black-forest-labs/flux  
**Pros:** Access to multiple models, pay-per-use  
**Cons:** Requires API key, variable pricing  

**Installation:**
```bash
uv add replicate
```

**Configuration:**
Add to `.env`:
```
REPLICATE_API_TOKEN=r8_your_token_here
```

**Usage:**
The tool supports `engine="replicate"` parameter.

### 3. Static Placeholder Images
**Service:** Unsplash or Pexels  
**Pros:** Free, instant, no generation time  
**Cons:** Limited customization, not AI-generated  

**Installation:**
```bash
uv add requests
```

**Usage:**
The tool supports `engine="placeholder"` parameter which fetches relevant images from Unsplash.

### 4. Hugging Face Transformers (Local)
**SDK:** `diffusers`, `transformers`  
**Pros:** Free, fully local, complete control  
**Cons:** Requires GPU, slower, more setup  

**Installation:**
```bash
uv add diffusers torch pillow
```

**Usage:**
The tool supports `engine="huggingface"` parameter for local generation.

## Implementation Priority

### Phase 1: Stability AI API (Easiest)
- Most similar to DALL-E API
- Best quality-to-effort ratio
- Direct replacement

### Phase 2: Placeholder Images (Fallback)
- Zero generation time
- Always available
- Good for demos

### Phase 3: Replicate API (Optional)
- Access to latest models
- Multiple model options

### Phase 4: Local Generation (Advanced)
- No API costs
- Full control
- Requires GPU setup

## Next Steps

1. Tell me which option you want to implement
2. I'll add the implementation to the cover image generator
3. We can test it together

## Switching Engines

After implementation, you can switch engines via the `image_engine` parameter:

```python
# Stability AI
result = await client.call_tool("generate_cover_image", {
    "editorial_text": "...",
    "image_engine": "stability-ai",
    ...
})

# Replicate
result = await client.call_tool("generate_cover_image", {
    "editorial_text": "...",
    "image_engine": "replicate",
    ...
})

# Placeholder (instant)
result = await client.call_tool("generate_cover_image", {
    "editorial_text": "...",
    "image_engine": "placeholder",
    ...
})
```

## Cost Comparison

| Engine | Cost | Quality | Speed | Setup |
|--------|------|---------|-------|-------|
| DALL-E 3 | ~$0.04/image | ⭐⭐⭐⭐⭐ | Fast | Easy |
| Stability AI | ~$0.03/image | ⭐⭐⭐⭐ | Fast | Easy |
| Replicate | ~$0.01-0.05/image | ⭐⭐⭐⭐⭐ | Fast | Easy |
| Placeholder | $0 | N/A | Instant | Very Easy |
| Local | $0 | ⭐⭐⭐ | Slow | Complex |

