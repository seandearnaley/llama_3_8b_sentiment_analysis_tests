from typing import Optional

import requests
from bs4 import BeautifulSoup

from utils.error_decorator import handle_errors

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
}

session = requests.Session()
session.headers.update(HEADERS)


@handle_errors(default_return=None)
def fetch_response(link: str) -> Optional[requests.Response]:
    response = session.get(link)
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
