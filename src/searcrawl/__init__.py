# -*- coding: utf-8 -*-
"""
SearCrawl - An open-source search and crawling tool based on SearXNG and Crawl4AI

This package provides search and web content extraction capabilities using
SearXNG as the search engine and Crawl4AI for web crawling.
"""

__version__ = "1.0.0"
__author__ = "SearCrawl Contributors"

from searcrawl.config import get_config_info
from searcrawl.crawler import WebCrawler
from searcrawl.logger import setup_logger

__all__ = ["WebCrawler", "get_config_info", "setup_logger", "__version__"]