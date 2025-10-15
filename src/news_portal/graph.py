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
    llm, SUMMARY_PROMPT, EDITORIAL_PROMPT, EXPAND_EDITORIAL_PROMPT, MAJOR_EDITORIAL_PROMPT, QUALITY_PROMPT,
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
    # per-subtopic loop flags
    need_more_crp: bool
    need_more_edd: bool
    need_more_cddd: bool
    need_more_ctm: bool
    need_more_po: bool
    # (kept for compatibility; not used for bouncing anymore)
    news_article_count: int


# ---------- Utility ----------
def _word_count(s: str | None) -> int:
    return len((s or "").split())

def _first_n_words(s: str, n=200) -> str:
    return " ".join((s or "").split()[:n])


# ---------- News Picker Nodes (one per sub-topic) ----------
def _picker_common(state: PortalState, sub: str, queries: List[str], need_flag: str) -> PortalState:
    llm()  # instantiate to ensure env validated; not used in picker logic
    want = state.get("news_article_count", NEWS_ARTICLE_COUNT)
    items = fetch_articles_with_content(queries, want=want, days_first=SEARCH_DAYS_FRESH, days_second=SEARCH_DAYS_EXTEND)
    pack = state.get("per_subtopic", {}).get(sub, {"retries": 0})
    pack["articles"] = items[: max(want * 2, want)]
    pack["good_indices"] = []
    state.setdefault("per_subtopic", {})[sub] = pack
    state[need_flag] = False
    return state

def news_picker_crp(state: PortalState) -> PortalState:
    return _picker_common(
        state,
        "Cancer Research & Prevention",
        ["Cancer research prevention news", "Cancer prevention population risk study", "Cancer prevention guideline update"],
        "need_more_crp",
    )

def news_picker_edd(state: PortalState) -> PortalState:
    return _picker_common(
        state,
        "Early Detection and Diagnosis",
        ["Early cancer detection diagnosis news", "Cancer screening biomarkers news", "Radiology pathology cancer diagnosis update"],
        "need_more_edd",
    )

def news_picker_cddd(state: PortalState) -> PortalState:
    return _picker_common(
        state,
        "Cancer Drug Discovery and Development",
        ["Cancer drug discovery development news", "AI drug discovery oncology trial", "Target identification oncology update"],
        "need_more_cddd",
    )

def news_picker_ctm(state: PortalState) -> PortalState:
    return _picker_common(
        state,
        "Cancer Treatment Methods",
        ["Cancer treatment methods chemo regimen news", "Oncology therapy selection guideline update", "Radiotherapy immunotherapy news"],
        "need_more_ctm",
    )

def news_picker_po(state: PortalState) -> PortalState:
    return _picker_common(
        state,
        "Precision Oncology",
        ["Precision oncology genomics EMR integration news", "Molecular tumor board news", "Biomarker-driven therapy update"],
        "need_more_po",
    )


# ---------- Editor Nodes (one per sub-topic) ----------
def _editor_common(state: PortalState, sub: str, need_more_flag: str) -> PortalState:
    model = llm()
    want = state.get("news_article_count", NEWS_ARTICLE_COUNT)
    pack = state["per_subtopic"].setdefault(sub, {"retries": 0})
    articles = pack.get("articles", [])

    # 1) Quality pass (structured output on LLM)
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
        if assessment["keep"] and assessment["quality_score"] >= 5 and a.get("content"):
            good.append(i)

    # Allow a single retry to fetch more if not enough
    if len(good) < want and pack.get("retries", 0) < 1:
        pack["good_indices"] = good
        pack["retries"] = pack.get("retries", 0) + 1
        state["per_subtopic"][sub] = pack
        state[need_more_flag] = True
        return state

    # 2) Summaries (≥300 words)
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

    # 3) Editorial (≥ 2,000 words) + self-expansion up to 2 attempts
    summaries_for_prompt = "\n\n".join(
        f"- {articles[idx].get('title')}\n{articles[idx].get('summary','')}" for idx in pack["good_indices"]
    )
    ed_chain = EDITORIAL_PROMPT | model
    editorial = ed_chain.invoke({
        "subtopic": sub,
        "description": SUBTOPIC_DESCRIPTIONS.get(sub, ""),
        "summaries": summaries_for_prompt
    }).content.strip()

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
    return state

def editor_crp(state: PortalState) -> PortalState:
    return _editor_common(state, "Cancer Research & Prevention", "need_more_crp")

def editor_edd(state: PortalState) -> PortalState:
    return _editor_common(state, "Early Detection and Diagnosis", "need_more_edd")

def editor_cddd(state: PortalState) -> PortalState:
    return _editor_common(state, "Cancer Drug Discovery and Development", "need_more_cddd")

def editor_ctm(state: PortalState) -> PortalState:
    return _editor_common(state, "Cancer Treatment Methods", "need_more_ctm")

def editor_po(state: PortalState) -> PortalState:
    return _editor_common(state, "Precision Oncology", "need_more_po")


# ---------- Chief Editor Node ----------
def chief_editor(state: PortalState) -> PortalState:
    model = llm(temperature=0.1)

    # Pick best articles (first good, simple heuristic)
    for sub in SUBTOPICS:
        pack = state["per_subtopic"].get(sub, {})
        if pack.get("good_indices"):
            pack["best_article_index"] = pack["good_indices"][0]
            state["per_subtopic"][sub] = pack

    # Build Home + Major Editorial
    best_articles, snippets = [], []
    for sub in SUBTOPICS:
        sp = state["per_subtopic"].get(sub, {})
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

    # Add nodes (pickers/editors for each sub-topic)
    g.add_node("news_picker_crp", news_picker_crp)
    g.add_node("editor_crp", editor_crp)

    g.add_node("news_picker_edd", news_picker_edd)
    g.add_node("editor_edd", editor_edd)

    g.add_node("news_picker_cddd", news_picker_cddd)
    g.add_node("editor_cddd", editor_cddd)

    g.add_node("news_picker_ctm", news_picker_ctm)
    g.add_node("editor_ctm", editor_ctm)

    g.add_node("news_picker_po", news_picker_po)
    g.add_node("editor_po", editor_po)

    g.add_node("chief", chief_editor)

    # Entry → CRP
    g.set_entry_point("news_picker_crp")
    g.add_edge("news_picker_crp", "editor_crp")

    # CRP loop/flow → EDD
    def router_crp(state: PortalState):
        return "news_picker_crp" if state.get("need_more_crp") else "news_picker_edd"
    g.add_conditional_edges("editor_crp", router_crp, {"news_picker_crp": "news_picker_crp", "news_picker_edd": "news_picker_edd"})

    # EDD
    g.add_edge("news_picker_edd", "editor_edd")
    def router_edd(state: PortalState):
        return "news_picker_edd" if state.get("need_more_edd") else "news_picker_cddd"
    g.add_conditional_edges("editor_edd", router_edd, {"news_picker_edd": "news_picker_edd", "news_picker_cddd": "news_picker_cddd"})

    # CDDD
    g.add_edge("news_picker_cddd", "editor_cddd")
    def router_cddd(state: PortalState):
        return "news_picker_cddd" if state.get("need_more_cddd") else "news_picker_ctm"
    g.add_conditional_edges("editor_cddd", router_cddd, {"news_picker_cddd": "news_picker_cddd", "news_picker_ctm": "news_picker_ctm"})

    # CTM
    g.add_edge("news_picker_ctm", "editor_ctm")
    def router_ctm(state: PortalState):
        return "news_picker_ctm" if state.get("need_more_ctm") else "news_picker_po"
    g.add_conditional_edges("editor_ctm", router_ctm, {"news_picker_ctm": "news_picker_ctm", "news_picker_po": "news_picker_po"})

    # PO
    g.add_edge("news_picker_po", "editor_po")
    def router_po(state: PortalState):
        return "news_picker_po" if state.get("need_more_po") else "chief"
    g.add_conditional_edges("editor_po", router_po, {"news_picker_po": "news_picker_po", "chief": "chief"})

    # Chief → END (no bounce needed; editors self-expand)
    g.add_edge("chief", END)

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
        "need_more_crp": False,
        "need_more_edd": False,
        "need_more_cddd": False,
        "need_more_ctm": False,
        "need_more_po": False,
        "news_article_count": news_article_count,
    }

    # Single run; bounded recursion limit (no infinite bouncing)
    state = graph.invoke(
        state,
        config={"configurable": {"thread_id": "MAIN"}, "recursion_limit": 20},
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
