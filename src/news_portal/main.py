import json
import traceback
from pathlib import Path
from datetime import datetime

import streamlit as st

from news_portal.config import RESULT_FILE, SUBTOPICS, TOPIC, NEWS_ARTICLE_COUNT
from news_portal.graph import run_graph # Load .env and map Streamlit secrets before imports that use env

# Load .env early
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

st.set_page_config(page_title="Cancer Health Care News Portal", layout="wide")
st.title("🧬 Cancer Health Care News Portal")

# Session state
if "results" not in st.session_state: st.session_state["results"] = None
if "error" not in st.session_state: st.session_state["error"] = None
if "active_menu" not in st.session_state: st.session_state["active_menu"] = "Home"
if "running" not in st.session_state: st.session_state["running"] = False
if "loaded_from_file" not in st.session_state: st.session_state["loaded_from_file"] = False
if "news_article_count" not in st.session_state: st.session_state["news_article_count"] = NEWS_ARTICLE_COUNT

def _read_results_file():
    try:
        if RESULT_FILE.exists():
            data = json.loads(RESULT_FILE.read_text())
            ts = datetime.fromtimestamp(RESULT_FILE.stat().st_mtime)
            return data, ts
    except Exception as e:
        st.session_state["error"] = f"Failed to load saved results: {e}\n\n{traceback.format_exc()}"
    return None, None

def load_cached():
    data, ts = _read_results_file()
    if data:
        st.session_state["results"] = data
        st.session_state["active_menu"] = "Home"
        st.session_state["loaded_from_file"] = True
        st.toast(f"Loaded saved results ({ts.strftime('%Y-%m-%d %H:%M:%S')})", icon="✅")
    else:
        st.toast("No saved results file found.", icon="⚠️")

def run_agents():
    st.session_state["running"] = True
    st.session_state["error"] = None
    try:
        with st.spinner("Running LangGraph agents..."):
            out = run_graph(news_article_count=st.session_state["news_article_count"])
            st.session_state["results"] = out
            st.session_state["active_menu"] = "Home"
            st.session_state["loaded_from_file"] = False
    except Exception as e:
        st.session_state["error"] = f"{e}\n\n{traceback.format_exc()}"
        st.session_state["results"] = None
    finally:
        st.session_state["running"] = False
        st.rerun()

def card_article(a: dict):
    st.markdown(
        f"**{a.get('title','(title)')}**  \n"
        f"[Open Link]({a.get('url','')})  \n"
        f"*Source:* {a.get('source','?')}  \n"
        f"*Published:* {a.get('published_date','?')}  \n\n"
        f"{a.get('summary','(no summary)')}"
    )

def render_home(final: dict):
    st.subheader("🏠 Home")
    home = final.get("home", {}) or {}
    best_articles = home.get("best_articles", []) or []
    main_editorial = home.get("main_editorial", "") or ""
    st.markdown("### Featured Articles")
    if best_articles:
        for a in best_articles:
            with st.container(border=True):
                card_article(a)
    else:
        st.info("No featured articles yet.")
    st.markdown("---")
    st.markdown("### Main Editorial")
    if main_editorial:
        st.write(main_editorial)
    else:
        st.info("Main editorial not available.")

def render_subtopic(final: dict, subtopic: str):
    st.subheader(f"📚 {subtopic}")
    ps = (final.get("per_subtopic", {}) or {}).get(subtopic, {}) or {}
    st.markdown(f"#### News Articles ({len(ps.get('articles', []))})")
    for a in ps.get("articles", []):
        with st.container(border=True):
            card_article(a)
    st.markdown("---")
    st.markdown("#### Editorial")
    editorial = ps.get("editorial")
    if editorial:
        st.write(editorial)
    else:
        st.info("Editorial not available for this sub-topic.")    
    

# Controls
left, mid, right = st.columns([2, 2, 6])
with left:
    st.button("Run Agents", type="primary", disabled=st.session_state["running"], on_click=run_agents)
with mid:
    st.button("Reload from saved file", disabled=st.session_state["running"], on_click=load_cached)
with right:
    st.number_input(
        "News articles per sub-topic",
        min_value=1, max_value=5, step=1,
        value=st.session_state["news_article_count"],
        key="news_article_count",
        help="Controls how many articles the picker/editor pipeline selects per sub-topic."
    )

# Auto-load saved file on first render
if st.session_state["results"] is None and not st.session_state["loaded_from_file"]:
    data, _ = _read_results_file()
    if data:
        st.session_state["results"] = data
        st.session_state["loaded_from_file"] = True

debug = st.toggle("Debug", value=False)

# Layout
nav, content = st.columns([1, 3])

with nav:
    st.markdown("### Sections")
    if st.button("Home", use_container_width=True, disabled=st.session_state["running"]):
        st.session_state["active_menu"] = "Home"
    for sub in SUBTOPICS:
        if st.button(sub, use_container_width=True, disabled=st.session_state["running"]):
            st.session_state["active_menu"] = sub
    if RESULT_FILE.exists():
        ts = datetime.fromtimestamp(RESULT_FILE.stat().st_mtime)
        st.caption(f"Saved: {ts.strftime('%Y-%m-%d %H:%M:%S')} → {RESULT_FILE}")

with content:
    if st.session_state["error"]:
        st.error(st.session_state["error"])
    res = st.session_state["results"]
    if not res:
        st.info("Click **Run Agents** or **Reload from saved file**.")
    else:
        if debug:
            st.write("### Debug (raw)")
            st.json(res)
        final = res.get("final")
        if not final:
            st.warning("No `final` object found in results.")
        else:
            active = st.session_state.get("active_menu", "Home")
            if active == "Home":
                render_home(final)
            else:
                render_subtopic(final, active)
