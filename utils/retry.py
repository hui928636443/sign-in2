"""
重试装饰器模块

提供支持同步和异步函数的重试机制，支持指数退避和随机延迟。

Requirements:
- 7.1: 网络请求失败时，最多重试3次，使用指数退避
- 7.2: 浏览器自动化步骤失败时，使用5-10秒随机延迟重试
- 7.3: 所有重试失败后，记录错误并继续处理其他平台/账号
"""

import asyncio
import functools
import inspect
import random
import time
from typing import Any, Callable, Optional, Tuple, Type, TypeVar, Union

from loguru import logger

T = TypeVar("T")

# 默认可重试的异常类型
DEFAULT_RETRY_EXCEPTIONS: Tuple[Type[Exception], ...] = (
    Exception,
)


def calculate_delay(
    attempt: int,
    delay_range: Tuple[float, float],
    exponential_backoff: bool,
    base_delay: float = 1.0,
) -> float:
    """
    计算重试延迟时间
    
    Args:
        attempt: 当前重试次数（从1开始）
        delay_range: 延迟范围 (min, max)，单位秒
        exponential_backoff: 是否使用指数退避
        base_delay: 指数退避的基础延迟
    
    Returns:
        计算后的延迟时间（秒）
    """
    min_delay, max_delay = delay_range
    
    if exponential_backoff:
        # 指数退避: base_delay * 2^(attempt-1)，但限制在 delay_range 范围内
        exp_delay = base_delay * (2 ** (attempt - 1))
        # 添加随机抖动 (jitter) 避免雷群效应
        jitter = random.uniform(0, exp_delay * 0.1)
        delay = min(max(exp_delay + jitter, min_delay), max_delay)
    else:
        # 随机延迟：在 delay_range 范围内随机选择
        delay = random.uniform(min_delay, max_delay)
    
    return delay


def retry_decorator(
    max_retries: int = 3,
    delay_range: Tuple[float, float] = (1.0, 5.0),
    exponential_backoff: bool = False,
    exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    on_retry: Optional[Callable[[Exception, int], None]] = None,
    raise_on_failure: bool = False,
    default_return: Any = None,
) -> Callable[[Callable[..., T]], Callable[..., Optional[T]]]:
    """
    重试装饰器，支持同步和异步函数
    
    Args:
        max_retries: 最大重试次数，默认3次
        delay_range: 延迟范围 (min, max)，单位秒，默认 (1.0, 5.0)
        exponential_backoff: 是否使用指数退避，默认 False
        exceptions: 需要重试的异常类型元组，默认所有 Exception
        on_retry: 重试时的回调函数，接收 (exception, attempt) 参数
        raise_on_failure: 所有重试失败后是否抛出异常，默认 False
        default_return: 所有重试失败后的默认返回值，默认 None
    
    Returns:
        装饰后的函数
    
    Example:
        # 网络请求重试（指数退避）
        @retry_decorator(max_retries=3, exponential_backoff=True)
        async def fetch_data():
            ...
        
        # 浏览器自动化重试（随机延迟5-10秒）
        @retry_decorator(max_retries=3, delay_range=(5.0, 10.0))
        def browser_action():
            ...
    """
    retry_exceptions = exceptions or DEFAULT_RETRY_EXCEPTIONS
    
    def decorator(func: Callable[..., T]) -> Callable[..., Optional[T]]:
        is_async = inspect.iscoroutinefunction(func)
        
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Optional[T]:
            last_exception: Optional[Exception] = None
            
            for attempt in range(1, max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except retry_exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        delay = calculate_delay(
                            attempt=attempt,
                            delay_range=delay_range,
                            exponential_backoff=exponential_backoff,
                        )
                        
                        logger.warning(
                            f"[{func.__name__}] 第 {attempt}/{max_retries} 次尝试失败: {e}. "
                            f"将在 {delay:.2f} 秒后重试..."
                        )
                        
                        if on_retry:
                            on_retry(e, attempt)
                        
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"[{func.__name__}] 所有 {max_retries} 次重试均失败. "
                            f"最后错误: {e}"
                        )
            
            # 所有重试失败
            if raise_on_failure and last_exception:
                raise last_exception
            return default_return
        
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Optional[T]:
            last_exception: Optional[Exception] = None
            
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retry_exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        delay = calculate_delay(
                            attempt=attempt,
                            delay_range=delay_range,
                            exponential_backoff=exponential_backoff,
                        )
                        
                        logger.warning(
                            f"[{func.__name__}] 第 {attempt}/{max_retries} 次尝试失败: {e}. "
                            f"将在 {delay:.2f} 秒后重试..."
                        )
                        
                        if on_retry:
                            on_retry(e, attempt)
                        
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"[{func.__name__}] 所有 {max_retries} 次重试均失败. "
                            f"最后错误: {e}"
                        )
            
            # 所有重试失败
            if raise_on_failure and last_exception:
                raise last_exception
            return default_return
        
        if is_async:
            return async_wrapper
        return sync_wrapper
    
    return decorator


def retry_with_exponential_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    raise_on_failure: bool = False,
) -> Callable[[Callable[..., T]], Callable[..., Optional[T]]]:
    """
    使用指数退避的重试装饰器（便捷函数）
    
    适用于网络请求等场景 (Requirement 7.1)
    
    Args:
        max_retries: 最大重试次数，默认3次
        base_delay: 基础延迟时间，默认1秒
        max_delay: 最大延迟时间，默认30秒
        exceptions: 需要重试的异常类型
        raise_on_failure: 失败后是否抛出异常
    
    Returns:
        装饰后的函数
    """
    return retry_decorator(
        max_retries=max_retries,
        delay_range=(base_delay, max_delay),
        exponential_backoff=True,
        exceptions=exceptions,
        raise_on_failure=raise_on_failure,
    )


def retry_with_random_delay(
    max_retries: int = 3,
    min_delay: float = 5.0,
    max_delay: float = 10.0,
    exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    raise_on_failure: bool = False,
) -> Callable[[Callable[..., T]], Callable[..., Optional[T]]]:
    """
    使用随机延迟的重试装饰器（便捷函数）
    
    适用于浏览器自动化等场景 (Requirement 7.2)
    
    Args:
        max_retries: 最大重试次数，默认3次
        min_delay: 最小延迟时间，默认5秒
        max_delay: 最大延迟时间，默认10秒
        exceptions: 需要重试的异常类型
        raise_on_failure: 失败后是否抛出异常
    
    Returns:
        装饰后的函数
    """
    return retry_decorator(
        max_retries=max_retries,
        delay_range=(min_delay, max_delay),
        exponential_backoff=False,
        exceptions=exceptions,
        raise_on_failure=raise_on_failure,
    )


# 预定义的装饰器实例，方便直接使用
network_retry = retry_with_exponential_backoff(max_retries=3)
browser_retry = retry_with_random_delay(max_retries=3, min_delay=5.0, max_delay=10.0)
