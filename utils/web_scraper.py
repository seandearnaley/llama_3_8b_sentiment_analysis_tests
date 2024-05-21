from typing import Optional

import requests
import requests_cache
from bs4 import BeautifulSoup

from utils.context import logger
from utils.error_decorator import handle_errors

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
}


session = requests_cache.CachedSession("news_cache", expire_after=86400)
session.headers.update(HEADERS)


@handle_errors(default_return=None)
def fetch_response(link: str) -> Optional[requests.Response]:
    response = session.get(link)
    if getattr(response, "from_cache", False):
        logger.info(f"Cache hit for URL: {link}")
    else:
        logger.info(f"Cache miss for URL: {link}")
    response.raise_for_status()
    return response


@handle_errors(default_return="")
def extract_relevant_content(
    soup: BeautifulSoup, company_name: str, ticker_symbol: str
) -> str:
    content = []
    for tag in soup.find_all(["p", "h2"]):
        lower_text = tag.text.lower()
        if company_name in lower_text or ticker_symbol in lower_text:
            text = tag.text.strip().replace("\n", " ")
            content.append(text)
    return "… ".join(content) if content else ""


@handle_errors(default_return="")
def get_content(link: str, company_name: str, ticker_symbol: str) -> str:
    response = fetch_response(link)
    if not response:
        return ""
    soup = BeautifulSoup(response.text, "html.parser")
    return extract_relevant_content(soup, company_name, ticker_symbol)


# Add a function to inspect the cache
def inspect_cache():
    logger.info("Inspecting cache contents...")
    for response in session.cache.filter():
        logger.info(
            f"Cached URL: {response.url}, from_cache: {response.from_cache}, created_at: {response.created_at}, expires: {response.expires}"
        )


# Call inspect_cache to log cache contents
# inspect_cache()
