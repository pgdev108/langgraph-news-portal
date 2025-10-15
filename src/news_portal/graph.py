import json
from typing import Dict, List, Optional, TypedDict

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from news_portal.config import (
    TOPIC, SUBTOPICS, SUBTOPIC_DESCRIPTIONS,
    NEWS_ARTICLE_COUNT, RESULT_FILE, SEARCH_DAYS_FRESH, SEARCH_DAYS_EXTEND
)
from news_portal.tools import fetch_articles_with_content
from news_portal.agents import (
    llm, SUMMARY_PROMPT, EDITORIAL_PROMPT, MAJOR_EDITORIAL_PROMPT, QUALITY_PROMPT,
    QualityAssessmentTD,
)

# ---------- Typed state ----------
class SubtopicPack(TypedDict, total=False):
    articles: List[Dict]            # {title,url,source,published_date,content,summary?}
    good_indices: List[int]         # indices of chosen good articles
    editorial: Optional[str]        # >= 2000 words when accepted
    best_article_index: Optional[int]
    retries: int                    # picker-editor retries for this sub-topic

class PortalState(TypedDict, total=False):
    topic: str
    subtopics: List[str]
    per_subtopic: Dict[str, SubtopicPack]
    home: Dict
    current_subtopic: Optional[str]
    need_more_csp: bool
    need_more_edd: bool
    need_fix_csp: bool
    need_fix_edd: bool
    news_article_count: int


# ---------- Utility ----------
def _word_count(s: str | None) -> int:
    return len((s or "").split())

def _first_n_words(s: str, n=200) -> str:
    return " ".join((s or "").split()[:n])


# ---------- News Picker Nodes (separate per sub-topic) ----------
def news_picker_csp(state: PortalState) -> PortalState:
    model = llm()
    sub = "Cancer Research & Prevention"
    want = state.get("news_article_count", NEWS_ARTICLE_COUNT)
    queries = [
        "Cancer research prevention news",
        "Cancer prevention population risk study",
        "Cancer prevention guideline update",
    ]
    items = fetch_articles_with_content(queries, want=want, days_first=SEARCH_DAYS_FRESH, days_second=SEARCH_DAYS_EXTEND)
    pack = state.get("per_subtopic", {}).get(sub, {"retries": 0})
    pack["articles"] = items[: max(want * 2, want)]
    pack["good_indices"] = []
    state.setdefault("per_subtopic", {})[sub] = pack
    state["need_more_csp"] = False
    return state

def news_picker_edd(state: PortalState) -> PortalState:
    model = llm()
    sub = "Early Detection and Diagnosis"
    want = state.get("news_article_count", NEWS_ARTICLE_COUNT)
    queries = [
        "Early cancer detection diagnosis news",
        "Cancer screening biomarkers news",
        "Radiology pathology cancer diagnosis update",
    ]
    items = fetch_articles_with_content(queries, want=want, days_first=SEARCH_DAYS_FRESH, days_second=SEARCH_DAYS_EXTEND)
    pack = state.get("per_subtopic", {}).get(sub, {"retries": 0})
    pack["articles"] = items[: max(want * 2, want)]
    pack["good_indices"] = []
    state.setdefault("per_subtopic", {})[sub] = pack
    state["need_more_edd"] = False
    return state


# ---------- Editor Nodes (separate per sub-topic) ----------
def _editor_common(state: PortalState, sub: str, need_more_flag: str, need_fix_flag: str) -> PortalState:
    from news_portal.agents import EXPAND_EDITORIAL_PROMPT  # local import avoids circulars on reload

    model = llm()
    want = state.get("news_article_count", NEWS_ARTICLE_COUNT)
    pack = state["per_subtopic"].setdefault(sub, {"retries": 0})
    articles = pack.get("articles", [])

    # 1) Quality pass (same as before)
    structured_llm = model.with_structured_output(QualityAssessmentTD)
    qa_chain = QUALITY_PROMPT | structured_llm

    good = []
    for i, a in enumerate(articles):
        if len(good) >= want:
            break
        assessment: QualityAssessmentTD = qa_chain.invoke({
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

    if len(good) < want and pack.get("retries", 0) < 1:
        pack["good_indices"] = good
        pack["retries"] = pack.get("retries", 0) + 1
        state["per_subtopic"][sub] = pack
        state[need_more_flag] = True
        return state

    # 2) Summaries
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

    # 3) Editorial (>= 2,000 words); self-expand up to 2 attempts
    summaries_for_prompt = "\n\n".join(
        f"- {articles[idx].get('title')}\n{articles[idx].get('summary','')}" for idx in pack["good_indices"]
    )
    ed_chain = EDITORIAL_PROMPT | model
    editorial = ed_chain.invoke({
        "subtopic": sub,
        "description": SUBTOPIC_DESCRIPTIONS.get(sub, ""),
        "summaries": summaries_for_prompt
    }).content.strip()

    # If short, expand in-place (bounded loop so chief won't bounce)
    attempts = 0
    while _word_count(editorial) < 2000 and attempts < 2:
        attempts += 1
        expand_chain = EXPAND_EDITORIAL_PROMPT | model
        editorial = expand_chain.invoke({
            "subtopic": sub,
            "description": SUBTOPIC_DESCRIPTIONS.get(sub, ""),
            "summaries": summaries_for_prompt,
            "editorial": editorial,
            "current_wc": _word_count(editorial),
        }).content.strip()

    pack["editorial"] = editorial
    state["per_subtopic"][sub] = pack
    state[need_more_flag] = False
    state[need_fix_flag] = False
    return state


def editor_csp(state: PortalState) -> PortalState:
    return _editor_common(state, "Cancer Research & Prevention", "need_more_csp", "need_fix_csp")

def editor_edd(state: PortalState) -> PortalState:
    return _editor_common(state, "Early Detection and Diagnosis", "need_more_edd", "need_fix_edd")


# ---------- Chief Editor Node ----------
def chief_editor(state: PortalState) -> PortalState:
    model = llm(temperature=0.1)
    # Verify editorials (after editor self-expansion, they should pass)
    for sub in SUBTOPICS:
        pack = state["per_subtopic"].get(sub, {})
        editorial = pack.get("editorial") or ""
        # pick best article = first good (heuristic)
        if pack.get("good_indices"):
            pack["best_article_index"] = pack["good_indices"][0]
            state["per_subtopic"][sub] = pack

    # Build Home + Major Editorial
    best_articles, snippets = [], []
    for sub in SUBTOPICS:
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

    # Nodes
    g.add_node("news_picker_csp", news_picker_csp)
    g.add_node("editor_csp", editor_csp)

    g.add_node("news_picker_edd", news_picker_edd)
    g.add_node("editor_edd", editor_edd)

    g.add_node("chief", chief_editor)

    # Entry: run both pipelines sequentially
    g.set_entry_point("news_picker_csp")
    g.add_edge("news_picker_csp", "editor_csp")

    # CSP loop: editor_csp -> picker_csp (if need_more) else move to EDD pipeline
    def router_csp(state: PortalState):
        return "news_picker_csp" if state.get("need_more_csp") else "news_picker_edd"
    g.add_conditional_edges("editor_csp", router_csp, {"news_picker_csp": "news_picker_csp", "news_picker_edd": "news_picker_edd"})

    # EDD pipeline
    g.add_edge("news_picker_edd", "editor_edd")

    # EDD loop: editor_edd -> picker_edd (if need_more) else -> chief
    def router_edd(state: PortalState):
        return "news_picker_edd" if state.get("need_more_edd") else "chief"
    g.add_conditional_edges("editor_edd", router_edd, {"news_picker_edd": "news_picker_edd", "chief": "chief"})

    # Chief can bounce back to editors if an editorial is short
    def chief_router(state: PortalState):
        if state.get("need_fix_csp"):
            return "editor_csp"
        if state.get("need_fix_edd"):
            return "editor_edd"
        return END
    g.add_conditional_edges("chief", chief_router, {"editor_csp": "editor_csp", "editor_edd": "editor_edd", END: END})

    memory = MemorySaver()
    return g.compile(checkpointer=memory)


# ---------- Runner ----------
def run_graph(news_article_count: int = NEWS_ARTICLE_COUNT) -> Dict:
    graph = build_graph()

    state: PortalState = {
        "topic": TOPIC,
        "subtopics": SUBTOPICS,
        "per_subtopic": {},
        "home": {},
        "current_subtopic": None,
        "need_more_csp": False,
        "need_more_edd": False,
        "need_fix_csp": False,
        "need_fix_edd": False,
        "news_article_count": news_article_count,
    }

    # Single pass to END; set recursion_limit (e.g., 12)
    state = graph.invoke(
        state,
        config={"configurable": {"thread_id": "MAIN"}, "recursion_limit": 12},
    )

    # Persist final JSON for the UI
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
        chosen = [arts[i] for i in good] if good else arts[: state.get("news_article_count", NEWS_ARTICLE_COUNT)]
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
    RESULT_FILE.write_text(json.dumps(payload, indent=2))
    return payload
