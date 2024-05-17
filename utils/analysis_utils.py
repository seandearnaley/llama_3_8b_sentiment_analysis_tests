import hashlib
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List

from langchain_community.llms import Ollama

from utils.context import AnalysisContext
from utils.error_decorator import handle_errors
from utils.file_utils import (
    get_file_content,
    save_json_to_file,
)
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

DUMMY_PROMPT = "Hello"


def hash_url(text: str) -> str:
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
    models_to_test: List[str],
    sample_size: int,
    context: AnalysisContext,
) -> None:
    for model_name in models_to_test:
        logging.info(f"Testing model: {model_name}")
        for i in range(sample_size):
            test_model(model_name, i, context)
        logging.info("")


def initialize_llm(
    model_name: str,
    default_temperature: float,
    context_window_size: int,
    num_tokens_to_predict: int,
) -> Ollama:
    return Ollama(
        model=model_name,
        temperature=default_temperature,
        num_ctx=context_window_size,
        num_predict=num_tokens_to_predict,
    )


def pre_warm_model(llm: Ollama, dummy_prompt: str = DUMMY_PROMPT) -> None:
    llm.invoke(dummy_prompt)


def test_model(
    model_name: str,
    iteration: int,
    context: AnalysisContext,
):
    start_time = time.time()
    llm = initialize_llm(
        model_name,
        context.default_temperature,
        context.context_window_size,
        context.num_tokens_to_predict,
    )

    # Pre-warm the model
    pre_warm_model(llm)

    analyze_prompt = prepare_analyze_prompt(llm, model_name)

    sentiments_map = analyze_content(
        llm,
        analyze_prompt,
        model_name,
        iteration,
        context.content_map,
        context.company_name,
        context.news_object,
    )

    average_sentiment = compute_weighted_average_sentiment(sentiments_map)

    end_time = time.time()

    save_results(
        model_name,
        context.sentiment_save_folder,
        context.ticker_symbol,
        iteration,
        average_sentiment,
        end_time - start_time,
        sentiments_map,
    )


def save_results(
    model_name: str,
    sentiment_save_folder: str,
    ticker_symbol: str,
    iteration: int,
    average_sentiment: float,
    time_taken: float,
    sentiments_map: Dict[str, Any],
) -> None:
    results_dir = os.path.join(sentiment_save_folder, model_name.replace(":", "_"))
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
        logging.info(f"Created directory: {results_dir}")

    sentiment_file = os.path.join(results_dir, ticker_symbol + f"_{iteration}.json")
    data = {
        "average_sentiment": average_sentiment,
        "time_taken": round(time_taken, 2),
        "sentiments": sentiments_map,
    }
    save_json_to_file(sentiment_file, data)


def analyze_content(
    llm: Ollama,
    analyze_prompt: str,
    model_name: str,
    iteration: int,
    content_map: Dict[str, str],
    company_name: str,
    news_object: List[Dict[str, Any]],
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


def prepare_analyze_prompt(llm: Ollama, model_name: str) -> str:
    match model_name:  # Using match-case
        case model_name if "sentiment" not in model_name:
            llm.system = get_file_content("sentiment_system_message.txt")
            llm.invoke(get_file_content("sentiment_user_first_prompt.txt"))
            return get_file_content("sentiment_user_message.txt")
        case _:  # Catch-all case (could be default sentiment model)
            return ""


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


@handle_errors(default_return={})
def process_content(
    llm: Ollama, prompt: str, url: str, news_object: List[Dict[str, Any]]
) -> Dict[str, Any]:
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


@handle_errors(default_return="")
def find_published_date(news_object, url):
    return next((news["published"] for news in news_object if news["link"] == url), "")


@handle_errors(default_return=0.0)
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
