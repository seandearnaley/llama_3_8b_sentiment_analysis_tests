import json
import os
from functools import lru_cache
from typing import Dict

import yaml

# Define constants for paths
MESSAGES_DIR = "messages"
SENTIMENTS_DIR = "sentiments"


@lru_cache(maxsize=None)
def read_file_content(file_path: str) -> str:
    with open(file_path, "r") as file:
        return file.read()


def get_file_content(file_name: str) -> str:
    return read_file_content(os.path.join(MESSAGES_DIR, file_name))


def ensure_directory_exists(directory: str):
    if not os.path.exists(directory):
        os.makedirs(directory)


def save_json_to_file(file_path: str, data: Dict):
    with open(file_path, "w") as file:
        json.dump(data, file, indent=2)


def load_config(file_path: str) -> dict:
    with open(file_path, "r") as file:
        return yaml.safe_load(file)


def get_results_directory(model_name: str) -> str:
    return os.path.join(SENTIMENTS_DIR, model_name.replace(":", "_"))


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
