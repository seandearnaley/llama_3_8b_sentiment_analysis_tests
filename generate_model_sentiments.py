from functools import lru_cache

import diskcache as dc
import FinNews as fn
import yfinance as yf

from utils.analysis_utils import (
    clean_company_name,
    filter_recent_news,
    test_models,
)
from utils.context import AnalysisContext, logger
from utils.error_decorator import handle_errors
from utils.file_utils import (
    load_config,
)
from utils.web_scraper import get_content

CONFIG_FILE = "config.yaml"
CACHE_DIR = "cache"
CACHE_TIMEOUT = 24 * 60 * 60  # 24 hours in seconds

logger.debug("Logging is configured.")


cache = dc.Cache(CACHE_DIR)


@lru_cache(maxsize=None)
@handle_errors()
def get_company_name(ticker_symbol: str) -> str:
    ticker = yf.Ticker(ticker_symbol)
    if "shortName" not in ticker.info:
        raise ValueError(f"Invalid security symbol: {ticker_symbol}")
    return clean_company_name(ticker.info["longName"])


@handle_errors([])
def get_news(ticker_symbol: str, max_news_age: int, max_news_items: int) -> list:
    cache_key = f"news_{ticker_symbol}"
    cached_news = cache.get(cache_key)
    if cached_news:
        logger.info("Returning cached news data.")
        # Ensure the cached data is a list
        if isinstance(cached_news, list):
            return cached_news
        else:
            logger.error("Cached news data is not a list.")
            return []

    yahoo_feed = fn.Yahoo(topics=["$" + ticker_symbol])
    logger.info("Getting news from Yahoo Finance...")
    news_object = yahoo_feed.get_news()
    filtered_news = filter_recent_news(news_object, max_news_age, max_news_items)

    cache.set(cache_key, filtered_news, expire=CACHE_TIMEOUT)
    return filtered_news


@handle_errors({})
def get_content_map(news_object: list, company_name: str, ticker_symbol: str) -> dict:
    content_map = {}
    logger.info("Getting content from the news articles...")
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
    logger.info(f"Company: {company_name} ({ticker_symbol})")
    return True


def main():
    config = load_config(CONFIG_FILE)
    ticker_symbol = config.get("ticker_symbol")
    company_name = get_company_name(ticker_symbol)
    max_news_age = config.get("max_news_age", 1)
    max_news_items = config.get("max_news_items", 5)
    models_to_test = config.get("models_to_test", [])
    sample_size = config.get("sample_size", 5)
    default_temperature = config.get("default_temperature", 0.2)
    context_window_size = config.get("context_window_size", 8192)
    num_tokens_to_predict = config.get("num_tokens_to_predict", 1024)
    sentiment_save_folder = config.get("sentiment_save_folder", "sentiments")

    if not company_name or not ticker_symbol:
        raise ValueError("Invalid company name or ticker symbol.")

    if len(models_to_test) == 0:
        raise ValueError("No models to test.")

    log_company_info(company_name, ticker_symbol)

    news_object = get_news(ticker_symbol, max_news_age, max_news_items)
    content_map = get_content_map(news_object, company_name, ticker_symbol)

    context = AnalysisContext(
        content_map=content_map,
        company_name=company_name,
        news_object=news_object,
        ticker_symbol=ticker_symbol,
        default_temperature=default_temperature,
        context_window_size=context_window_size,
        num_tokens_to_predict=num_tokens_to_predict,
        sentiment_save_folder=sentiment_save_folder,
    )
    test_models(models_to_test, sample_size, context)


if __name__ == "__main__":
    main()
