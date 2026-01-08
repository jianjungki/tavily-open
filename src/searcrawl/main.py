# -*- coding: utf-8 -*-
"""
Sear-Crawl4AI - An open-source search and crawling tool based on SearXNG and Crawl4AI

Sear-Crawl4AI is an open-source alternative to Tavily, providing search and crawling
capabilities using SearXNG as the search engine and Crawl4AI for web crawling.

This project can serve as an open-source alternative to Tavily, providing similar search
and web content extraction capabilities.
"""

from typing import List
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import sys
import subprocess
from loguru import logger

# Import custom modules
from searcrawl.config import (
    API_HOST,
    API_PORT,
    DEFAULT_SEARCH_LIMIT,
    DISABLED_ENGINES,
    ENABLED_ENGINES
)
from searcrawl.crawler import WebCrawler
import searcrawl.logger as log_module

# Global crawler instance
crawler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager

    Handles startup and shutdown events for the FastAPI application
    """
    global crawler

    # Startup
    log_module.setup_logger("INFO")
    logger.info("Sear-Crawl4AI service starting...")

    # Check and install browsers
    logger.info("Checking Playwright browsers...")
    try:
        subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            check=True
        )
        logger.info("Playwright browsers installed successfully or already exist")
    except subprocess.CalledProcessError as e:
        logger.error(f"Browser installation failed: {e}")
        raise

    # Initialize crawler
    crawler = WebCrawler()
    await crawler.initialize()
    logger.info("Crawler initialization completed")
    logger.info(f"API service running at: http://{API_HOST}:{API_PORT}")
    logger.info("Sear-Crawl4AI service startup completed")

    yield

    # Shutdown
    if crawler:
        await crawler.close()
        logger.info("Crawler resources released")
    logger.info("Sear-Crawl4AI service shut down")


# Initialize FastAPI application with lifespan
app = FastAPI(
    title="Sear-Crawl4AI API",
    description="An open-source search and crawling tool based on SearXNG and Crawl4AI, "
                "serving as an open-source alternative to Tavily",
    version="1.0.0",
    lifespan=lifespan
)


# Request model definitions
class SearchRequest(BaseModel):
    """Search request model

    Attributes:
        query: Search query string
        limit: Limit on number of results to return, default is 10
        disabled_engines: List of disabled search engines, comma-separated
        enabled_engines: List of enabled search engines, comma-separated
    """
    query: str
    limit: int = DEFAULT_SEARCH_LIMIT
    disabled_engines: str = DISABLED_ENGINES
    enabled_engines: str = ENABLED_ENGINES


class CrawlRequest(BaseModel):
    """
    Crawl request model

    Attributes:
        urls: List of URLs to crawl
        instruction: Crawling instruction, typically a search query
    """
    urls: List[str]
    instruction: str


async def crawl(request: CrawlRequest):
    """
    API endpoint function to crawl multiple URLs and process content

    Args:
        request: Crawl request containing URLs and instruction

    Returns:
        Dict: Dictionary containing processed content, success count, and failed URLs

    Raises:
        HTTPException: Raised when an error occurs during crawling
    """
    global crawler
    return await crawler.crawl_urls(request.urls, request.instruction)


@app.post("/search")
async def search(request: SearchRequest):
    """
    Search API endpoint

    Receives search request, calls SearXNG search engine to get results,
    then crawls the search result pages

    Args:
        request: Search request object containing query string and configuration parameters

    Returns:
        Dict: Dictionary containing processed content, success count, and failed URLs

    Raises:
        HTTPException: Raised when an error occurs during search or crawling
    """
    try:
        # Add status feedback
        logger.info(f"Starting search: {request.query}")

        # Call SearXNG search engine
        response = WebCrawler.make_searxng_request(
            query=request.query,
            limit=request.limit,
            disabled_engines=request.disabled_engines,
            enabled_engines=request.enabled_engines
        )

        # Check search results
        results = response.get("results", [])
        if not results:
            logger.warning("No search results found")
            raise HTTPException(status_code=404, detail="No search results found")

        # Limit result count and extract URLs
        urls = [result["url"] for result in results[:request.limit] if "url" in result]
        if not urls:
            logger.warning("No valid URLs found")
            raise HTTPException(status_code=404, detail="No valid URLs found")

        logger.info(f"Found {len(urls)} URLs, starting to crawl")

        # Call crawl function to process URLs
        return await crawl(CrawlRequest(urls=urls, instruction=request.query))
    except HTTPException:
        # Directly re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log other exceptions and convert to HTTP exception
        logger.error(f"Exception occurred during search: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def main():
    """Main entry point for the application"""
    logger.info("Starting Sear-Crawl4AI service via command line")
    uvicorn.run(app, host=API_HOST, port=API_PORT)


if __name__ == "__main__":
    main()