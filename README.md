# tavily-open

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

[中文文档](README_CN.md) | English

> 🔍 Open-source intelligent search and web crawling tool - An open-source alternative to Tavily

## 📖 Introduction

**tavily-open** is a powerful open-source search and web crawling tool built on SearXNG and Crawl4AI. It provides search and web content extraction capabilities similar to Tavily, while being fully open-source, customizable, and supporting distributed caching.

### ✨ Key Features

- 🔎 **Intelligent Search** - High-quality search results through SearXNG meta search engine
- 🕷️ **Smart Crawling** - Efficient web content extraction using Crawl4AI
- 🚀 **Distributed Caching** - Redis-based distributed caching to reduce redundant crawling and improve performance
- 🎯 **RESTful API** - Clean and easy-to-use API interface with Swagger documentation
- ⚙️ **Highly Customizable** - Flexible configuration for search engines, crawler parameters, and caching strategies
- 🔄 **Concurrent Processing** - Multi-threaded parallel crawling for improved throughput
- 🐳 **Docker Support** - One-click deployment with all dependencies included
- 🧪 **Comprehensive Testing** - Full test suite and code quality tools

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Client Application                          │
│                     (Web App / CLI / SDK)                            │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 │ HTTP POST /search
                                 │ { query, limit, engines }
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        tavily-open API Service                       │
│                      (FastAPI + Uvicorn)                             │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
                    ▼                         ▼
         ┌──────────────────┐      ┌──────────────────┐
         │  SearXNG Search  │      │   Redis Cache    │
         │  Meta Engine     │      │  Distributed     │
         └────────┬─────────┘      └────────┬─────────┘
                  │                         │
                  │ Return URL List         │ Cache Hit Check
                  │ + Metadata              │
                  ▼                         │
         ┌──────────────────┐              │
         │  URL Dedup &     │◄─────────────┘
         │  Cache Query     │
         └────────┬─────────┘
                  │
                  │ URLs to Crawl
                  │
         ┌────────▼─────────┐
         │  Crawl4AI Pool   │
         │  (Multi-thread)  │
         └────────┬─────────┘
                  │
                  │ Extract Content
                  │
         ┌────────▼─────────┐
         │ Content Filter   │
         │ & Processing     │
         └────────┬─────────┘
                  │
                  │ Store to Cache
                  ▼
         ┌──────────────────┐
         │ Return Results   │
         │ + Statistics     │
         └──────────────────┘
```

### 🔄 Workflow Explanation

1. **Receive Request** - Client sends search query with parameters (keywords, result count, search engine config)
2. **Cache Check** - System first checks Redis cache for previously crawled content (if caching enabled)
3. **Search Phase** - Query is sent to SearXNG to retrieve relevant URL list and metadata
4. **URL Deduplication** - Deduplicate search results and check cache hit status
5. **Parallel Crawling** - Use Crawl4AI thread pool to concurrently crawl uncached URLs
6. **Content Processing** - Extract, clean, and format web content, filter low-quality content
7. **Cache Storage** - Store successfully crawled content to Redis with expiration time
8. **Return Results** - Return processed content with statistics (cache hits, newly crawled, failures)

### 🧩 Core Components

| Component | Description | Tech Stack |
|-----------|-------------|------------|
| **API Server** | RESTful API interface | FastAPI + Uvicorn |
| **Search Engine** | Privacy-friendly meta search | SearXNG |
| **Crawler Engine** | Intelligent content extraction | Crawl4AI + Playwright |
| **Cache Layer** | Distributed cache storage | Redis |
| **Concurrent Processing** | Multi-threaded crawling | ThreadPoolExecutor |

## 🚀 Quick Start

### 📋 Prerequisites

- Python 3.8+
- SearXNG instance (local or remote)
- Playwright browser (automatically handled by installation script)
- Redis (optional, for caching - included in Docker setup)

### 🐳 Docker Deployment (Recommended)

The easiest way to deploy all services with Docker Compose:

```bash
# 1. Clone the repository
git clone https://github.com/Owoui/SearXNG-Crawl4AI.git
cd SearXNG-Crawl4AI

# 2. Configure environment variables
cp .env.example .env
# Edit .env file as needed

# 3. Start all services (app + Redis)
docker-compose up -d

# 4. View logs
docker-compose logs -f

# 5. Stop services
docker-compose down
```

The service will be available at `http://localhost:3000`

### 💻 Manual Installation

#### 1. Clone the Repository

```bash
git clone https://github.com/Owoui/SearXNG-Crawl4AI.git
cd SearXNG-Crawl4AI
```

#### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### 3. Install Dependencies

```bash
# Production
pip install -e .

# Development (includes testing and code quality tools)
pip install -e ".[dev]"
```

#### 4. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env file to configure SearXNG, Redis, etc.
```

#### 5. Start the Service

```bash
# Using CLI tool
searcrawl

# Or directly with Python
python -m searcrawl.main
```

The service runs by default at `http://0.0.0.0:3000`

> **Note:** The package name remains `searcrawl` for backward compatibility, but the project is now known as **tavily-open**.

## 📚 Usage Guide

### 🔌 API Endpoints

#### Search Endpoint

```http
POST /search
Content-Type: application/json
```

**Request Example:**

```json
{
  "query": "artificial intelligence latest developments",
  "limit": 10,
  "disabled_engines": "wikipedia__general,currency__general,wikidata__general",
  "enabled_engines": "baidu__general,bing__general"
}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | ✅ | Search keywords |
| `limit` | integer | ❌ | Number of results to return (default: 10) |
| `disabled_engines` | string | ❌ | Disabled search engines (comma-separated) |
| `enabled_engines` | string | ❌ | Enabled search engines (comma-separated) |

**Response Example:**

```json
{
  "results": [
    {
      "content": "Artificial Intelligence (AI) is a branch of computer science...",
      "reference": "https://example.com/ai-article"
    },
    {
      "content": "The latest GPT-4 model demonstrates powerful capabilities...",
      "reference": "https://example.com/gpt4-news"
    }
  ],
  "success_count": 8,
  "failed_urls": [
    "https://example.com/timeout-page"
  ],
  "cache_hits": 3,
  "newly_crawled": 5
}
```

**Response Fields:**

| Field | Description |
|-------|-------------|
| `results` | Array of crawled content with source URLs |
| `success_count` | Total number of successful results (cached + newly crawled) |
| `failed_urls` | List of URLs that failed to crawl |
| `cache_hits` | Number of results retrieved from cache (when caching enabled) |
| `newly_crawled` | Number of newly crawled results (when caching enabled) |

### 📖 API Documentation

After starting the service, visit the following URLs for interactive API documentation:

- **Swagger UI**: `http://localhost:3000/docs`
- **ReDoc**: `http://localhost:3000/redoc`

### 🔧 Configuration Options

Configure system parameters through the `.env` file:

```env
# ========== SearXNG Configuration ==========
SEARXNG_HOST=localhost
SEARXNG_PORT=8080
SEARXNG_BASE_PATH=/search

# ========== API Service Configuration ==========
API_HOST=0.0.0.0
API_PORT=3000

# ========== Crawler Configuration ==========
DEFAULT_SEARCH_LIMIT=10          # Default search result count
CONTENT_FILTER_THRESHOLD=0.6     # Content filter threshold
WORD_COUNT_THRESHOLD=10          # Minimum word count threshold
CRAWLER_POOL_SIZE=4              # Crawler thread pool size

# ========== Cache Configuration ==========
CACHE_ENABLED=true               # Enable/disable caching
REDIS_URL=redis://localhost:6379/0
CACHE_TTL_HOURS=24               # Cache expiration time (hours)

# ========== Search Engine Configuration ==========
DISABLED_ENGINES=wikipedia__general,currency__general,wikidata__general
ENABLED_ENGINES=baidu__general,bing__general
```

### 💾 Cache Configuration Details

tavily-open supports Redis-based distributed caching for significant performance improvements:

- **CACHE_ENABLED**: Enable/disable caching (true/false)
- **REDIS_URL**: Redis connection URL (default: redis://localhost:6379/0)
- **CACHE_TTL_HOURS**: Cache expiration time in hours (default: 24)

**Cache Benefits:**
- ✅ Reduce redundant crawling, save bandwidth and time
- ✅ Multi-instance cache sharing for improved overall efficiency
- ✅ Automatic expiration mechanism ensures data freshness

For detailed cache implementation documentation, see: [`CACHE_IMPLEMENTATION.md`](CACHE_IMPLEMENTATION.md)

## 🛠️ Development Guide

### 📁 Project Structure

```
tavily-open/
├── src/
│   └── searcrawl/
│       ├── __init__.py           # Package initialization
│       ├── cache.py              # Redis cache manager
│       ├── config.py             # Configuration loader
│       ├── crawler.py            # Crawler core logic
│       ├── logger.py             # Logging module
│       └── main.py               # API service entry
├── tests/
│   ├── __init__.py
│   ├── test_config.py            # Configuration tests
│   ├── test_crawler.py           # Crawler tests
│   └── test_api.py               # API tests
├── .env.example                  # Environment variables example
├── .gitignore                    # Git ignore rules
├── .pre-commit-config.yaml       # Pre-commit hooks config
├── docker-compose.yml            # Docker Compose config
├── Dockerfile                    # Docker image definition
├── pyproject.toml                # Project metadata and dependencies
├── requirements.txt              # Production dependencies
├── requirements-dev.txt          # Development dependencies
├── CACHE_IMPLEMENTATION.md       # Cache system documentation
├── LICENSE                       # MIT License
└── README.md                     # Project documentation
```

### 🔨 Development Setup

```bash
# 1. Install development dependencies
pip install -e ".[dev]"

# 2. Install pre-commit hooks
pre-commit install

# 3. Run tests
pytest

# 4. Run tests with coverage report
pytest --cov=searcrawl --cov-report=html

# 5. Format code
black src/ tests/

# 6. Lint code
ruff check src/ tests/

# 7. Type checking
mypy src/
```

### 🧪 Code Quality Tools

| Tool | Purpose | Command |
|------|---------|---------|
| **Black** | Code formatting | `black src/ tests/` |
| **Ruff** | Fast Python linter | `ruff check src/ tests/` |
| **MyPy** | Static type checking | `mypy src/` |
| **isort** | Import sorting | `isort src/ tests/` |
| **pytest** | Testing framework | `pytest` |
| **pre-commit** | Git hooks | `pre-commit run --all-files` |

### 🔧 Extending Functionality

Modify the following files to extend functionality:

- [`src/searcrawl/cache.py`](src/searcrawl/cache.py) - Extend caching strategies or add new cache backends
- [`src/searcrawl/crawler.py`](src/searcrawl/crawler.py) - Add new crawling strategies or content processing methods
- [`src/searcrawl/main.py`](src/searcrawl/main.py) - Add new API endpoints
- [`src/searcrawl/config.py`](src/searcrawl/config.py) - Add new configuration parameters

### 📦 Building Distribution

```bash
# Build source and wheel distributions
python -m build

# Built distributions will be in the dist/ directory
```

## 🚢 Deployment Notes

### SearXNG Configuration

When deploying SearXNG, pay special attention to the following configuration:

In SearXNG's `settings.yml` configuration file, add or modify the `formats` configuration in the `search` section:

```yaml
search:
  formats:
    - html
    - json
```

This configuration ensures SearXNG returns JSON format search results, which is necessary for tavily-open to function properly.

### Production Environment Recommendations

- ✅ Use Docker Compose for deployment, easier to manage
- ✅ Enable Redis caching for performance improvement
- ✅ Configure appropriate `CRAWLER_POOL_SIZE` to balance performance and resources
- ✅ Set reasonable `CACHE_TTL_HOURS` to balance freshness and efficiency
- ✅ Use reverse proxy (e.g., Nginx) for SSL and load balancing

## 🤝 Contributing

Contributions are welcome! If you'd like to contribute to the project, please follow these steps:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/AmazingFeature`)
3. **Commit your changes** (`git commit -m 'Add some AmazingFeature'`)
4. **Push to the branch** (`git push origin feature/AmazingFeature`)
5. **Create a Pull Request**

### Contribution Requirements

- ✅ Update relevant test cases
- ✅ Follow code style (enforced by pre-commit hooks)
- ✅ Update related documentation
- ✅ Ensure all tests pass

## 📄 License

This project is licensed under the [MIT License](LICENSE)

## 🙏 Acknowledgments

This project is built on the following excellent open-source projects:

- **[SearCrawl](https://github.com/Owoui/SearXNG-Crawl4AI)** - The predecessor of this project, thanks for the original contributions
- **[SearXNG](https://github.com/searxng/searxng)** - Privacy-respecting meta search engine
- **[Crawl4AI](https://github.com/unclecode/crawl4ai)** - Web crawling library designed for AI
- **[FastAPI](https://fastapi.tiangolo.com/)** - Modern, fast web framework
- **[Redis](https://redis.io/)** - High-performance in-memory data store

Thanks to all developers who contributed to these projects!

## 📞 Contact

- **Issues**: [GitHub Issues](https://github.com/Owoui/SearXNG-Crawl4AI/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Owoui/SearXNG-Crawl4AI/discussions)

## 🗺️ Roadmap

- [ ] Support for more search engines
- [ ] Add GraphQL API
- [ ] Implement result ranking and relevance scoring
- [ ] Support custom content extraction rules
- [ ] Add Web UI management interface
- [ ] Support more cache backends (Memcached, DynamoDB, etc.)
- [ ] Implement distributed crawling cluster

---

<div align="center">

**If this project helps you, please give us a ⭐️**

Made with ❤️ by the tavily-open community

</div>
