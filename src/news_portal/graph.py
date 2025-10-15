import json
from dataclasses import dataclass
from typing import Dict, List, Optional, TypedDict

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from news_portal.config import (
    TOPIC, SUBTOPICS, SUBTOPIC_DESCRIPTIONS,
    NEWS_ARTICLE_COUNT, RESULT_FILE, SEARCH_DAYS_FRESH, SEARCH_DAYS_EXTEND
)
from news_portal.tools import fetch_articles_with_content
from news_portal.agents import llm, SUMMARY_PROMPT, EDITORIAL_PROMPT, MAJOR_EDITORIAL_PROMPT, QUALITY_PROMPT, QualityAssessmentTD

# Load .env early
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


# ---------- Typed state ----------
class SubtopicPack(TypedDict, total=False):
    articles: List[Dict]          # each: {title,url,source,published_date,content,summary?}
    good_indices: List[int]       # indices of chosen good articles
    editorial: Optional[str]      # >= 2000 words when accepted
    best_article_index: Optional[int]

class PortalState(TypedDict, total=False):
    topic: str
    subtopics: List[str]
    per_subtopic: Dict[str, SubtopicPack]
    home: Dict
    # loop control
    current_subtopic: Optional[str]
    need_more: bool
    need_editor_fix: bool
    need_chief_fix: bool
    news_article_count: int


# ---------- Utility ----------
def _word_count(s: str | None) -> int:
    return len((s or "").split())

def _first_n_words(s: str, n=200) -> str:
    return " ".join((s or "").split()[:n])

# ---------- Nodes ----------
def news_picker_node(state: PortalState) -> PortalState:
    """Fetch candidates with content for the current subtopic."""
    model = llm()
    sub = state["current_subtopic"]
    want = state.get("news_article_count", NEWS_ARTICLE_COUNT)
    # Queries balanced (non-AI specific)
    q = [
        f"{sub} news",
        f"{sub} latest study results",
        f"{sub} guideline update cancer",
    ]
    items = fetch_articles_with_content(q, want=want, days_first=SEARCH_DAYS_FRESH, days_second=SEARCH_DAYS_EXTEND)

    pack = state.get("per_subtopic", {}).get(sub, {})
    pack["articles"] = items[: max(want*2, want)]
    pack["good_indices"] = []
    state.setdefault("per_subtopic", {})[sub] = pack
    # Let editor decide keepers
    state["need_more"] = False
    return state

def editor_node(state: PortalState) -> PortalState:
    """Evaluate candidates; if fewer than N good, request more; else produce summaries and editorial."""
    model = llm()
    sub = state["current_subtopic"]
    want = state.get("news_article_count", NEWS_ARTICLE_COUNT)
    pack = state["per_subtopic"][sub]
    articles = pack.get("articles", [])

    # 1) Fast quality pass
    good = []
    structured_llm = model.with_structured_output(QualityAssessmentTD)  # <-- make the LLM structured
    qa_chain = QUALITY_PROMPT | structured_llm # <-- use the structured LLM
    for i, a in enumerate(articles):
        if len(good) >= want:
            break
        assessment = qa_chain.invoke({
            "subtopic": sub,
            "title": a.get("title",""),
            "source": a.get("source",""),
            "date": a.get("published_date",""),
            "content": (a.get("content") or "")[:1200],
        })
        keep = assessment["keep"]
        score = assessment["quality_score"]
        if keep and score >= 5 and a.get("content"):
            good.append(i)

    if len(good) < want:
        # Ask news_picker to fetch again on next loop
        pack["good_indices"] = good
        state["per_subtopic"][sub] = pack
        state["need_more"] = True
        return state

    # 2) Summaries for selected
    sum_chain = SUMMARY_PROMPT | model
    for idx in good[:want]:
        a = articles[idx]
        summary = sum_chain.invoke({
            "title": a.get("title",""),
            "source": a.get("source",""),
            "date": a.get("published_date",""),
            "content": (a.get("content") or "")[:12000],
        }).content.strip()
        a["summary"] = summary

    pack["good_indices"] = good[:want]

    # 3) Sub-topic editorial (>= 2,000 words)
    summaries_for_prompt = "\n\n".join(
        f"- {articles[idx].get('title')}\n{articles[idx].get('summary','')}" for idx in pack["good_indices"]
    )
    ed_chain = EDITORIAL_PROMPT | model
    editorial = ed_chain.invoke({
        "subtopic": sub,
        "description": SUBTOPIC_DESCRIPTIONS.get(sub, ""),
        "summaries": summaries_for_prompt
    }).content.strip()

    pack["editorial"] = editorial
    state["per_subtopic"][sub] = pack
    # Flag for chief to validate length
    state["need_more"] = False
    state["need_editor_fix"] = False
    return state

def chief_editor_node(state: PortalState) -> PortalState:
    """Verify sub-topic editorial length; pick best article; build main editorial when all sub-topics done."""
    model = llm(temperature=0.1)
    # 1) Ensure each subtopic editorial >= 2000 words; if not, send back to editor on next loop
    all_ok = True
    for sub in state["subtopics"]:
        pack = state["per_subtopic"].get(sub, {})
        editorial = pack.get("editorial") or ""
        if _word_count(editorial) < 2000:
            all_ok = False
            state["current_subtopic"] = sub
            state["need_editor_fix"] = True
            return state  # send back to editor
        # pick best article = first good (heuristic); you can score further if needed
        if pack.get("good_indices"):
            pack["best_article_index"] = pack["good_indices"][0]
            state["per_subtopic"][sub] = pack

    if not all_ok:
        return state

    # 2) Build home + major editorial once all 5 done
    best_articles = []
    snippets = []
    for sub in state["subtopics"]:
        sp = state["per_subtopic"][sub]
        idx = sp.get("best_article_index")
        a = sp["articles"][idx] if isinstance(idx, int) else (sp["articles"][0] if sp.get("articles") else {})
        best_articles.append({
            "subtopic": sub,
            "title": a.get("title"),
            "url": a.get("url"),
            "published_date": a.get("published_date"),
            "summary": a.get("summary"),
            "source": a.get("source"),
        })
        snippets.append(f"[{sub}] { _first_n_words(sp.get('editorial',''), 200) }")

    maj_chain = MAJOR_EDITORIAL_PROMPT | model
    major_editorial = maj_chain.invoke({
        "topic": state["topic"],
        "subtopics": ", ".join(state["subtopics"]),
        "snippets": "\n\n".join(snippets)
    }).content.strip()

    state["home"] = {
        "best_articles": best_articles[: state.get("news_article_count", NEWS_ARTICLE_COUNT)],
        "main_editorial": major_editorial
    }
    return state


# ---------- Graph builder ----------
def build_graph():
    g = StateGraph(PortalState)

    g.add_node("news_picker", news_picker_node)
    g.add_node("editor", editor_node)
    g.add_node("chief", chief_editor_node)

    # Edges
    # start -> picker
    g.set_entry_point("news_picker")

    # picker -> editor
    g.add_edge("news_picker", "editor")

    # editor -> picker if need_more; else -> chief
    def editor_router(state: PortalState):
        return "news_picker" if state.get("need_more") else "chief"
    g.add_conditional_edges("editor", editor_router, {"news_picker": "news_picker", "chief": "chief"})

    # chief -> editor (if need_editor_fix) else END
    def chief_router(state: PortalState):
        return "editor" if state.get("need_editor_fix") else END
    g.add_conditional_edges("chief", chief_router, {"editor": "editor", END: END})

    memory = MemorySaver()  # in-memory checkpoint; swap for SQLiteSaver if you want persistence across runs
    return g.compile(checkpointer=memory)


# ---------- Runner ----------
def run_graph(news_article_count: int = NEWS_ARTICLE_COUNT) -> Dict:
    """Run one subgraph per sub-topic with loop edges until editorial passes; then run chief to assemble home."""
    graph = build_graph()

    # Initial state
    init: PortalState = {
        "topic": TOPIC,
        "subtopics": SUBTOPICS,
        "per_subtopic": {},
        "home": {},
        "current_subtopic": None,
        "need_more": False,
        "need_editor_fix": False,
        "need_chief_fix": False,
        "news_article_count": news_article_count,
    }

    # Process each sub-topic through the (picker <-> editor) loop; chief is used for length enforcement later collectively
    state = init
    for sub in SUBTOPICS:
        state["current_subtopic"] = sub
        # Drive the subgraph: news_picker -> editor -> (news_picker if need_more) -> editor -> chief (only checks lengths later)
        # We’ll run until editor no longer requests more for this subtopic (articles found + summaries + preliminary editorial).
        # The chief node will be called at the very end to validate lengths and produce the main editorial.
        # Here, we step until editor stops asking for more.
        while True:
            for event in graph.stream(state, {"configurable": {"thread_id": f"subtopic:{sub}"}}):
                state = event  # last emitted state
            if not state.get("need_more"):
                break

    # All subtopics have draft editorials; run chief to enforce 2k length and build home/main editorial (with possible editor fixes)
    # This loop lets chief bounce back to editor to expand editorials if short.
    while True:
        for event in graph.stream(state, {"configurable": {"thread_id": "chief"}}):
            state = event
        if not state.get("need_editor_fix"):
            break
        # chief set current_subtopic and need_editor_fix=True; the loop will send back through editor to expand.

    # Persist final JSON your UI expects
    final = {
        "topic": state["topic"],
        "subtopics": state["subtopics"],
        "per_subtopic": {},
        "home": state.get("home", {}),
    }

    for sub in SUBTOPICS:
        pack = state["per_subtopic"].get(sub, {})
        arts = pack.get("articles", [])
        good = pack.get("good_indices", [])
        chosen = [arts[i] for i in good] if good else arts[: news_article_count]
        # normalize for UI
        final["per_subtopic"][sub] = {
            "articles": [
                {
                    "title": a.get("title"),
                    "url": a.get("url"),
                    "source": a.get("source"),
                    "published_date": a.get("published_date"),
                    "summary": a.get("summary"),
                } for a in chosen
            ],
            "editorial": pack.get("editorial"),
        }

    payload = {"final": final}

    # Save to disk for Streamlit to auto-load next time
    RESULT_FILE.write_text(json.dumps(payload, indent=2))
    return payload
