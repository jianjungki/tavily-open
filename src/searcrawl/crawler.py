# -*- coding: utf-8 -*-
"""
Crawler Module - Provides web crawling and content processing functionality

This module provides web crawling and content processing functionality.
It encapsulates the AsyncWebCrawler from crawl4ai library and provides
high-level methods for crawling web pages and processing their content.
"""

from typing import List, Dict, Any
from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    CacheMode,
)
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import PruningContentFilter
import markdown
from bs4 import BeautifulSoup
import re
import http.client
from codecs import encode
import json
from fastapi import HTTPException
from loguru import logger

# Import configuration
from searcrawl.config import (
    SEARXNG_HOST,
    SEARXNG_PORT,
    SEARXNG_BASE_PATH,
    DISABLED_ENGINES,
    ENABLED_ENGINES,
    SEARCH_LANGUAGE,
    CONTENT_FILTER_THRESHOLD,
    WORD_COUNT_THRESHOLD
)


class WebCrawler:
    """Web crawler class that encapsulates web crawling and content processing functionality"""

    def __init__(self):
        """Initialize crawler instance"""
        self.crawler = None
        logger.info("Initializing WebCrawler instance")

    async def initialize(self) -> None:
        """Initialize AsyncWebCrawler instance

        Must be called before using the crawler
        """
        # Configure browser
        browser_config = BrowserConfig(headless=True, verbose=True)
        # Initialize crawler
        self.crawler = await AsyncWebCrawler(config=browser_config).__aenter__()
        logger.info("AsyncWebCrawler initialization completed")

    async def close(self) -> None:
        """Close crawler instance and release resources"""
        if self.crawler:
            await self.crawler.__aexit__(None, None, None)
            logger.info("AsyncWebCrawler closed")

    @staticmethod
    def markdown_to_text_regex(markdown_str: str) -> str:
        """Convert Markdown text to plain text using regular expressions

        Args:
            markdown_str: Markdown formatted text

        Returns:
            str: Converted plain text
        """
        # Remove heading symbols
        text = re.sub(r'#+\s*', '', markdown_str)

        # Remove links and images
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)

        # Remove bold, italic, and other emphasis markers
        text = re.sub(r'(\*\*|__)(.*?)\1', r'\2', text)
        text = re.sub(r'(\*|_)(.*?)\1', r'\2', text)

        # Remove list markers
        text = re.sub(r'^[\*\-\+]\s*', '', text, flags=re.MULTILINE)

        # Remove code blocks
        text = re.sub(r'`{3}.*?`{3}', '', text, flags=re.DOTALL)
        text = re.sub(r'`(.*?)`', r'\1', text)

        # Remove quote blocks
        text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)

        return text.strip()

    @staticmethod
    def markdown_to_text(markdown_str: str) -> str:
        """Convert Markdown text to plain text using markdown and BeautifulSoup libraries

        Args:
            markdown_str: Markdown formatted text

        Returns:
            str: Converted plain text
        """
        html = markdown.markdown(markdown_str, extensions=['fenced_code'])
        # Extract plain text using BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")

        text = soup.get_text(separator="\n")  # Preserve paragraph line breaks

        # Clean up extra blank lines
        cleaned_text = "\n".join([
            line.strip() for line in text.split("\n") if line.strip()
        ])

        return cleaned_text

    @staticmethod
    def make_searxng_request(
        query: str,
        limit: int = 10,
        disabled_engines: str = DISABLED_ENGINES,
        enabled_engines: str = ENABLED_ENGINES
    ) -> dict:
        """Send search request to SearXNG

        Args:
            query: Search query string
            limit: Limit on number of results to return
            disabled_engines: List of disabled search engines, comma-separated
            enabled_engines: List of enabled search engines, comma-separated

        Returns:
            dict: Search results returned by SearXNG

        Raises:
            Exception: Raised when request fails
        """
        try:
            conn = http.client.HTTPConnection(SEARXNG_HOST, SEARXNG_PORT)
            dataList = []
            boundary = 'wL36Yn8afVp8Ag7AmP8qZ0SA4n1v9T'

            form_data = {
                'q': query,
                'format': 'json',
                'language': SEARCH_LANGUAGE,
                'time_range': 'week',
                'safesearch': '2',
                'pageno': '1',
                'category_general': '1'
            }

            # Add form fields
            for key, value in form_data.items():
                dataList.append(encode('--' + boundary))
                dataList.append(encode(f'Content-Disposition: form-data; name={key};'))
                dataList.append(encode('Content-Type: {}'.format('text/plain')))
                dataList.append(encode(''))
                dataList.append(encode(str(value)))

            dataList.append(encode('--'+boundary+'--'))
            dataList.append(encode(''))
            body = b'\r\n'.join(dataList)

            headers = {
                'Cookie': f'disabled_engines={disabled_engines};enabled_engines={enabled_engines};method=POST',
                'User-Agent': 'Sear-Crawl4AI/1.0.0',
                'Accept': '*/*',
                'Host': f'{SEARXNG_HOST}:{SEARXNG_PORT}',
                'Connection': 'keep-alive',
                'Content-Type': f'multipart/form-data; boundary={boundary}'
            }

            logger.info(f"Sending search request to SearXNG: {query}")
            conn.request("POST", SEARXNG_BASE_PATH, body, headers)
            res = conn.getresponse()
            data = res.read()
            return json.loads(data.decode("utf-8"))
        except Exception as e:
            logger.error(f"SearXNG request failed: {str(e)}")
            raise Exception(f"Search request failed: {str(e)}")

    async def crawl_urls(self, urls: List[str], instruction: str) -> Dict[str, Any]:
        """Crawl multiple URLs and process content

        Args:
            urls: List of URLs to crawl
            instruction: Crawling instruction, typically a search query

        Returns:
            Dict[str, Any]: Dictionary containing processed content, success count, and failed URLs

        Raises:
            HTTPException: Raised when all URL crawls fail
        """
        try:
            # Check if crawler has been initialized
            if not self.crawler:
                logger.warning("Crawler not initialized, auto-initializing")
                await self.initialize()

            # Configure Markdown generator
            md_generator = DefaultMarkdownGenerator(
                content_filter=PruningContentFilter(threshold=CONTENT_FILTER_THRESHOLD),
                options={
                    "ignore_links": True,
                    "ignore_images": True,
                    "escape_html": False,
                }
            )

            # Configure crawler run parameters
            run_config = CrawlerRunConfig(
                word_count_threshold=WORD_COUNT_THRESHOLD,
                exclude_external_links=True,
                remove_overlay_elements=True,
                excluded_tags=['img', 'header', 'footer', 'iframe', 'nav'],
                process_iframes=True,
                markdown_generator=md_generator,
                cache_mode=CacheMode.BYPASS
            )

            logger.info(f"Starting to crawl URLs: {', '.join(urls)}")
            results = await self.crawler.arun_many(urls=urls, config=run_config)

            # Create a list to store crawl results from all successful URLs
            all_results = []
            failed_urls = []
            retry_urls = []

            # First crawl attempt processing
            for i, result in enumerate(results):
                try:
                    if result is None:
                        logger.debug(f"URL crawl result is None: {urls[i]}")
                        retry_urls.append(urls[i])
                        continue

                    if not hasattr(result, 'success'):
                        logger.debug(f"URL crawl result missing success attribute: {urls[i]}")
                        retry_urls.append(urls[i])
                        continue

                    if result.success:
                        if not hasattr(result, 'markdown') or not hasattr(result.markdown, 'fit_markdown'):
                            logger.debug(f"URL crawl result missing markdown content: {urls[i]}")
                            retry_urls.append(urls[i])
                            continue

                        # Add successful result's markdown content to the list
                        result_with_source = result.markdown.fit_markdown + '\n\n'
                        all_results.append(result_with_source)
                        logger.info(f"Successfully crawled URL: {urls[i]}")
                    else:
                        logger.debug(f"URL crawl failed: {urls[i]}")
                        retry_urls.append(urls[i])
                except Exception as e:
                    # Record URLs that need retry
                    retry_urls.append(urls[i])
                    error_msg = str(e)
                    logger.warning(f"URL first crawl attempt failed: {urls[i]}, error: {error_msg}")

            # If there are URLs to retry, perform second crawl attempt
            if retry_urls:
                logger.info(f"Retrying failed URLs: {', '.join(retry_urls)}")
                retry_results = await self.crawler.arun_many(urls=retry_urls, config=run_config)

                for i, result in enumerate(retry_results):
                    try:
                        if result is None:
                            logger.debug(f"Retry URL crawl result is None: {retry_urls[i]}")
                            failed_urls.append(retry_urls[i])
                            continue

                        if not hasattr(result, 'success'):
                            logger.debug(f"Retry URL crawl result missing success attribute: {retry_urls[i]}")
                            failed_urls.append(retry_urls[i])
                            continue

                        if result.success:
                            if not hasattr(result, 'markdown') or not hasattr(result.markdown, 'fit_markdown'):
                                logger.debug(f"Retry URL crawl result missing markdown content: {retry_urls[i]}")
                                failed_urls.append(retry_urls[i])
                                continue

                            # Add successful retry result to the list
                            result_with_source = result.markdown.fit_markdown + '\n\n'
                            all_results.append(result_with_source)
                            logger.info(f"Successfully crawled URL on retry: {retry_urls[i]}")
                        else:
                            logger.debug(f"Retry URL crawl still failed: {retry_urls[i]}")
                            failed_urls.append(retry_urls[i])
                    except Exception as e:
                        # Record finally failed URLs
                        failed_urls.append(retry_urls[i])
                        error_msg = str(e)
                        logger.error(f"URL second crawl attempt failed: {retry_urls[i]}, error: {error_msg}")

            if not all_results:
                logger.error("All URL crawls failed")
                raise HTTPException(status_code=500, detail="All URL crawls failed")

            # Join all successful results into a complete string with separators
            combined_content = '\n\n==========\n\n'.join(all_results)

            # Convert to plain text
            plain_text = self.markdown_to_text_regex(self.markdown_to_text(combined_content))

            response = {
                "content": plain_text,
                "success_count": len(all_results),
                "failed_urls": failed_urls
            }

            logger.info(f"Crawl completed, successful: {len(all_results)}, failed: {len(failed_urls)}")
            return response
        except Exception as e:
            logger.error(f"Exception occurred during crawling: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))