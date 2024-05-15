from typing import Optional

import requests
from bs4 import BeautifulSoup
from requests.exceptions import RequestException


def fetch_response(link: str) -> Optional[requests.Response]:
    try:
        response = requests.get(link)
        response.raise_for_status()
        return response
    except RequestException:
        # logging.error(f"Failed to get article content from {link}: {e}")
        return None


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


def get_content(link: str, company_name: str, ticker_symbol: str) -> str:
    response = fetch_response(link)
    if not response:
        return ""
    soup = BeautifulSoup(response.text, "html.parser")
    return extract_relevant_content(soup, company_name, ticker_symbol)
