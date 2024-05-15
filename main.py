#!/usr/bin/env python3
import logging
from functools import wraps

import FinNews as fn
import requests_cache
import yaml
import yfinance as yf

from utils import (
    clean_company_name,
    filter_recent_news,
    test_model,
)
from web_scraper import get_content

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Initialize requests cache
requests_cache.install_cache(
    "news_cache", expire_after=3600
)  # Cache expires after 1 hour


def handle_errors(default_return=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logging.error(f"Error in {func.__name__}: {e}")
                return default_return

        return wrapper

    return decorator


def load_config(file_path: str) -> dict:
    with open(file_path, "r") as file:
        return yaml.safe_load(file)


@handle_errors()
def get_company_name(ticker_symbol: str) -> str:
    ticker = yf.Ticker(ticker_symbol)
    if "shortName" not in ticker.info:
        raise ValueError(f"Invalid security symbol: {ticker_symbol}")
    return clean_company_name(ticker.info["longName"])


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


def print_company_info(company_name, ticker_symbol):
    try:
        print(f"Company: {company_name} ({ticker_symbol})")
    except ValueError as e:
        print(e)
        return False
    return True


def test_models(
    models_to_test, sample_size, content_map, company_name, news_object, ticker_symbol
):
    for model_name in models_to_test:
        print(f"Testing model: {model_name}")
        for i in range(sample_size):
            test_model(
                model_name, i, content_map, company_name, news_object, ticker_symbol
            )
        print("")


def main():
    config = load_config("config.yaml")
    company_name = get_company_name(config["ticker_symbol"])
    if not print_company_info(company_name, config["ticker_symbol"]):
        return

    news_object = get_news(
        config["ticker_symbol"], config["max_news_age"], config["max_news_items"]
    )
    content_map = get_content_map(news_object, company_name, config["ticker_symbol"])

    test_models(
        config["models_to_test"],
        config["sample_size"],
        content_map,
        company_name,
        news_object,
        config["ticker_symbol"],
    )


if __name__ == "__main__":
    main()
