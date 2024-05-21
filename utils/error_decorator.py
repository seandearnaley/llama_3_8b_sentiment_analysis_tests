from functools import wraps
from typing import Any, Callable, Optional, TypeVar, cast

from utils.context import logger

F = TypeVar("F", bound=Callable[..., Any])


def handle_errors(default_return: Optional[Any] = None) -> Callable[[F], F]:
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {e}")
                return default_return

        return cast(F, wrapper)

    return decorator
