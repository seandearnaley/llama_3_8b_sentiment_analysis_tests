import json
import logging
import os
from functools import lru_cache
from typing import Any, Dict

import yaml

# Define constants for paths
MESSAGES_DIR = "messages"
FILE_READ_MODE = "r"
FILE_WRITE_MODE = "w"


@lru_cache(maxsize=None)
def read_file_content(file_path: str) -> str:
    with open(file_path, "r") as file:
        return file.read()


def get_file_content(file_name: str) -> str:
    return read_file_content(os.path.join(MESSAGES_DIR, file_name))


def ensure_directory_exists(directory: str) -> None:
    if not os.path.exists(directory):
        os.makedirs(directory)
        logging.info(f"Created directory: {directory}")


def save_json_to_file(file_path: str, data: Dict[str, Any]) -> None:
    with open(file_path, FILE_WRITE_MODE) as file:
        json.dump(data, file, indent=2)
        logging.info(f"Saved JSON to file: {file_path}")


def load_config(file_path: str) -> Dict[str, Any]:
    """Load a YAML configuration file and return it as a dictionary."""
    try:
        with open(file_path, FILE_READ_MODE) as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        logging.error(f"Config file not found: {file_path}")
        raise
    except yaml.YAMLError as e:
        logging.error(f"Error parsing YAML file {file_path}: {e}")
        raise


def get_results_directory(model_name: str, directory: str) -> str:
    return os.path.join(directory, model_name.replace(":", "_"))
