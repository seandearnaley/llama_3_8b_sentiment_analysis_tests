import hashlib
import json
import logging
import os
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Union

from langchain_community.llms import Ollama


def hash_url(text):
    return hashlib.md5(text.encode()).hexdigest()[0:8]


def validate_json(json_data: str) -> Tuple[bool, Dict]:
    try:
        json_dict = json.loads(json_data)
        return True, json_dict
    except ValueError:
        return False, {}


def parse_json_numeric_value(json_data: Dict, key: str) -> Union[float, None]:
    try:
        return float(json_data[key])
    except KeyError:
        return search_numeric_value(json.dumps(json_data))


def clean_company_name(long_name: str) -> str:
    """
    Cleans the company name by removing common suffixes and anything after a comma.
    """
    company_name = long_name.lower().split(",")[0]
    to_remove = get_common_suffixes()
    for word in to_remove:
        company_name = company_name.replace(word, "")
    return company_name.strip()


def get_common_suffixes() -> List[str]:
    return [
        "inc.",
        "incorporated",
        "corp.",
        "corporation",
        "ltd.",
        "limited",
        "co.",
        "company",
    ]


def search_numeric_value(json_str: str) -> Union[float, None]:
    match = re.search(r"[-+]?[0-1]\.\d+", json_str)
    return float(match.group()) if match else None


def filter_recent_news(
    news_object: List[Dict], max_news_age: int, max_news_items: int
) -> List[Dict]:
    now_UTC = datetime.utcnow()
    cutoff_time = now_UTC - timedelta(days=max_news_age)
    return [
        news
        for news in news_object
        if datetime(*news["published_parsed"][:6]) >= cutoff_time
    ][:max_news_items]


def test_model(
    model_name, iteration, content_map, company_name, news_object, ticker_symbol
):
    start_time = time.time()
    llm = initialize_llm(model_name)

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
    return Ollama(model=model_name, temperature=0.2)


def read_file_content(file_path: str) -> str:
    with open(file_path, "r") as file:
        return file.read()


def get_file_content(file_name: str) -> str:
    return read_file_content(os.path.join("messages", file_name))


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


def analyze_content(
    llm, analyze_prompt, content_map, company_name, news_object, model_name, iteration
):
    sentiments_map = {}
    is_sentiment_model = "sentiment" in model_name

    for j, (url, content) in enumerate(content_map.items()):
        prompt = format_prompt(
            is_sentiment_model, analyze_prompt, content, company_name
        )

        print(f"\rIteration: {iteration + 1} item: {j + 1}/{len(content_map)}", end="")
        output = llm.invoke(prompt)

        valid, sentiment_json = validate_json(output)
        if valid:
            sentiment_json["url"] = url
            sentiment_json["published"] = find_published_date(news_object, url)
            sentiments_map[hash_url(url)] = sentiment_json

    return sentiments_map


def find_published_date(news_object, url):
    return next((news["published"] for news in news_object if news["link"] == url), "")


def ensure_directory_exists(directory: str):
    if not os.path.exists(directory):
        os.makedirs(directory)


def save_json_to_file(file_path: str, data: Dict):
    with open(file_path, "w") as file:
        json.dump(data, file, indent=2)


def save_results(
    model_name, ticker_symbol, iteration, average_sentiment, time_taken, sentiments_map
):
    results_dir = get_results_directory(model_name)
    ensure_directory_exists(results_dir)

    sentiment_file = os.path.join(results_dir, ticker_symbol + f"_{iteration}.json")
    data = {
        "average_sentiment": average_sentiment,
        "time_taken": round(time_taken, 2),
        "sentiments": sentiments_map,
    }
    save_json_to_file(sentiment_file, data)


def get_results_directory(model_name: str) -> str:
    return os.path.join("sentiments", model_name.replace(":", "_"))


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
