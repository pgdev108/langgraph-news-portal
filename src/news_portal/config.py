from pathlib import Path

TOPIC = "Cancer Health Care"

SUBTOPICS = [
    "Cancer Research & Prevention",
    "Early Detection and Diagnosis",
    "Cancer Drug Discovery and Development",
    "Cancer Treatment Methods",
    "Precision Oncology",
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
    "Cancer Drug Discovery and Development": (
        "What role does AI play in accelerating cancer drug discovery, from target identification to clinical trials?"
    ),
    "Cancer Treatment Methods": (
        "How can AI assist in determining whether a cancer patient requires chemotherapy, and if so, recommend the "
        "most suitable medication and regimen during the chemotherapy process?"
    ),
    "Precision Oncology": (
        "How does AI enable precision oncology by personalizing treatments through integration of genomics, medical "
        "records, and patient data?"
    ),
}

# Tunables
NEWS_ARTICLE_COUNT = 2        # configurable via Streamlit control
SEARCH_DAYS_FRESH = 21
SEARCH_DAYS_EXTEND = 60

# Files
OUTPUT_DIR = Path("./output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
RESULT_FILE = OUTPUT_DIR / "cancer_health_care_result.json"
