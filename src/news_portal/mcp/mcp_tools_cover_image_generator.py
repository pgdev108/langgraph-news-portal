#!/usr/bin/env python3
"""
Cover Image Generator MCP Tool
===============================

Tool for generating contextually relevant cover images using Tool-externally, Agent-internally pattern.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

import cloudinary
import cloudinary.uploader

# Configure Cloudinary immediately at module level
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME', ''),
    api_key=os.getenv('CLOUDINARY_API_KEY', ''),
    api_secret=os.getenv('CLOUDINARY_API_SECRET', '')
)

from .mcp_tools_base import (
    BaseMCPTool, KnowledgeGraph, LLMProcessor, ImageProcessor, Config
)

logger = logging.getLogger(__name__)

class CoverImageGeneratorTool(BaseMCPTool):
    """MCP Tool for generating contextually relevant cover images."""
    
    def __init__(self, openai_client=None):
        super().__init__(openai_client)
        self.llm_processor = LLMProcessor(self.openai_client)
        self.image_processor = ImageProcessor()
        
        # Create generated_images directory
        self.generated_images_dir = Path("generated_images")
        self.generated_images_dir.mkdir(exist_ok=True)
    
    def _setup_cloudinary(self):
        """Setup Cloudinary configuration - no longer needed, configured at module level."""
        pass  # Cloudinary is now configured at module import time
    
    
    def _upload_to_cloudinary(self, local_image_path: str) -> str:
        """
        Upload image to Cloudinary and return the secure URL.
        
        Args:
            local_image_path: Path to the local image file
            
        Returns:
            Cloudinary secure URL or local path if upload fails
        """
        try:
            logger.info(f"Uploading image to Cloudinary: {local_image_path}")
            response = cloudinary.uploader.upload(local_image_path)
            cloudinary_url = response['secure_url']
            logger.info(f"✅ Image uploaded to Cloudinary: {cloudinary_url}")
            return cloudinary_url
        except Exception as e:
            logger.error(f"❌ Failed to upload to Cloudinary: {e}")
            return local_image_path  # Fallback to local path
    
    def _save_image_locally(self, image_data: str, dimensions: str) -> str:
        """
        Save image data to local file in generated_images folder.
        
        Args:
            image_data: Image data as base64 string
            dimensions: Image dimensions for filename
            
        Returns:
            Local file path
        """
        try:
            # Generate filename with timestamp and dimensions
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"cover_image_{dimensions}_{timestamp}.png"
            local_path = self.generated_images_dir / filename
            
            # Convert base64 string back to bytes and save
            import base64
            image_bytes = base64.b64decode(image_data)
            
            with open(local_path, 'wb') as f:
                f.write(image_bytes)
            
            logger.info(f"✅ Image saved locally: {local_path}")
            return str(local_path)
            
        except Exception as e:
            logger.error(f"❌ Failed to save image locally: {e}")
            # Create a fallback filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            fallback_path = self.generated_images_dir / f"cover_image_{timestamp}.png"
            try:
                import base64
                image_bytes = base64.b64decode(image_data)
                with open(fallback_path, 'wb') as f:
                    f.write(image_bytes)
                return str(fallback_path)
            except Exception as fallback_error:
                logger.error(f"❌ Fallback save also failed: {fallback_error}")
                return None
    
    def get_tool_definition(self) -> Dict[str, Any]:
        """Return the MCP tool definition."""
        return {
            "name": "generate_cover_image",
            "description": "Generate contextually relevant cover image from editorial text using Tool-externally, Agent-internally pattern",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "editorial_text": {
                        "type": "string",
                        "description": "Editorial text to analyze and generate image from"
                    },
                    "domain": {
                        "type": "string",
                        "description": "Domain context for image style and knowledge graph lookup"
                    },
                    "style": {
                        "type": "string",
                        "enum": Config.SUPPORTED_STYLES,
                        "default": "professional",
                        "description": "Visual style for the image"
                    },
                    "dimensions": {
                        "type": "string",
                        "default": Config.DEFAULT_IMAGE_SIZE,
                        "description": "Image dimensions (e.g., '1024x1024', '1920x1080')"
                    },
                    "image_engine": {
                        "type": "string",
                        "enum": Config.SUPPORTED_ENGINES,
                        "default": "dall-e-3",
                        "description": "Image generation engine to use"
                    }
                },
                "required": ["editorial_text", "domain"]
            }
        }
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the cover image generation tool."""
        editorial_text = kwargs["editorial_text"]
        domain = kwargs["domain"]
        style = kwargs.get("style", "professional")
        dimensions = kwargs.get("dimensions", Config.DEFAULT_IMAGE_SIZE)
        image_engine = kwargs.get("image_engine", "dall-e-3")
        
        logger.info(f"Generating cover image for domain: {domain}")
        
        try:
            # Step 1: Tool Call - Extract keywords using knowledge graph
            logger.info("Step 1: Extracting keywords from editorial text")
            keywords_result = await self._extract_keywords_from_text(
                editorial_text, domain
            )
            
            if keywords_result["status"] != "success":
                return {
                    "status": "error",
                    "message": f"Keyword extraction failed: {keywords_result.get('message', 'Unknown error')}"
                }
            
            # Step 2: Agent Reasoning - Understand editorial context
            logger.info("Step 2: Reasoning over editorial context")
            context_analysis = await self._analyze_editorial_context(
                editorial_text, keywords_result["keywords"], domain
            )
            
            # Step 3: Agent Reasoning - Generate contextually relevant prompt
            logger.info("Step 3: Generating contextually relevant image prompt")
            image_prompt = await self._generate_contextual_image_prompt(
                editorial_text, keywords_result["keywords"], domain, style, context_analysis
            )
            
            # Step 4: Tool Call - Generate image using specified engine
            logger.info(f"Step 4: Generating image using {image_engine}")
            image_result = await self._generate_image_with_engine(
                prompt=image_prompt,
                engine=image_engine,
                dimensions=dimensions,
                style=style
            )
            
            if image_result["status"] != "success":
                return image_result
            
            # Step 5: Download and encode image
            logger.info("Step 5: Processing generated image")
            image_data = await self.image_processor.download_and_encode_image(
                image_result["image_url"]
            )
            
            # Step 6: Save image locally and upload to Cloudinary
            logger.info("Step 6: Saving image locally and uploading to Cloudinary")
            local_image_path = self._save_image_locally(image_data, dimensions)
            cloudinary_url = self._upload_to_cloudinary(local_image_path)
            
            return {
                "status": "success",
                "image_url": cloudinary_url,  # Return Cloudinary URL as primary URL
                "original_url": image_result["image_url"],  # Keep original URL for reference
                "local_path": local_image_path,  # Local file path
                "image_data": image_data,
                "prompt_used": image_prompt,
                "keywords_extracted": keywords_result["keywords"],
                "context_analysis": context_analysis,
                "dimensions": dimensions,
                "style": style,
                "engine_used": image_engine,
                "reasoning_steps": [
                    "Extracted keywords using knowledge graph centrality",
                    "Analyzed editorial context and tone",
                    "Generated contextual prompt with guardrails",
                    f"Created image using {image_engine}",
                    "Processed and encoded final image",
                    "Saved image locally and uploaded to Cloudinary"
                ]
            }
            
        except Exception as e:
            logger.error(f"Cover image generation failed: {e}")
            return {
                "status": "error",
                "message": f"Cover image generation failed: {str(e)}"
            }
    
    async def _extract_keywords_from_text(
        self, 
        text: str, 
        domain: str
    ) -> Dict[str, Any]:
        """Tool Call: Extract keywords using knowledge graph."""
        # Check if knowledge graph exists
        if domain not in self.knowledge_graphs:
            return {
                "status": "error",
                "message": f"No knowledge graph found for domain: {domain}"
            }
        
        kg = self.knowledge_graphs[domain]
        
        # Extract candidate keywords
        candidate_keywords = await self.llm_processor.extract_candidate_keywords(text)
        
        # Match against knowledge graph nodes
        matched_keywords = []
        for keyword in candidate_keywords:
            keyword_lower = keyword.lower()
            for node_id, node in kg.nodes.items():
                if (keyword_lower in node.label.lower() or 
                    node.label.lower() in keyword_lower):
                    matched_keywords.append({
                        "keyword": keyword,
                        "node_id": node_id,
                        "centrality_score": node.centrality_score,
                        "node_label": node.label
                    })
                    break
        
        # Sort by centrality and filter
        matched_keywords.sort(key=lambda x: x["centrality_score"], reverse=True)
        filtered_keywords = [
            kw for kw in matched_keywords 
            if kw["centrality_score"] >= Config.DEFAULT_MIN_CENTRALITY_THRESHOLD
        ][:Config.DEFAULT_MAX_CANDIDATE_KEYWORDS]
        
        return {
            "status": "success",
            "keywords": filtered_keywords,
            "total_candidates": len(candidate_keywords),
            "matched_keywords": len(filtered_keywords)
        }
    
    async def _analyze_editorial_context(
        self, 
        editorial_text: str, 
        keywords: List[Dict[str, Any]], 
        domain: str
    ) -> Dict[str, Any]:
        """Agent Reasoning: Analyze editorial context, tone, and visual requirements."""
        
        prompt = f"""
        Analyze this {domain} editorial text and provide context for image generation:
        
        Editorial Text: {editorial_text[:Config.MAX_TEXT_LENGTH_FOR_ANALYSIS]}
        
        Extracted Keywords: {[kw['keyword'] for kw in keywords[:Config.DEFAULT_MAX_KEYWORDS]]}
        
        Please analyze and provide:
        1. Editorial tone (formal, conversational, technical, emotional)
        2. Main themes and concepts
        3. Visual mood (hopeful, serious, innovative, clinical, breakthrough)
        4. Target audience (professionals, patients, researchers, general public)
        5. Key visual elements that should be emphasized
        6. Color palette suggestions based on tone and domain
        7. Any sensitive topics that need careful visual treatment
        
        Respond in JSON format with these fields.
        """
        
        response = await self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=500
        )
        
        try:
            context_data = json.loads(response.choices[0].message.content)
            return context_data
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return {
                "tone": "professional",
                "themes": [kw['keyword'] for kw in keywords[:5]],
                "mood": "professional",
                "audience": "professionals",
                "visual_elements": keywords[:3],
                "color_palette": "blues, grays, whites",
                "sensitive_topics": []
            }
    
    async def _generate_contextual_image_prompt(
        self, 
        editorial_text: str, 
        keywords: List[Dict[str, Any]], 
        domain: str, 
        style: str,
        context_analysis: Dict[str, Any]
    ) -> str:
        """Agent Reasoning: Generate contextually relevant image prompt with guardrails."""
        
        # Extract high-centrality keywords
        high_centrality_keywords = [
            kw['keyword'] for kw in keywords 
            if kw.get('centrality_score', 0) > 0.1
        ][:5]
        
        # Apply guardrails for sensitive medical content
        guardrails = self.image_processor.apply_content_guardrails(
            editorial_text, domain, context_analysis
        )
        
        # Generate domain-specific visual elements
        visual_elements = self.image_processor.generate_visual_elements(
            domain, context_analysis
        )
        
        prompt = f"""
        Create a {style} cover image for a {domain} editorial publication.
        
        Editorial Context:
        - Tone: {context_analysis.get('tone', 'professional')}
        - Mood: {context_analysis.get('mood', 'professional')}
        - Audience: {context_analysis.get('audience', 'professionals')}
        
        Key Concepts (high centrality): {', '.join(high_centrality_keywords)}
        
        Visual Requirements:
        - Style: {style} design approach
        - Color Palette: {context_analysis.get('color_palette', 'professional blues, grays, whites')}
        - Visual Elements: {', '.join(visual_elements)}
        - Layout: Balanced composition with clear hierarchy
        
        Content Guardrails:
        {guardrails}
        
        Technical Specifications:
        - Professional medical/healthcare aesthetic
        - Clean, readable typography
        - Appropriate for {context_analysis.get('audience', 'professional')} audience
        - Avoid cluttered or overly complex designs
        
        Generate an image that visually represents the editorial's key concepts while
        maintaining appropriate tone and professional standards for the {domain} domain.
        """
        
        return prompt.strip()
    
    async def _generate_image_with_engine(
        self, 
        prompt: str, 
        engine: str, 
        dimensions: str, 
        style: str
    ) -> Dict[str, Any]:
        """Tool Call: Generate image using specified engine."""
        
        try:
            if engine == "dall-e-3":
                return await self._generate_dall_e_image(prompt, dimensions)
            else:
                # Default to DALL-E for unsupported engines
                logger.warning(f"Unsupported engine '{engine}', falling back to DALL-E")
                return await self._generate_dall_e_image(prompt, dimensions)
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Image generation with {engine} failed: {str(e)}"
            }
    
    async def _generate_dall_e_image(self, prompt: str, dimensions: str) -> Dict[str, Any]:
        """Generate image using DALL-E 3."""
        try:
            response = await self.openai_client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=dimensions,
                quality="standard",
                n=1
            )
            
            return {
                "status": "success",
                "image_url": response.data[0].url,
                "engine": "dall-e-3"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"DALL-E generation failed: {str(e)}"
            }
    
