import json
import re
from typing import Dict, Tuple, Union

from pydantic import BaseModel, Field, ValidationError


class SentimentResponse(BaseModel):
    reasoning: str = Field(
        ...,  # This indicates that the 'reasoning' field must be provided
        description="A brief description explaining the logic used to determine the numeric sentiment value.",
        min_length=1,
    )
    sentiment: float = Field(
        ...,  # This indicates that the 'sentiment' field must be provided
        description="A floating-point representation of the sentiment of the news article, rounded to two decimal places. Scale ranges from -1.0 (negative) to 1.0 (positive), where 0.0 represents neutral sentiment.",
        ge=-1.0,
        le=1.0,
    )
    confidence: float = Field(
        ...,  # This indicates that the 'confidence' field must be provided
        description="A floating-point representation of the confidence in the sentiment analysis, ranging from 0.0 (least confident) to 1.0 (most confident), rounded to two decimal places.",
        ge=0.0,
        le=1.0,
    )


def validate_json(json_data: str) -> Tuple[bool, Dict]:
    try:
        SentimentResponse.model_validate_json(json_data, strict=True)
        json_dict = json.loads(json_data)
        return True, json_dict
    except ValidationError as e:
        print(f"Pydantic validation error: {e.json()}")
        return False, {}
    except ValueError:
        return False, {}


def search_numeric_value(json_str: str) -> Union[float, None]:
    match = re.search(r"[-+]?[0-1]\.\d+", json_str)
    return float(match.group()) if match else None


def parse_json_numeric_value(json_data: Dict, key: str) -> Union[float, None]:
    try:
        return float(json_data[key])
    except KeyError:
        return search_numeric_value(json.dumps(json_data))
