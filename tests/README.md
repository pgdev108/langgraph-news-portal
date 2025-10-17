# Tests Directory

This directory contains all test scripts for the LangGraph News Portal.

## Test Files

- `test_featured_articles.py` - Tests that 5 featured articles are displayed (one per subtopic)
- `test_fresh_news.py` - Tests that news search returns fresh articles
- `test_performance.py` - Compares performance between original and optimized versions
- `test_summary_length.py` - Tests that summaries meet the 150-word minimum requirement

## Running Tests

From the project root directory:

```bash
# Run individual tests
python tests/test_featured_articles.py
python tests/test_fresh_news.py
python tests/test_performance.py
python tests/test_summary_length.py

# Or run all tests
python -m pytest tests/
```

## Requirements

- Set up environment variables (OPENAI_API_KEY, SERPER_API_KEY) before running tests
- Some tests require API access and may fail without proper credentials
