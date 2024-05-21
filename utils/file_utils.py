import json
import os
from functools import lru_cache
from typing import Any, Dict

import yaml

from utils.context import logger

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


def save_json_to_file(file_path: str, data: Dict[str, Any]) -> None:
    with open(file_path, FILE_WRITE_MODE) as file:
        json.dump(data, file, indent=2)
        logger.info(f"Saved JSON to file: {file_path}")


def load_config(file_path: str) -> Dict[str, Any]:
    """Load a YAML configuration file and return it as a dictionary."""
    try:
        with open(file_path, FILE_READ_MODE) as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        logger.error(f"Config file not found: {file_path}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML file {file_path}: {e}")
        raise
