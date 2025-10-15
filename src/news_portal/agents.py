import os
from typing import List, Dict, TypedDict

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# Load .env early
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# ---------- LLM ----------
def llm(model: str | None = None, temperature: float = 0.2) -> ChatOpenAI:
    model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    return ChatOpenAI(model=model, temperature=temperature)

# ---------- Prompts ----------
SUMMARY_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are a precise medical/health editor. Summarize the article in 2–3 sentences (60–90 words). "
     "Be neutral, specific, and avoid sensationalism. Use facts from the article text only."),
    ("human", "Title: {title}\nSource: {source}\nDate: {date}\n\nArticle Text:\n{content}\n\nSummary:")
])

EDITORIAL_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are a senior editor writing a rigorous, well-structured editorial for clinicians and researchers. "
     "Write at least 2,000 words, with clear sections, synthesis of evidence, and cautious, balanced tone. "
     "Include context, limitations, and practical implications."),
    ("human",
     "Sub-topic: {subtopic}\n\n"
     "Brief descriptions/context: {description}\n\n"
     "Summaries of selected articles:\n{summaries}\n\n"
     "Write the editorial:")
])

MAJOR_EDITORIAL_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are the chief editor synthesizing five 2,000-word editorials into one major editorial of at least 2,000 words. "
     "Write a coherent, structured piece with clear sections, cross-cutting themes, and careful conclusions."),
    ("human",
     "Topic: {topic}\n\nSub-topics: {subtopics}\n\n"
     "Editorial snippets per sub-topic (first ~200 words each):\n{snippets}\n\n"
     "Write the major editorial:")
])

QUALITY_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You evaluate article candidates for fit and quality for a given sub-topic. "
     "Return JSON with fields: keep (true/false), reason (short), quality_score (0-10)."),
    ("human",
     "Sub-topic: {subtopic}\n\nTitle: {title}\nSource: {source}\nDate: {date}\n\n"
     "First 1200 chars of content:\n{content}\n\n"
     "Assess now:")
])

class QualityAssessmentTD(TypedDict):
    keep: bool
    reason: str
    quality_score: float