import asyncio
import aiohttp
from aiohttp import ClientTimeout
from typing import Optional, Dict, Any
from .config import READER_URL, READER_API_KEY
from .logger import logger

async def fetch_with_reader(url: str) -> Optional[Dict[str, Any]]:
    """
    Asynchronously fetches the content of a URL using the Jina Reader service.

    Args:
        url (str): The URL to fetch.

    Returns:
        Optional[Dict[str, Any]]: A dictionary containing the fetched content and metadata,
                                     or None if the fetch failed.
    """
    reader_api_url = f"{READER_URL}/{url}"
    headers = {
        "Accept": "application/json",
        "X-Respond-With": "markdown",
    }
    if READER_API_KEY:
        headers["Authorization"] = f"Bearer {READER_API_KEY}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(reader_api_url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    content = await response.text()
                    if content:
                        logger.info(f"Successfully fetched content for {url} with Jina Reader.")
                        return {"content": content, "reference": url}
                    else:
                        logger.warning(f"Jina Reader returned no content for {url}.")
                        return None
                else:
                    error_text = await response.text()
                    logger.error(
                        f"Failed to fetch {url} with Jina Reader. Status: {response.status}, Response: {error_text}"
                    )
                    return None
    except asyncio.TimeoutError:
        logger.error(f"Timeout error when fetching {url} with Jina Reader.")
        return None
    except aiohttp.ClientError as e:
        logger.error(f"AIOHTTP client error when fetching {url} with Jina Reader: {e}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred when fetching {url} with Jina Reader: {e}")
        return None
