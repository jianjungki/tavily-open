# -*- coding: utf-8 -*-
"""
Configuration Module - Loads configuration from environment variables

This module loads configuration from environment variables and provides
default values when environment variables are not set.
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv
from loguru import logger

# Load environment variables from .env file
load_dotenv()
logger.info("Loading environment variable configuration")

# SearXNG Configuration
SEARXNG_HOST = os.getenv("SEARXNG_HOST", "localhost")
SEARXNG_PORT = int(os.getenv("SEARXNG_PORT", "8080"))
SEARXNG_BASE_PATH = os.getenv("SEARXNG_BASE_PATH", "/search")
SEARXNG_API_BASE = f"http://{SEARXNG_HOST}:{SEARXNG_PORT}{SEARXNG_BASE_PATH}"

# API Service Configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "3000"))

# Crawler Configuration
DEFAULT_SEARCH_LIMIT = int(os.getenv("DEFAULT_SEARCH_LIMIT", "10"))
CONTENT_FILTER_THRESHOLD = float(os.getenv("CONTENT_FILTER_THRESHOLD", "0.6"))
WORD_COUNT_THRESHOLD = int(os.getenv("WORD_COUNT_THRESHOLD", "10"))

# Search Engine Configuration
DISABLED_ENGINES = os.getenv(
    "DISABLED_ENGINES",
    "wikipedia__general,currency__general,wikidata__general,duckduckgo__general,"
    "google__general,lingva__general,qwant__general,startpage__general,"
    "dictzone__general,mymemory translated__general,brave__general"
)
ENABLED_ENGINES = os.getenv("ENABLED_ENGINES", "baidu__general")
SEARCH_LANGUAGE = os.getenv("SEARCH_LANGUAGE", "auto")


def get_config_info() -> Dict[str, Any]:
    """Returns a dictionary of current configuration information

    Returns:
        dict: Dictionary containing all configuration parameters
    """
    return {
        "searxng": {
            "host": SEARXNG_HOST,
            "port": SEARXNG_PORT,
            "base_path": SEARXNG_BASE_PATH,
            "api_base": SEARXNG_API_BASE
        },
        "api": {
            "host": API_HOST,
            "port": API_PORT
        },
        "crawler": {
            "default_search_limit": DEFAULT_SEARCH_LIMIT,
            "content_filter_threshold": CONTENT_FILTER_THRESHOLD,
            "word_count_threshold": WORD_COUNT_THRESHOLD
        },
        "search_engines": {
            "disabled": DISABLED_ENGINES,
            "enabled": ENABLED_ENGINES
        }
    }