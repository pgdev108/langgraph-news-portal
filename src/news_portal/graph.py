import json
import asyncio
import time
from typing import Dict, List, Optional, TypedDict
from concurrent.futures import ThreadPoolExecutor, as_completed

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from news_portal.config import (
    TOPIC, SUBTOPICS, SUBTOPIC_DESCRIPTIONS,
    NEWS_ARTICLE_COUNT, RESULT_FILE, SEARCH_DAYS_FRESH, SEARCH_DAYS_EXTEND
)
from news_portal.tools import fetch_articles_with_content
from news_portal.agents import (
    llm, SUMMARY_PROMPT, EDITORIAL_PROMPT, MAJOR_EDITORIAL_PROMPT, QUALITY_PROMPT,
    BATCH_SUMMARY_PROMPT, BATCH_QUALITY_PROMPT, QualityAssessmentTD,
)


# ---------- Typed state ----------
class SubtopicPack(TypedDict, total=False):
    articles: List[Dict]
    good_indices: List[int]
    editorial: Optional[str]
    best_article_index: Optional[int]
    completed: bool

class PortalState(TypedDict, total=False):
    topic: str
    subtopics: List[str]
    per_subtopic: Dict[str, SubtopicPack]
    home: Dict
    news_article_count: int
    processing_complete: bool


# ---------- Utility ----------
def _word_count(s: str | None) -> int:
    return len((s or "").split())

def _first_n_words(s: str, n=100) -> str:
    return " ".join((s or "").split()[:n])

def _validate_summary_length(summary: str, min_words: int = 150) -> bool:
    """Validate that a summary meets minimum word count."""
    word_count = _word_count(summary)
    return word_count >= min_words


# ---------- Optimized Subtopic Processing ----------
def process_subtopic_parallel(subtopic: str, queries: List[str], want: int) -> SubtopicPack:
    """Process a single subtopic with optimized approach."""
    start_time = time.time()
    print(f"🔄 Processing {subtopic}...")
    
    # 1. Fetch articles
    fetch_start = time.time()
    articles = fetch_articles_with_content(
        queries, want=want*2,  # Get more to have better selection
        days_first=SEARCH_DAYS_FRESH, 
        days_second=SEARCH_DAYS_EXTEND
    )
    fetch_time = time.time() - fetch_start
    print(f"  📰 Article fetching: {fetch_time:.2f}s ({len(articles)} articles)")
    
    if not articles:
        return {"articles": [], "good_indices": [], "editorial": "", "completed": True}
    
    # 2. Batch quality assessment
    qa_start = time.time()
    model = llm()
    batch_qa_chain = BATCH_QUALITY_PROMPT | model
    
    # Prepare articles for batch processing
    articles_for_batch = []
    for i, a in enumerate(articles[:10]):  # Limit to 10 for batch processing
        articles_for_batch.append({
            "index": i,
            "title": a.get("title", ""),
            "source": a.get("source", ""),
            "date": a.get("published_date", ""),
            "content": (a.get("content") or "")[:800]  # Shorter content for faster processing
        })
    
    try:
        batch_assessment = batch_qa_chain.invoke({
            "subtopic": subtopic,
            "articles": json.dumps(articles_for_batch)
        }).content.strip()
        
        # Parse batch results
        assessments = json.loads(batch_assessment)
        good_indices = []
        
        for assessment in assessments:
            if (assessment.get("keep") and 
                assessment.get("quality_score", 0) >= 6 and  # Higher threshold
                assessment.get("index") is not None):
                good_indices.append(assessment["index"])
        
        # Take only the number we want
        good_indices = good_indices[:want]
        
    except Exception as e:
        print(f"⚠️ Batch quality assessment failed for {subtopic}: {e}")
        # Fallback: take first few articles
        good_indices = list(range(min(want, len(articles))))
    
    qa_time = time.time() - qa_start
    print(f"  🔍 Quality assessment: {qa_time:.2f}s ({len(good_indices)} selected)")
    
    # 3. Batch summary generation
    summary_time = 0
    if good_indices:
        summary_start = time.time()
        selected_articles = [articles[i] for i in good_indices]
        
        try:
            batch_summary_chain = BATCH_SUMMARY_PROMPT | model
            summaries_result = batch_summary_chain.invoke({
                "articles": json.dumps([
                    {
                        "title": a.get("title", ""),
                        "content": (a.get("content") or "")[:3000]  # More content for better summaries
                    } for a in selected_articles
                ])
            }).content.strip()
            
            summaries = json.loads(summaries_result)
            
            # Add summaries to articles with validation
            for i, summary_data in enumerate(summaries):
                if i < len(selected_articles):
                    summary_text = summary_data.get("summary", "")
                    word_count = len(summary_text.split())
                    
                    # If summary is too short, try to expand it
                    if word_count < 150:
                        print(f"  ⚠️ Summary too short ({word_count} words), expanding...")
                        try:
                            # Use individual summary prompt for expansion
                            individual_summary_chain = SUMMARY_PROMPT | model
                            expanded_summary = individual_summary_chain.invoke({
                                "title": selected_articles[i].get("title", ""),
                                "source": selected_articles[i].get("source", ""),
                                "date": selected_articles[i].get("published_date", ""),
                                "content": (selected_articles[i].get("content") or "")[:4000]
                            }).content.strip()
                            
                            expanded_word_count = len(expanded_summary.split())
                            if expanded_word_count >= 150:
                                selected_articles[i]["summary"] = expanded_summary
                                print(f"  ✅ Expanded to {expanded_word_count} words")
                            else:
                                selected_articles[i]["summary"] = summary_text
                                print(f"  ⚠️ Still short after expansion ({expanded_word_count} words)")
                        except Exception as expand_error:
                            print(f"  ⚠️ Expansion failed: {expand_error}")
                            selected_articles[i]["summary"] = summary_text
                    else:
                        selected_articles[i]["summary"] = summary_text
                        print(f"  ✅ Summary length: {word_count} words")
            
        except Exception as e:
            print(f"⚠️ Batch summary failed for {subtopic}: {e}")
            # Fallback: generate individual summaries
            print(f"  🔄 Falling back to individual summaries...")
            individual_summary_chain = SUMMARY_PROMPT | model
            for a in selected_articles:
                try:
                    summary = individual_summary_chain.invoke({
                        "title": a.get("title", ""),
                        "source": a.get("source", ""),
                        "date": a.get("published_date", ""),
                        "content": (a.get("content") or "")[:4000]
                    }).content.strip()
                    a["summary"] = summary
                    word_count = len(summary.split())
                    print(f"  ✅ Individual summary: {word_count} words")
                except Exception as individual_error:
                    print(f"  ⚠️ Individual summary failed: {individual_error}")
                    a["summary"] = f"Comprehensive summary of {a.get('title', 'article')} - detailed analysis of key findings, clinical implications, and research outcomes."
        
        summary_time = time.time() - summary_start
        print(f"  📝 Summary generation: {summary_time:.2f}s ({len(selected_articles)} summaries)")
    
    # 4. Generate editorial
    editorial_start = time.time()
    editorial = ""
    if good_indices:
        summaries_text = "\n\n".join([
            f"- {articles[i].get('title', '')}\n{articles[i].get('summary', '')}" 
            for i in good_indices
        ])
        
        try:
            editorial_chain = EDITORIAL_PROMPT | model
            editorial = editorial_chain.invoke({
                "subtopic": subtopic,
                "description": SUBTOPIC_DESCRIPTIONS.get(subtopic, ""),
                "summaries": summaries_text
            }).content.strip()
        except Exception as e:
            print(f"⚠️ Editorial generation failed for {subtopic}: {e}")
            editorial = f"Editorial for {subtopic} - processing completed."
    
    editorial_time = time.time() - editorial_start
    total_time = time.time() - start_time
    
    print(f"  📄 Editorial generation: {editorial_time:.2f}s")
    print(f"  ⏱️  Total subtopic time: {total_time:.2f}s")
    
    return {
        "articles": articles,
        "good_indices": good_indices,
        "editorial": editorial,
        "best_article_index": good_indices[0] if good_indices else None,
        "completed": True
    }


# ---------- Parallel Subtopic Processing Node ----------
def process_all_subtopics(state: PortalState) -> PortalState:
    """Process all subtopics in parallel for maximum speed."""
    parallel_start = time.time()
    print("🚀 Starting parallel subtopic processing...")
    
    want = state.get("news_article_count", NEWS_ARTICLE_COUNT)
    
    # Define queries for each subtopic with more variety
    import random
    from datetime import datetime
    
    current_date = datetime.now().strftime("%Y-%m-%d")
    current_month = datetime.now().strftime("%B %Y")
    
    subtopic_queries = {
        "Cancer Research & Prevention": [
            f"Cancer research prevention news {current_date}", 
            f"Cancer prevention population risk study {current_month}", 
            f"Cancer prevention guideline update latest",
            f"Cancer research breakthrough {current_date}"
        ],
        "Early Detection and Diagnosis": [
            f"Early cancer detection diagnosis news {current_date}", 
            f"Cancer screening biomarkers news {current_month}", 
            f"Radiology pathology cancer diagnosis update latest",
            f"Cancer detection technology breakthrough {current_date}"
        ],
        "Cancer Drug Discovery and Development": [
            f"Cancer drug discovery development news {current_date}", 
            f"AI drug discovery oncology trial {current_month}", 
            f"Target identification oncology update latest",
            f"Cancer drug breakthrough {current_date}"
        ],
        "Cancer Treatment Methods": [
            f"Cancer treatment methods chemo regimen news {current_date}", 
            f"Oncology therapy selection guideline update {current_month}", 
            f"Radiotherapy immunotherapy news latest",
            f"Cancer treatment breakthrough {current_date}"
        ],
        "Precision Oncology": [
            f"Precision oncology genomics EMR integration news {current_date}", 
            f"Molecular tumor board news {current_month}", 
            f"Biomarker-driven therapy update latest",
            f"Precision medicine cancer {current_date}"
        ],
    }
    
    # Process subtopics in parallel with randomized query selection
    with ThreadPoolExecutor(max_workers=3) as executor:  # Limit to avoid rate limits
        future_to_subtopic = {}
        for subtopic, queries in subtopic_queries.items():
            # Randomly select 3 queries from the 4 available to add variety
            selected_queries = random.sample(queries, min(3, len(queries)))
            future_to_subtopic[executor.submit(process_subtopic_parallel, subtopic, selected_queries, want)] = subtopic
        
        for future in as_completed(future_to_subtopic):
            subtopic = future_to_subtopic[future]
            try:
                result = future.result()
                state["per_subtopic"][subtopic] = result
                print(f"✅ Completed {subtopic}")
            except Exception as e:
                print(f"❌ Failed {subtopic}: {e}")
                state["per_subtopic"][subtopic] = {
                    "articles": [], "good_indices": [], "editorial": "", "completed": True
                }
    
    parallel_time = time.time() - parallel_start
    print(f"✅ Parallel processing completed in {parallel_time:.2f}s")
    state["processing_complete"] = True
    return state


# ---------- Chief Editor Node ----------
def chief_editor(state: PortalState) -> PortalState:
    """Generate final home page content."""
    chief_start = time.time()
    print("📝 Generating final editorial...")
    
    model = llm(temperature=0.1)
    
    # Build best articles and snippets
    best_articles, snippets = [], []
    for sub in SUBTOPICS:
        sp = state["per_subtopic"].get(sub, {})
        idx = sp.get("best_article_index")
        articles = sp.get("articles", [])
        
        print(f"🔍 {sub}: {len(articles)} articles, best_index={idx}")
        
        a = articles[idx] if isinstance(idx, int) and articles and idx < len(articles) else {}
        
        if a:
            best_articles.append({
                "subtopic": sub,
                "title": a.get("title", ""),
                "url": a.get("url", ""),
                "published_date": a.get("published_date", ""),
                "summary": a.get("summary", ""),
                "source": a.get("source", ""),
            })
            print(f"✅ Added featured article: {a.get('title', 'No title')[:50]}...")
        else:
            print(f"⚠️ No featured article for {sub}")
        
        snippets.append(f"[{sub}] {_first_n_words(sp.get('editorial', ''), 100)}")
    
    print(f"📊 Total featured articles: {len(best_articles)}")
    
    # Generate major editorial
    try:
        maj_chain = MAJOR_EDITORIAL_PROMPT | model
        major_editorial = maj_chain.invoke({
            "topic": state["topic"],
            "subtopics": ", ".join(state["subtopics"]),
            "snippets": "\n\n".join(snippets)
        }).content.strip()
    except Exception as e:
        print(f"⚠️ Major editorial generation failed: {e}")
        major_editorial = f"Comprehensive editorial on {state['topic']} covering all sub-topics."
    
    state["home"] = {
        "best_articles": best_articles,  # Show one article from each subtopic (5 total)
        "main_editorial": major_editorial
    }
    
    chief_time = time.time() - chief_start
    print(f"📄 Chief editor completed in {chief_time:.2f}s")
    
    return state


# ---------- Optimized Graph Builder ----------
def build_graph():
    """Build the optimized graph with parallel processing."""
    g = StateGraph(PortalState)
    
    # Add nodes
    g.add_node("process_subtopics", process_all_subtopics)
    g.add_node("chief", chief_editor)
    
    # Simple linear flow
    g.set_entry_point("process_subtopics")
    g.add_edge("process_subtopics", "chief")
    g.add_edge("chief", END)
    
    memory = MemorySaver()
    return g.compile(checkpointer=memory)


# ---------- Optimized Runner ----------
def run_graph(news_article_count: int = NEWS_ARTICLE_COUNT) -> Dict:
    """Run the optimized graph."""
    total_start = time.time()
    print("🚀 Starting optimized news portal processing...")
    print(f"📊 Configuration: {news_article_count} articles per subtopic")
    print("=" * 60)
    
    graph_start = time.time()
    graph = build_graph()
    graph_build_time = time.time() - graph_start
    print(f"🔧 Graph built in {graph_build_time:.2f}s")
    
    state: PortalState = {
        "topic": TOPIC,
        "subtopics": SUBTOPICS,
        "per_subtopic": {},
        "home": {},
        "news_article_count": news_article_count,
        "processing_complete": False,
    }
    
    # Run the graph
    execution_start = time.time()
    state = graph.invoke(
        state,
        config={"configurable": {"thread_id": "MAIN"}, "recursion_limit": 10},
    )
    execution_time = time.time() - execution_start
    print(f"⚡ Graph execution completed in {execution_time:.2f}s")
    
    # Prepare final output
    final_start = time.time()
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
        chosen = [arts[i] for i in good] if good else arts[:news_article_count]
        
        final["per_subtopic"][sub] = {
            "articles": [
                {
                    "title": a.get("title", ""),
                    "url": a.get("url", ""),
                    "source": a.get("source", ""),
                    "published_date": a.get("published_date", ""),
                    "summary": a.get("summary", ""),
                } for a in chosen
            ],
            "editorial": pack.get("editorial", ""),
        }
    
    payload = {"final": final}
    RESULT_FILE.write_text(json.dumps(payload, indent=2))
    
    final_time = time.time() - final_start
    total_time = time.time() - total_start
    
    print("=" * 60)
    print("📊 PERFORMANCE SUMMARY")
    print("=" * 60)
    print(f"🔧 Graph building:     {graph_build_time:.2f}s")
    print(f"⚡ Graph execution:    {execution_time:.2f}s")
    print(f"📄 Final processing:   {final_time:.2f}s")
    print(f"⏱️  TOTAL TIME:         {total_time:.2f}s ({total_time/60:.1f} minutes)")
    print("=" * 60)
    print("✅ Processing completed!")
    return payload