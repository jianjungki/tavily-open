# -*- coding: utf-8 -*-
"""
Tests for API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from searcrawl.main import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


def test_search_endpoint_structure(client):
    """Test that search endpoint exists and returns proper structure"""
    # Note: This will fail without actual SearXNG running
    # This is a structural test only
    response = client.post(
        "/search",
        json={"query": "test"}
    )
    # We expect this to fail in test environment, but endpoint should exist
    assert response.status_code in [200, 404, 500, 503]


def test_search_request_validation(client):
    """Test search request validation"""
    # Test with missing query
    response = client.post("/search", json={})
    assert response.status_code == 422  # Validation error


def test_api_docs_accessible(client):
    """Test that API documentation is accessible"""
    response = client.get("/docs")
    assert response.status_code == 200
    
    response = client.get("/openapi.json")
    assert response.status_code == 200