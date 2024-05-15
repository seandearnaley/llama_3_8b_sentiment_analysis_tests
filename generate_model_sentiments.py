#!/usr/bin/env python3
import logging
from functools import lru_cache

import FinNews as fn
import requests_cache
import yfinance as yf

from utils.analysis_utils import (
    AnalysisContext,
    clean_company_name,
    filter_recent_news,
    test_models,
)
from utils.error_decorator import handle_errors
from utils.file_utils import (
    load_config,
)
from utils.web_scraper import get_content

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Initialize requests cache
requests_cache.install_cache(
    "news_cache", expire_after=3600
)  # Cache expires after 1 hour


@lru_cache(maxsize=None)
@handle_errors()
def get_company_name(ticker_symbol: str) -> str:
    ticker = yf.Ticker(ticker_symbol)
    if "shortName" not in ticker.info:
        raise ValueError(f"Invalid security symbol: {ticker_symbol}")
    return clean_company_name(ticker.info["longName"])


@lru_cache(maxsize=None)
@handle_errors([])
def get_news(ticker_symbol: str, max_news_age: int, max_news_items: int) -> list:
    yahoo_feed = fn.Yahoo(topics=["$" + ticker_symbol])
    logging.info("Getting news from Yahoo Finance...")
    news_object = yahoo_feed.get_news()
    return filter_recent_news(news_object, max_news_age, max_news_items)


@handle_errors({})
def get_content_map(news_object: list, company_name: str, ticker_symbol: str) -> dict:
    content_map = {}
    logging.info("Getting content from the news articles...")
    for news in news_object:
        url = news["link"]
        content = news["summary"] if news["summary"][-1] != "?" else ""
        extra_content = get_content(url, company_name, ticker_symbol)
        if extra_content:
            content += " " + extra_content
        if content:
            content_map[url] = content
    return content_map


@handle_errors(False)
def log_company_info(company_name: str, ticker_symbol: str) -> bool:
    if not company_name or not ticker_symbol:
        raise ValueError("Invalid company name or ticker symbol.")
    logging.info(f"Company: {company_name} ({ticker_symbol})")
    return True


def main():
    config = load_config("config.yaml")
    company_name = get_company_name(config["ticker_symbol"])

    log_company_info(company_name, config["ticker_symbol"])

    news_object = get_news(
        config["ticker_symbol"], config["max_news_age"], config["max_news_items"]
    )
    content_map = get_content_map(news_object, company_name, config["ticker_symbol"])

    context = AnalysisContext(
        content_map=content_map,
        company_name=company_name,
        news_object=news_object,
        ticker_symbol=config["ticker_symbol"],
    )
    test_models(config["models_to_test"], config["sample_size"], context)


if __name__ == "__main__":
    main()
