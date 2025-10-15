import os
from typing import TypedDict

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate


def llm(model: str | None = None, temperature: float = 0.2) -> ChatOpenAI:
    model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")  # optional
    organization = os.getenv("OPENAI_ORG_ID")  # optional

    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Set it via env, .env, or Streamlit secrets.\n"
            "Example: export OPENAI_API_KEY=sk-..."
        )
    return ChatOpenAI(model=model, temperature=temperature, api_key=api_key, base_url=base_url, organization=organization)


# ----- Structured output schema for quality check -----
class QualityAssessmentTD(TypedDict):
    keep: bool
    reason: str
    quality_score: float


# ----- Prompts -----
SUMMARY_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are a precise medical/health editor. Summarize the article in a cohesive, neutral way using only facts from "
     "the provided text. The summary must be AT LEAST 300 words, ideally 320–380 words. No fluff, no hype."),
    ("human", "Title: {title}\nSource: {source}\nDate: {date}\n\nArticle Text:\n{content}\n\nSummary (≥300 words):")
])

EDITORIAL_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are a senior editor writing a rigorous editorial for clinicians and researchers. "
     "Write AT LEAST 2,000 words with clear sections, synthesis of evidence, context, limitations, and implications."),
    ("human",
     "Sub-topic: {subtopic}\n\n"
     "Brief description/context: {description}\n\n"
     "Summaries of selected articles:\n{summaries}\n\n"
     "Write the editorial (≥2,000 words):")
])

MAJOR_EDITORIAL_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are the chief editor synthesizing multiple sub-topic editorials into one major editorial of AT LEAST 2,000 words. "
     "Write a coherent, structured piece with cross-cutting themes and cautious conclusions."),
    ("human",
     "Topic: {topic}\n\nSub-topics: {subtopics}\n\n"
     "Editorial snippets (first ~200 words for each sub-topic):\n{snippets}\n\n"
     "Write the major editorial (≥2,000 words):")
])

QUALITY_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You evaluate article candidates for fit and quality for a sub-topic. "
     "Return JSON with fields: keep (true/false), reason (short), quality_score (0-10)."),
    ("human",
     "Sub-topic: {subtopic}\n\nTitle: {title}\nSource: {source}\nDate: {date}\n\n"
     "First 1200 chars of content:\n{content}\n\n"
     "Assess now:")
])

# agents.py (append near other prompts)
EXPAND_EDITORIAL_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are a senior editor. Expand and refine the given editorial to meet or exceed 2,000 words "
     "while preserving meaning, improving structure, and adding evidence/context as needed."),
    ("human",
     "Sub-topic: {subtopic}\n\n"
     "Brief description/context: {description}\n\n"
     "Article summaries:\n{summaries}\n\n"
     "Current editorial (~{current_wc} words):\n{editorial}\n\n"
     "Rewrite/expand to >= 2,000 words, coherent and well-structured:")
])
