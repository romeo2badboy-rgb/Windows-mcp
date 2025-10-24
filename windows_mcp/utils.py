"""Utility functions and decorators for error handling and validation."""

import functools
import logging
import time
from typing import Any, Callable, Optional
from mcp.types import TextContent, ImageContent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('windows-mcp')


def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Retry failed operations with exponential backoff."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {str(e)}. "
                            f"Retrying in {current_delay}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"All {max_retries} retries failed for {func.__name__}: {str(e)}")

            return [TextContent(
                type="text",
                text=f"Error: Operation failed after {max_retries} retries. Last error: {str(last_exception)}"
            )]

        return wrapper
    return decorator


def validate_coordinates(x: Optional[int] = None, y: Optional[int] = None,
                        screen_width: int = 3840, screen_height: int = 2160) -> tuple[bool, Optional[str]]:
    """Validate screen coordinates."""
    if x is not None:
        if not isinstance(x, int):
            return False, f"X must be integer, got {type(x)}"
        if x < 0 or x > screen_width:
            return False, f"X {x} out of bounds (0-{screen_width})"

    if y is not None:
        if not isinstance(y, int):
            return False, f"Y must be integer, got {type(y)}"
        if y < 0 or y > screen_height:
            return False, f"Y {y} out of bounds (0-{screen_height})"

    return True, None


def validate_label(label: int, max_label: int) -> tuple[bool, Optional[str]]:
    """Validate element label."""
    if not isinstance(label, int):
        return False, f"Label must be integer, got {type(label)}"
    if label < 0:
        return False, f"Label must be non-negative, got {label}"
    if label >= max_label:
        return False, f"Label {label} out of range (0-{max_label - 1})"
    return True, None


def validate_string(value: Any, name: str, min_length: int = 0,
                   max_length: int = 10000) -> tuple[bool, Optional[str]]:
    """Validate string input."""
    if not isinstance(value, str):
        return False, f"{name} must be string, got {type(value)}"
    if len(value) < min_length:
        return False, f"{name} must be at least {min_length} characters"
    if len(value) > max_length:
        return False, f"{name} must not exceed {max_length} characters"
    return True, None


def validate_number(value: Any, name: str, min_val: Optional[float] = None,
                   max_val: Optional[float] = None) -> tuple[bool, Optional[str]]:
    """Validate numeric input."""
    if not isinstance(value, (int, float)):
        return False, f"{name} must be number, got {type(value)}"
    if min_val is not None and value < min_val:
        return False, f"{name} must be at least {min_val}, got {value}"
    if max_val is not None and value > max_val:
        return False, f"{name} must not exceed {max_val}, got {value}"
    return True, None


def safe_execute(func: Callable, *args, **kwargs) -> tuple[Any, Optional[Exception]]:
    """Safely execute function and return result or exception."""
    try:
        result = func(*args, **kwargs)
        return result, None
    except Exception as e:
        logger.error(f"Error executing {func.__name__}: {str(e)}")
        return None, e


def create_error_response(error_msg: str, tool_name: str = "") -> list[TextContent]:
    """Create standardized error response."""
    if tool_name:
        full_msg = f"Error in {tool_name}: {error_msg}"
    else:
        full_msg = f"Error: {error_msg}"
    logger.error(full_msg)
    return [TextContent(type="text", text=full_msg)]


def create_success_response(msg: str, additional_content: Optional[list] = None) -> list:
    """Create standardized success response."""
    logger.info(msg)
    result = [TextContent(type="text", text=msg)]
    if additional_content:
        result.extend(additional_content)
    return result


class PerformanceTimer:
    """Context manager for timing operations."""

    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        logger.info(f"{self.operation_name} completed in {duration:.3f}s")
        return False

    @property
    def duration(self) -> Optional[float]:
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None


def sanitize_file_path(path: str, allowed_extensions: Optional[set[str]] = None) -> tuple[bool, Optional[str], Optional[str]]:
    """Validate and sanitize file path."""
    if not isinstance(path, str):
        return False, None, f"Path must be string, got {type(path)}"
    if not path:
        return False, None, "Path cannot be empty"
    if '..' in path or path.startswith('/') or path.startswith('\\\\'):
        return False, None, "Invalid path: path traversal detected"

    import os
    normalized_path = os.path.normpath(path)

    if allowed_extensions:
        _, ext = os.path.splitext(normalized_path)
        if ext.lower() not in allowed_extensions:
            return False, None, f"Invalid extension: {ext}. Allowed: {allowed_extensions}"

    return True, normalized_path, None
