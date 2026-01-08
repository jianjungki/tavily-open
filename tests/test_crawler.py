# -*- coding: utf-8 -*-
"""
Tests for crawler module
"""

import pytest
from searcrawl.crawler import WebCrawler


def test_markdown_to_text_regex():
    """Test markdown to text conversion using regex"""
    markdown_text = """
    # Heading
    
    This is **bold** and *italic* text.
    
    - List item 1
    - List item 2
    
    [Link](https://example.com)
    """
    
    result = WebCrawler.markdown_to_text_regex(markdown_text)
    
    assert "Heading" in result
    assert "bold" in result
    assert "italic" in result
    assert "**" not in result
    assert "*" not in result
    assert "[Link]" not in result
    assert "https://" not in result


def test_markdown_to_text():
    """Test markdown to text conversion using markdown library"""
    markdown_text = """
    # Heading
    
    This is a paragraph with **bold** text.
    """
    
    result = WebCrawler.markdown_to_text(markdown_text)
    
    assert "Heading" in result
    assert "bold" in result
    assert len(result) > 0


@pytest.mark.asyncio
async def test_webcrawler_initialization():
    """Test WebCrawler initialization"""
    crawler = WebCrawler()
    assert crawler.crawler is None
    
    # Note: Full initialization requires browser setup
    # This is a basic structure test only


def test_webcrawler_creation():
    """Test WebCrawler object creation"""
    crawler = WebCrawler()
    assert isinstance(crawler, WebCrawler)
    assert hasattr(crawler, 'initialize')
    assert hasattr(crawler, 'close')
    assert hasattr(crawler, 'crawl_urls')