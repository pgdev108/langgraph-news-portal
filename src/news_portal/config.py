from pathlib import Path

TOPIC = "Cancer Health Care"

# Two sub-topics (names only; descriptions separate)
SUBTOPICS = [
    "Cancer Research & Prevention",
    "Early Detection and Diagnosis",
]

SUBTOPIC_DESCRIPTIONS = {
    "Cancer Research & Prevention": (
        "How is AI transforming cancer research by analyzing large-scale genomic, imaging, and clinical datasets "
        "to discover new insights? In what ways can AI predict cancer risk and guide prevention strategies at both "
        "individual and population levels?"
    ),
    "Early Detection and Diagnosis": (
        "How does AI enhance early cancer detection and diagnosis through imaging, pathology, and screening tools?"
    ),
}

# Tunables
NEWS_ARTICLE_COUNT = 2        # configurable; Streamlit control can override at runtime
SEARCH_DAYS_FRESH = 21
SEARCH_DAYS_EXTEND = 60

# Files
OUTPUT_DIR = Path("./output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
RESULT_FILE = OUTPUT_DIR / "cancer_health_care_result.json"
