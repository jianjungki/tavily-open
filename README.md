# SearCrawl

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## Introduction

SearCrawl is an open-source search and crawling tool based on SearXNG and Crawl4AI, serving as an open-source alternative to Tavily. It provides similar search and web content extraction capabilities while being fully open-source and customizable.

Key Features:
- Search results retrieval through SearXNG search engine
- Web content crawling and processing using Crawl4AI
- Clean RESTful API interface
- Customizable search engine and crawling parameters
- Modern Python packaging with pyproject.toml
- Comprehensive test suite
- Code quality tools integration

## Installation

### Prerequisites

- Python 3.8+
- SearXNG instance (local or remote)
- Playwright browser (installation script handles automatically)

### Installation Steps

1. Clone the repository
```bash
git clone https://github.com/Owoui/SearXNG-Crawl4AI.git
cd SearXNG-Crawl4AI
```

2. Create and activate a virtual environment
```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

3. Install the package
```bash
# For production use
pip install -e .

# For development (includes testing and code quality tools)
pip install -e ".[dev]"
```

4. Configure environment variables
```bash
cp .env.example .env
# Edit .env file and modify configurations as needed
```

## Usage

### Start the Service

Using the installed command:
```bash
searcrawl
```

Or directly with Python:
```bash
python -m searcrawl.main
```

Service runs by default at `http://0.0.0.0:3000`

### API Endpoints

#### Search Endpoint

```
POST /search
```

Request body:
```json
{
  "query": "search keywords",
  "limit": 10,
  "disabled_engines": "wikipedia__general,currency__general,wikidata__general,duckduckgo__general,google__general,lingva__general,qwant__general,startpage__general,dictzone__general,mymemory translated__general,brave__general",
  "enabled_engines": "baidu__general"
}
```

Parameters:
- `query`: Search query string (required)
- `limit`: Maximum number of results to return, default is 10
- `disabled_engines`: List of disabled search engines, comma-separated
- `enabled_engines`: List of enabled search engines, comma-separated

Response:
```json
{
  "content": "Crawled web content...",
  "success_count": 8,
  "failed_urls": ["https://example.com/failed1", "https://example.com/failed2"]
}
```

### API Documentation

Once the service is running, visit:
- Swagger UI: `http://localhost:3000/docs`
- ReDoc: `http://localhost:3000/redoc`

## Deployment Notes

When deploying SearXNG, pay special attention to the following configuration:

1. Modify the SearXNG settings.yml configuration file:
   - Add or modify formats configuration in the `search` section:
   ```yaml
   search:
     formats:
       - html
       - json
   ```
   This configuration ensures SearXNG returns JSON format search results, which is necessary for SearCrawl to function properly.

## Configuration Options

The following parameters can be configured through the `.env` file:

```env
# SearXNG Configuration
SEARXNG_HOST=localhost
SEARXNG_PORT=8080
SEARXNG_BASE_PATH=/search

# API Service Configuration
API_HOST=0.0.0.0
API_PORT=3000

# Crawler Configuration
DEFAULT_SEARCH_LIMIT=10
CONTENT_FILTER_THRESHOLD=0.6
WORD_COUNT_THRESHOLD=10

# Search Engine Configuration
DISABLED_ENGINES=wikipedia__general,currency__general,...
ENABLED_ENGINES=baidu__general
```

## Development

### Project Structure

```
.
├── src/
│   └── searcrawl/
│       ├── __init__.py      # Package initialization
│       ├── config.py         # Configuration loading module
│       ├── crawler.py        # Crawler functionality module
│       ├── logger.py         # Logging module
│       └── main.py           # Main program and API endpoints
├── tests/
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_crawler.py
│   └── test_api.py
├── .env.example              # Environment variables example
├── .gitignore                # Git ignore patterns
├── .pre-commit-config.yaml   # Pre-commit hooks configuration
├── pyproject.toml            # Project metadata and dependencies
├── requirements.txt          # Production dependencies
├── requirements-dev.txt      # Development dependencies
├── LICENSE                   # MIT License
└── README.md                 # Project documentation
```

### Development Setup

1. Install development dependencies:
```bash
pip install -e ".[dev]"
```

2. Install pre-commit hooks:
```bash
pre-commit install
```

3. Run tests:
```bash
pytest
```

4. Run tests with coverage:
```bash
pytest --cov=searcrawl --cov-report=html
```

5. Format code:
```bash
black src/ tests/
```

6. Lint code:
```bash
ruff check src/ tests/
```

7. Type checking:
```bash
mypy src/
```

### Code Quality Tools

This project uses several tools to maintain code quality:

- **Black**: Code formatting
- **Ruff**: Fast Python linter
- **MyPy**: Static type checking
- **isort**: Import sorting
- **pytest**: Testing framework
- **pre-commit**: Git hooks for code quality

### Extending Functionality

To extend functionality, you can modify the following files:

- `src/searcrawl/crawler.py`: Add new crawling strategies or content processing methods
- `src/searcrawl/main.py`: Add new API endpoints
- `src/searcrawl/config.py`: Add new configuration parameters

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_crawler.py

# Run with coverage report
pytest --cov=searcrawl --cov-report=term-missing

# Run with verbose output
pytest -v
```

### Building Distribution

```bash
# Build source and wheel distributions
python -m build

# The built distributions will be in the dist/ directory
```

## License

[MIT](LICENSE)

## Acknowledgments

- [SearXNG](https://github.com/searxng/searxng) - Privacy-respecting meta search engine
- [Crawl4AI](https://github.com/unclecode/crawl4ai) - Web crawling library for AI
- [FastAPI](https://fastapi.tiangolo.com/) - Modern, fast web framework

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

Make sure to:
- Update tests as appropriate
- Follow the code style (enforced by pre-commit hooks)
- Update documentation as needed
