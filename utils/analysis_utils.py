import hashlib
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List

from langchain_community.llms import Ollama

from utils.file_utils import get_file_content, save_results
from utils.validation_utils import (
    parse_json_numeric_value,
    validate_json,
)

COMMON_SUFFIXES: List[str] = [
    "inc.",
    "incorporated",
    "corp.",
    "corporation",
    "ltd.",
    "limited",
    "co.",
    "company",
]

DEFAULT_TEMPERATURE = 0.2

DUMMY_PROMPT = "Hello"


def hash_url(text):
    return hashlib.md5(text.encode()).hexdigest()[0:8]


def clean_company_name(long_name: str) -> str:
    """
    Cleans the company name by removing common suffixes and anything after a comma.
    """
    company_name = long_name.lower().split(",")[0]
    for word in COMMON_SUFFIXES:
        company_name = company_name.replace(word, "")
    return company_name.strip()


def filter_recent_news(
    news_object: List[Dict], max_news_age: int, max_news_items: int
) -> List[Dict[str, Any]]:
    now_UTC = datetime.utcnow()
    cutoff_time = now_UTC - timedelta(days=max_news_age)
    return [
        news
        for news in news_object
        if datetime(*news["published_parsed"][:6]) >= cutoff_time
    ][:max_news_items]


def test_models(
    models_to_test, sample_size, content_map, company_name, news_object, ticker_symbol
):
    for model_name in models_to_test:
        logging.info(f"Testing model: {model_name}")
        for i in range(sample_size):
            test_model(
                model_name, i, content_map, company_name, news_object, ticker_symbol
            )
        logging.info("")


def test_model(
    model_name, iteration, content_map, company_name, news_object, ticker_symbol
):
    start_time = time.time()
    llm = initialize_llm(model_name)

    # Pre-warm the model
    pre_warm_model(llm)

    analyze_prompt = prepare_analyze_prompt(llm, model_name)

    sentiments_map = analyze_content(
        llm,
        analyze_prompt,
        content_map,
        company_name,
        news_object,
        model_name,
        iteration,
    )

    average_sentiment = compute_weighted_average_sentiment(sentiments_map)

    end_time = time.time()

    save_results(
        model_name,
        ticker_symbol,
        iteration,
        average_sentiment,
        end_time - start_time,
        sentiments_map,
    )


def initialize_llm(model_name):
    return Ollama(model=model_name, temperature=DEFAULT_TEMPERATURE)


def pre_warm_model(llm, dummy_prompt=DUMMY_PROMPT):
    llm.invoke(dummy_prompt)


def prepare_analyze_prompt(llm, model_name):
    if "sentiment" not in model_name:
        llm.system = get_file_content("sentiment_system_message.txt")
        llm.invoke(get_file_content("sentiment_user_first_prompt.txt"))
        analyze_prompt = get_file_content("sentiment_user_message.txt")
    else:
        analyze_prompt = ""
    return analyze_prompt


def format_prompt(
    is_sentiment_model: bool, analyze_prompt: str, content: str, company_name: str
) -> str:
    return (
        content
        if is_sentiment_model
        else analyze_prompt.format(
            content_to_analyze=content, company_name=company_name
        )
    )


def process_content(
    llm: Ollama, prompt: str, url: str, news_object: List[Dict[str, Any]]
) -> Dict[str, Any]:
    try:
        start_time = time.time()
        output = llm.invoke(prompt)
        time_taken = time.time() - start_time

        valid, sentiment_json = validate_json(output)
        sentiment_json.update(
            {
                "valid": valid,
                "url": url,
                "published": find_published_date(news_object, url),
                "time_taken": round(time_taken, 2),
            }
        )
        if not valid:
            logging.error(f"Invalid JSON output for URL {url}: {output}")
        return sentiment_json
    except Exception as e:
        logging.error(f"Error processing URL {url}: {e}")
        return {}


def analyze_content(
    llm, analyze_prompt, content_map, company_name, news_object, model_name, iteration
) -> Dict[str, Dict[str, Any]]:
    sentiments_map = {}
    is_sentiment_model = "sentiment" in model_name

    for j, (url, content) in enumerate(content_map.items()):
        prompt = format_prompt(
            is_sentiment_model, analyze_prompt, content, company_name
        )

        logging.info(f"Iteration: {iteration + 1}, item: {j + 1}/{len(content_map)}")
        sentiment_json = process_content(llm, prompt, url, news_object)
        if sentiment_json:
            sentiments_map[hash_url(url)] = sentiment_json
    return sentiments_map


def find_published_date(news_object, url):
    return next((news["published"] for news in news_object if news["link"] == url), "")


def compute_weighted_average_sentiment(sentiments_map: Dict[str, Dict]) -> float:
    average_sentiment = 0.0
    total_weight = 0.0

    for url, sentiment_json in sentiments_map.items():
        s_value = parse_json_numeric_value(sentiment_json, "sentiment")
        s_confidence = parse_json_numeric_value(sentiment_json, "confidence")

        if s_value is not None and s_confidence is not None and s_value != 0.0:
            average_sentiment += s_value * s_confidence
            total_weight += s_confidence

    if total_weight != 0.0:
        average_sentiment /= total_weight
        average_sentiment = round(average_sentiment, 2)
    else:
        logging.warning("Total weight is zero. Returning default sentiment value.")
        average_sentiment = 0.0

    return average_sentiment
