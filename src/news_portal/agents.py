"""
Optimized Agents for News Portal

This module contains optimized prompts and agents designed for speed
while maintaining quality. Key optimizations:
- Shorter summaries (150-200 words)
- Shorter editorials (500-800 words)
- Batch processing where possible
- Reduced LLM calls
"""

import os
from typing import TypedDict, List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate


def llm(model: str | None = None, temperature: float = 0.1) -> ChatOpenAI:
    """Optimized LLM with lower temperature for faster, more consistent responses."""
    model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    organization = os.getenv("OPENAI_ORG_ID")

    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Set it via env, .env, or Streamlit secrets.\n"
            "Example: export OPENAI_API_KEY=sk-..."
        )
    return ChatOpenAI(model=model, temperature=temperature, api_key=api_key, base_url=base_url, organization=organization)


class QualityAssessmentTD(TypedDict):
    keep: bool
    reason: str
    quality_score: float


# OPTIMIZED PROMPTS - Much shorter and faster

SUMMARY_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are a medical editor. Write a concise, factual summary in 150-200 words. "
     "Focus on key findings, implications, and clinical relevance. Be comprehensive "
     "but concise. Minimum 150 words required."),
    ("human", "Title: {title}\nSource: {source}\nDate: {date}\n\nArticle Text:\n{content}\n\nConcise Summary (150-200 words):")
])

EDITORIAL_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are a senior editor. Write a focused editorial in 500-800 words covering: "
     "key insights, clinical implications, limitations, and future directions. "
     "Be concise but comprehensive."),
    ("human",
     "Sub-topic: {subtopic}\n\n"
     "Context: {description}\n\n"
     "Article summaries:\n{summaries}\n\n"
     "Write editorial (500-800 words):")
])

MAJOR_EDITORIAL_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are the chief editor. Write a comprehensive editorial in 800-1200 words "
     "synthesizing insights across sub-topics. Focus on cross-cutting themes, "
     "clinical implications, and future directions."),
    ("human",
     "Topic: {topic}\n\nSub-topics: {subtopics}\n\n"
     "Editorial snippets:\n{snippets}\n\n"
     "Write major editorial (800-1200 words):")
])

QUALITY_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You evaluate articles for relevance and quality. Return JSON with: "
     "keep (true/false), reason (brief), quality_score (0-10). "
     "Be strict - only keep high-quality, relevant articles."),
    ("human",
     "Sub-topic: {subtopic}\n\nTitle: {title}\nSource: {source}\nDate: {date}\n\n"
     "Content preview:\n{content}\n\n"
     "Assess relevance and quality:")
])

# BATCH PROCESSING PROMPTS

BATCH_SUMMARY_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are a medical editor. Summarize multiple articles concisely. "
     "For each article, provide: title, concise summary (150-200 words), key findings (2-3 points), clinical implications (1-2 points). "
     "Be comprehensive but concise. Minimum 150 words per summary required. Format as JSON array."),
    ("human",
     "Articles to summarize:\n{articles}\n\n"
     "Provide concise summaries as JSON array with fields: title, summary, key_findings, implications")
])

BATCH_QUALITY_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You evaluate multiple articles for relevance and quality. "
     "Return JSON array with fields: title, keep (true/false), reason (brief), quality_score (0-10). "
     "Be strict - only keep high-quality, relevant articles."),
    ("human",
     "Sub-topic: {subtopic}\n\nArticles to evaluate:\n{articles}\n\n"
     "Assess each article and return JSON array:")
])