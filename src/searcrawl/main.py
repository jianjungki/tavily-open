# -*- coding: utf-8 -*-
"""
Sear-Crawl4AI - An open-source search and crawling tool based on SearXNG and Crawl4AI

Sear-Crawl4AI is an open-source alternative to Tavily, providing search and crawling
capabilities using SearXNG as the search engine and Crawl4AI for web crawling.

This project can serve as an open-source alternative to Tavily, providing similar search
and web content extraction capabilities.
"""

from typing import List, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import sys
import subprocess
import asyncio
from loguru import logger

# Import custom modules
from searcrawl.config import (
    API_HOST,
    API_PORT,
    DEFAULT_SEARCH_LIMIT,
    DISABLED_ENGINES,
    ENABLED_ENGINES,
    CRAWLER_POOL_SIZE,
    CACHE_ENABLED,
    REDIS_URL,
    CACHE_TTL_HOURS
)
from searcrawl.crawler import WebCrawler
from searcrawl.cache import CacheManager
import searcrawl.logger as log_module

# Global crawler pool and cache manager
crawler_pool: Optional[asyncio.Queue] = None
cache_manager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager

    Handles startup and shutdown events for the FastAPI application
    """
    global crawler_pool, cache_manager

    # Startup
    log_module.setup_logger("INFO")
    logger.info("Sear-Crawl4AI service starting...")

    # Initialize cache manager if enabled
    if CACHE_ENABLED:
        try:
            logger.info(f"Initializing cache manager with Redis: {REDIS_URL}")
            cache_manager = CacheManager(REDIS_URL, CACHE_TTL_HOURS)
            if cache_manager.is_available():
                logger.info("Cache manager initialized successfully")
                cache_stats = cache_manager.get_cache_stats()
                logger.info(f"Cache stats: {cache_stats}")
            else:
                logger.warning("Cache manager initialized but Redis is not available")
                cache_manager = None
        except Exception as e:
            logger.error(f"Failed to initialize cache manager: {str(e)}")
            logger.warning("Continuing without cache")
            cache_manager = None
    else:
        logger.info("Cache is disabled")
        cache_manager = None

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

    # Initialize crawler pool
    logger.info(f"Initializing crawler pool with size: {CRAWLER_POOL_SIZE}")
    crawler_pool = asyncio.Queue(maxsize=CRAWLER_POOL_SIZE)
    
    # Create and initialize crawler instances with cache manager
    for i in range(CRAWLER_POOL_SIZE):
        crawler = WebCrawler(cache_manager=cache_manager)
        await crawler.initialize()
        await crawler_pool.put(crawler)
        logger.info(f"Crawler {i+1}/{CRAWLER_POOL_SIZE} initialized and added to pool")
    
    logger.info("Crawler pool initialization completed")
    logger.info(f"API service running at: http://{API_HOST}:{API_PORT}")
    logger.info("Sear-Crawl4AI service startup completed")

    yield

    # Shutdown
    logger.info("Starting graceful shutdown...")
    if crawler_pool:
        # Close all crawler instances in the pool
        crawlers_to_close = []
        while not crawler_pool.empty():
            try:
                crawler = await asyncio.wait_for(crawler_pool.get(), timeout=1.0)
                crawlers_to_close.append(crawler)
            except asyncio.TimeoutError:
                break
        
        # Close all crawlers concurrently
        if crawlers_to_close:
            await asyncio.gather(*[crawler.close() for crawler in crawlers_to_close])
            logger.info(f"Released {len(crawlers_to_close)} crawler instances")
    
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


async def get_crawler_from_pool():
    """Get a crawler instance from the pool
    
    Returns:
        WebCrawler: A crawler instance from the pool
        
    Raises:
        HTTPException: If unable to get a crawler from the pool
    """
    global crawler_pool
    if crawler_pool is None:
        logger.error("Crawler pool not initialized")
        raise HTTPException(status_code=503, detail="Service not ready - crawler pool not initialized")
    
    try:
        # Wait up to 30 seconds to get a crawler from the pool
        crawler = await asyncio.wait_for(crawler_pool.get(), timeout=30.0)
        return crawler
    except asyncio.TimeoutError:
        logger.error("Timeout waiting for available crawler from pool")
        raise HTTPException(status_code=503, detail="Service temporarily unavailable - all crawlers busy")
    except Exception as e:
        logger.error(f"Error getting crawler from pool: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def return_crawler_to_pool(crawler: WebCrawler):
    """Return a crawler instance to the pool
    
    Args:
        crawler: The crawler instance to return to the pool
    """
    global crawler_pool
    if crawler_pool is None:
        logger.error("Crawler pool not initialized, cannot return crawler")
        return
    
    try:
        await crawler_pool.put(crawler)
    except Exception as e:
        logger.error(f"Error returning crawler to pool: {str(e)}")


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
    crawler = await get_crawler_from_pool()
    try:
        return await crawler.crawl_urls(request.urls, request.instruction)
    finally:
        await return_crawler_to_pool(crawler)


@app.get("/cache/stats")
async def get_cache_stats():
    """
    Get cache statistics endpoint

    Returns cache statistics including total entries and memory usage

    Returns:
        Dict: Cache statistics
    """
    global cache_manager
    try:
        if not cache_manager:
            logger.warning("Cache manager not available")
            return {"status": "unavailable", "message": "Cache is not enabled or not available"}
        
        stats = cache_manager.get_cache_stats()
        logger.info(f"Cache stats retrieved: {stats}")
        return stats
    except Exception as e:
        logger.error(f"Error getting cache stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/cache/clear")
async def clear_cache():
    """
    Clear all cache entries endpoint

    Clears all cached crawl results

    Returns:
        Dict: Operation result
    """
    global cache_manager
    try:
        if not cache_manager:
            logger.warning("Cache manager not available")
            return {"status": "unavailable", "message": "Cache is not enabled or not available"}
        
        success = cache_manager.clear_all()
        if success:
            logger.info("Cache cleared successfully")
            return {"status": "success", "message": "Cache cleared successfully"}
        else:
            logger.warning("Failed to clear cache")
            return {"status": "error", "message": "Failed to clear cache"}
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


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
    global cache_manager
    try:
        # Add status feedback
        logger.info(f"Starting search: {request.query}")

        # Check cache for search results
        if cache_manager:
            cached_result = cache_manager.get_search_cache(request.query)
            if cached_result:
                logger.info(f"Search cache hit for query: {request.query}")
                return cached_result

        # Call SearXNG search engine (now async)
        response = await WebCrawler.make_searxng_request(
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
        crawl_result = await crawl(CrawlRequest(urls=urls, instruction=request.query))

        # Cache the search result
        if cache_manager:
            cache_manager.set_search_cache(request.query, crawl_result)

        return crawl_result
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
