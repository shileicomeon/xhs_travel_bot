"""
重试机制模块

使用tenacity实现自动重试
"""

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
import requests
from .logger import logger


def retry_on_failure(max_attempts=3, backoff_min=2, backoff_max=10):
    """
    重试装饰器
    
    Args:
        max_attempts: 最大重试次数
        backoff_min: 最小退避时间（秒）
        backoff_max: 最大退避时间（秒）
    
    Example:
        @retry_on_failure(max_attempts=3)
        def fetch_data():
            return requests.get("https://api.example.com/data")
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=backoff_min, max=backoff_max),
        retry=retry_if_exception_type((
            requests.exceptions.RequestException,
            TimeoutError,
            ConnectionError
        )),
        before_sleep=lambda retry_state: logger.warning(
            f"重试 {retry_state.attempt_number}/{max_attempts}..."
        ),
        reraise=True
    )


def retry_on_network_error(func):
    """网络错误重试装饰器（快捷方式）"""
    return retry_on_failure(max_attempts=3, backoff_min=2, backoff_max=10)(func)

