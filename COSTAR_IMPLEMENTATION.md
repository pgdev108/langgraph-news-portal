# COSTAR Template Implementation

This document outlines how the COSTAR template has been implemented across all prompts in the LangGraph News Portal.

## COSTAR Template Structure

**C**ontext: Provide the necessary background information for the AI to understand the scenario.
**O**bjective: Clearly state the specific goal you want the AI to achieve.
**S**tyle: Specify the writing style (e.g., formal, casual, technical, creative).
**T**one: Determine the emotional or attitudinal coloring of the response (e.g., professional, friendly, empathetic).
**A**udience: Identify the intended audience for the response to tailor it appropriately.
**R**esponse: Specify the desired output format (e.g., bullet points, paragraph, list, JSON).

## Implemented Prompts

### 1. SUMMARY_PROMPT
- **Context:** Medical editor working for healthcare news portal
- **Objective:** Create comprehensive yet concise summary of medical articles
- **Style:** Professional medical writing with clear, factual language
- **Tone:** Authoritative yet accessible, evidence-based, clinically relevant
- **Audience:** Healthcare professionals (doctors, researchers, medical students)
- **Response:** Well-structured summary of 150-200 words with key findings, clinical implications, methodology highlights, and practical applications

### 2. EDITORIAL_PROMPT
- **Context:** Senior medical editor creating editorial content for cancer healthcare news portal
- **Objective:** Write comprehensive editorial synthesizing insights from multiple research articles
- **Style:** Academic editorial writing with analytical depth
- **Tone:** Expert, insightful, forward-thinking with critical analysis
- **Audience:** Healthcare professionals, researchers, policy makers
- **Response:** Structured editorial of 500-800 words with clear sections: landscape analysis, insights synthesis, clinical implications, limitations, future directions

### 3. MAJOR_EDITORIAL_PROMPT
- **Context:** Chief editor of prestigious cancer healthcare news portal
- **Objective:** Write comprehensive editorial synthesizing insights across multiple cancer research domains
- **Style:** Executive-level editorial writing with strategic perspective
- **Tone:** Authoritative, visionary, comprehensive
- **Audience:** Senior healthcare leaders, policy makers, researchers, medical professionals
- **Response:** Comprehensive editorial of 800-1200 words with sections: executive summary, cross-cutting themes, clinical implications, policy considerations, strategic directions

### 4. QUALITY_PROMPT
- **Context:** Medical content curator for healthcare news portal
- **Objective:** Assess medical articles for relevance and quality
- **Style:** Analytical evaluation with clear criteria
- **Tone:** Objective, critical, professional
- **Audience:** Internal content curation system
- **Response:** JSON object with keep (boolean), reason (brief explanation), quality_score (0-10 integer)

### 5. BATCH_SUMMARY_PROMPT
- **Context:** Medical editor processing multiple medical research articles simultaneously
- **Objective:** Create detailed summaries for multiple articles with consistency
- **Style:** Professional medical writing with structured language
- **Tone:** Authoritative, evidence-based, clinically relevant
- **Audience:** Healthcare professionals (doctors, researchers, medical students)
- **Response:** JSON array with title, summary (150-200 words), key_findings (array), implications (array)

### 6. BATCH_QUALITY_PROMPT
- **Context:** Medical content curation specialist evaluating multiple articles
- **Objective:** Assess multiple articles for relevance and quality efficiently
- **Style:** Systematic evaluation with consistent criteria
- **Tone:** Objective, critical, professional
- **Audience:** Internal content curation system
- **Response:** JSON array with title, keep (boolean), reason (brief explanation), quality_score (0-10 integer)

## Benefits of COSTAR Implementation

1. **Clarity:** Each prompt clearly defines the role, context, and expectations
2. **Consistency:** All prompts follow the same structured format
3. **Specificity:** Clear objectives and response formats reduce ambiguity
4. **Audience Awareness:** Tailored content for specific healthcare professional audiences
5. **Quality Control:** Explicit tone and style guidelines ensure professional output
6. **Efficiency:** Clear response formats enable better parsing and processing

## Usage

The COSTAR-templated prompts are automatically used when running the news portal:

```bash
uv run streamlit run src/news_portal/main.py
```

All prompts now provide clearer guidance to the LLM, resulting in more consistent, professional, and targeted content generation.
