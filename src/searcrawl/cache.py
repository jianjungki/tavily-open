# -*- coding: utf-8 -*-
"""
Cache Module - Provides distributed caching functionality for crawl results

This module provides a distributed cache system using Redis as the backend,
allowing multiple instances to share cached crawl results and reduce redundant
crawling operations.
"""

import json
import hashlib
from typing import Optional, Dict, Any
from redis import Redis
from datetime import datetime, timedelta
import redis
from loguru import logger


class CacheManager:
    """Distributed cache manager using Redis backend"""

    def __init__(self, redis_url: str, ttl_hours: int = 24):
        """Initialize cache manager with Redis connection

        Args:
            redis_url: Redis connection URL (e.g., 'redis://localhost:6379/0')
            ttl_hours: Time-to-live for cached items in hours, default is 24
        """
        # initialize attribute for type checkers
        self.redis_client: Optional[Redis] = None
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            # Test connection
            assert self.redis_client is not None
            self.redis_client.ping()
            self.ttl_seconds = ttl_hours * 3600
            logger.info(f"Cache manager initialized with Redis: {redis_url}, TTL: {ttl_hours} hours")
        except Exception as e:
            logger.error(f"Failed to initialize cache manager: {str(e)}")
            self.redis_client = None
            self.ttl_seconds = ttl_hours * 3600

    def _generate_cache_key(self, url: str, instruction: str = "") -> str:
        """Generate a cache key from URL and instruction

        Args:
            url: The URL to cache
            instruction: Optional instruction/query string

        Returns:
            str: Generated cache key
        """
        # Create a hash of URL and instruction to generate cache key
        cache_input = f"{url}:{instruction}".encode('utf-8')
        cache_hash = hashlib.md5(cache_input).hexdigest()
        return f"crawl_cache:{cache_hash}"

    def _generate_search_cache_key(self, query: str) -> str:
        """Generate a cache key from a search query
        
        Args:
            query: The search query string
            
        Returns:
            str: Generated cache key
        """
        cache_input = f"search:{query}".encode('utf-8')
        cache_hash = hashlib.md5(cache_input).hexdigest()
        return f"search_cache:{cache_hash}"

    def get_search_cache(self, query: str) -> Optional[Dict[str, Any]]:
        """Get cached search result for a query
        
        Args:
            query: The search query to retrieve from cache
            
        Returns:
            Dict or None: Cached result if found, None otherwise
        """
        if not self.redis_client:
            logger.debug("Redis client not available, skipping cache retrieval")
            return None
            
        try:
            cache_key = self._generate_search_cache_key(query)
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                result = json.loads(cached_data)
                logger.debug(f"Search cache hit for query: {query}")
                # The actual result is nested inside the 'result' key
                return result.get("result")
            else:
                logger.debug(f"Search cache miss for query: {query}")
                return None
        except Exception as e:
            logger.warning(f"Error retrieving from search cache: {str(e)}")
            return None

    def set_search_cache(self, query: str, result: Dict[str, Any]) -> bool:
        """Cache a search result for a query with a 1-minute TTL
        
        Args:
            query: The search query being cached
            result: The search result to cache
            
        Returns:
            bool: True if caching succeeded, False otherwise
        """
        if not self.redis_client:
            logger.debug("Redis client not available, skipping cache storage")
            return False
            
        try:
            cache_key = self._generate_search_cache_key(query)
            cache_data = {
                "result": result,
                "cached_at": datetime.now().isoformat(),
                "query": query
            }
            
            self.redis_client.setex(
                cache_key,
                300, # 1 minute TTL
                json.dumps(cache_data, ensure_ascii=False)
            )
            logger.debug(f"Cached search result for query: {query}")
            return True
        except Exception as e:
            logger.warning(f"Error storing in search cache: {str(e)}")
            return False

    def get(self, url: str, instruction: str = "") -> Optional[Dict[str, Any]]:
        """Get cached crawl result for a URL

        Args:
            url: The URL to retrieve from cache
            instruction: Optional instruction/query string

        Returns:
            Dict or None: Cached result if found, None otherwise
        """
        if not self.redis_client:
            logger.debug("Redis client not available, skipping cache retrieval")
            return None

        try:
            cache_key = self._generate_cache_key(url, instruction)
            cached_data = self.redis_client.get(cache_key)

            if cached_data:
                result = json.loads(cached_data)
                logger.debug(f"Cache hit for URL: {url}")
                return result
            else:
                logger.debug(f"Cache miss for URL: {url}")
                return None
        except Exception as e:
            logger.warning(f"Error retrieving from cache: {str(e)}")
            return None

    def set(self, url: str, content: str, reference: str, instruction: str = "") -> bool:
        """Cache a crawl result for a URL

        Args:
            url: The URL being cached
            content: The crawled content
            reference: The reference URL
            instruction: Optional instruction/query string

        Returns:
            bool: True if caching succeeded, False otherwise
        """
        if not self.redis_client:
            logger.debug("Redis client not available, skipping cache storage")
            return False

        try:
            cache_key = self._generate_cache_key(url, instruction)
            cache_data = {
                "content": content,
                "reference": reference,
                "cached_at": datetime.now().isoformat(),
                "url": url
            }

            self.redis_client.setex(
                cache_key,
                self.ttl_seconds,
                json.dumps(cache_data, ensure_ascii=False)
            )
            logger.debug(f"Cached result for URL: {url}")
            return True
        except Exception as e:
            logger.warning(f"Error storing in cache: {str(e)}")
            return False

    def get_batch(self, urls: list, instruction: str = "") -> Dict[str, Optional[Dict[str, Any]]]:
        """Get cached results for multiple URLs

        Args:
            urls: List of URLs to retrieve from cache
            instruction: Optional instruction/query string

        Returns:
            Dict: Mapping of URLs to cached results (None if not found)
        """
        if not self.redis_client:
            logger.debug("Redis client not available, skipping batch cache retrieval")
            return {url: None for url in urls}

        try:
            results = {}
            for url in urls:
                results[url] = self.get(url, instruction)
            return results
        except Exception as e:
            logger.warning(f"Error retrieving batch from cache: {str(e)}")
            return {url: None for url in urls}

    def set_batch(self, items: list, instruction: str = "") -> int:
        """Cache multiple crawl results

        Args:
            items: List of dicts with 'url', 'content', and 'reference' keys
            instruction: Optional instruction/query string

        Returns:
            int: Number of items successfully cached
        """
        if not self.redis_client:
            logger.debug("Redis client not available, skipping batch cache storage")
            return 0

        try:
            success_count = 0
            for item in items:
                if self.set(item.get("url"), item.get("content"), item.get("reference"), instruction):
                    success_count += 1
            return success_count
        except Exception as e:
            logger.warning(f"Error storing batch in cache: {str(e)}")
            return 0

    def clear_url(self, url: str, instruction: str = "") -> bool:
        """Clear cache for a specific URL

        Args:
            url: The URL to clear from cache
            instruction: Optional instruction/query string

        Returns:
            bool: True if cleared successfully, False otherwise
        """
        if not self.redis_client:
            return False

        try:
            cache_key = self._generate_cache_key(url, instruction)
            self.redis_client.delete(cache_key)
            logger.debug(f"Cleared cache for URL: {url}")
            return True
        except Exception as e:
            logger.warning(f"Error clearing cache: {str(e)}")
            return False

    def clear_all(self) -> bool:
        """Clear all crawl cache entries

        Returns:
            bool: True if cleared successfully, False otherwise
        """
        if not self.redis_client:
            return False

        try:
            # Use pattern matching to delete all crawl_cache keys
            cursor = 0
            deleted_count = 0
            while True:
                cursor, keys = self.redis_client.scan(cursor, match="crawl_cache:*", count=100)
                if keys:
                    deleted_count += self.redis_client.delete(*keys)
                if cursor == 0:
                    break
            logger.info(f"Cleared {deleted_count} cache entries")
            return True
        except Exception as e:
            logger.warning(f"Error clearing all cache: {str(e)}")
            return False

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics

        Returns:
            Dict: Cache statistics including total entries and memory usage
        """
        if not self.redis_client:
            return {"status": "unavailable"}

        try:
            cursor = 0
            total_entries = 0
            while True:
                cursor, keys = self.redis_client.scan(cursor, match="crawl_cache:*", count=100)
                total_entries += len(keys)
                if cursor == 0:
                    break

            info = self.redis_client.info()
            return {
                "status": "available",
                "total_entries": total_entries,
                "memory_used": info.get("used_memory_human", "unknown"),
                "redis_version": info.get("redis_version", "unknown")
            }
        except Exception as e:
            logger.warning(f"Error getting cache stats: {str(e)}")
            return {"status": "error", "error": str(e)}

    def is_available(self) -> bool:
        """Check if cache is available

        Returns:
            bool: True if Redis connection is available, False otherwise
        """
        if not self.redis_client:
            return False

        try:
            self.redis_client.ping()
            return True
        except Exception:
            return False
