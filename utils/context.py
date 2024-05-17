from dataclasses import dataclass
from typing import Any, Dict, List


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
