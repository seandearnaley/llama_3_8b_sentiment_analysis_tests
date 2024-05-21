import logging
from dataclasses import dataclass
from typing import Any, Dict, List


def configure_logging():
    logger = logging.getLogger("app_logger")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


logger = configure_logging()


@dataclass
class AnalysisContext:
    content_map: Dict[str, str]
    company_name: str
    news_object: List[Dict[str, Any]]
    ticker_symbol: str
    default_temperature: float
    context_window_size: int
    num_tokens_to_predict: int
    sentiment_save_folder: str
