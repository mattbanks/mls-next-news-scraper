"""
Configuration settings for the MLS NEXT News Scraper.
"""

import os
from pathlib import Path

# Base configuration
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"

# URLs
MLS_NEXT_NEWS_URL = "https://www.mlssoccer.com/mlsnext/news/"
MLS_BASE_URL = "https://www.mlssoccer.com"

# Scraping settings
MAX_ARTICLES = 15
REQUEST_TIMEOUT = 30
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

# Output files
RSS_OUTPUT_FILE = OUTPUT_DIR / "mls_next_news.xml"
JSON_OUTPUT_FILE = OUTPUT_DIR / "mls_next_articles.json"

# Logging
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

# Ensure output directory exists
OUTPUT_DIR.mkdir(exist_ok=True)
