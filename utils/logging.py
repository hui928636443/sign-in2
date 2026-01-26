#!/usr/bin/env python3
"""
日志配置模块

提供统一的日志格式和敏感信息脱敏功能。

Requirements:
- 8.1: 统一日志格式：时间戳、级别、模块名
- 8.2: 支持 DEBUG 模式详细输出
- 8.3: 日志输出到 stderr
- 8.4: 敏感信息脱敏
"""

import re
import sys
from typing import Optional

from loguru import logger


# 敏感信息模式
SENSITIVE_PATTERNS = [
    # 密码
    (r'(password["\']?\s*[:=]\s*["\']?)([^"\'\s,}]+)', r'\1***MASKED***'),
    (r'(PASSWORD["\']?\s*[:=]\s*["\']?)([^"\'\s,}]+)', r'\1***MASKED***'),
    # Token
    (r'(token["\']?\s*[:=]\s*["\']?)([^"\'\s,}]+)', r'\1***MASKED***'),
    (r'(TOKEN["\']?\s*[:=]\s*["\']?)([^"\'\s,}]+)', r'\1***MASKED***'),
    # API Key
    (r'(api[_-]?key["\']?\s*[:=]\s*["\']?)([^"\'\s,}]+)', r'\1***MASKED***'),
    (r'(API[_-]?KEY["\']?\s*[:=]\s*["\']?)([^"\'\s,}]+)', r'\1***MASKED***'),
    # Secret
    (r'(secret["\']?\s*[:=]\s*["\']?)([^"\'\s,}]+)', r'\1***MASKED***'),
    (r'(SECRET["\']?\s*[:=]\s*["\']?)([^"\'\s,}]+)', r'\1***MASKED***'),
    # Cookie
    (r'(cookie["\']?\s*[:=]\s*["\']?)([^"\'\s,}]{20,})', r'\1***MASKED***'),
    (r'(COOKIE["\']?\s*[:=]\s*["\']?)([^"\'\s,}]{20,})', r'\1***MASKED***'),
    # Authorization header
    (r'(Authorization["\']?\s*[:=]\s*["\']?)([^"\'\s,}]+)', r'\1***MASKED***'),
    # Bearer token
    (r'(Bearer\s+)([A-Za-z0-9._-]+)', r'\1***MASKED***'),
    # CSRF token (partial mask)
    (r'(csrf["\']?\s*[:=]\s*["\']?)([A-Za-z0-9]{10})([A-Za-z0-9]+)', r'\1\2***'),
    (r'(CSRF["\']?\s*[:=]\s*["\']?)([A-Za-z0-9]{10})([A-Za-z0-9]+)', r'\1\2***'),
]


def mask_sensitive_data(message: str) -> str:
    """脱敏敏感信息
    
    Args:
        message: 原始消息
    
    Returns:
        脱敏后的消息
    """
    result = message
    for pattern, replacement in SENSITIVE_PATTERNS:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    return result


class SensitiveFilter:
    """敏感信息过滤器"""
    
    def __call__(self, record):
        """过滤日志记录中的敏感信息"""
        record["message"] = mask_sensitive_data(record["message"])
        return True


def setup_logging(
    debug: bool = False,
    mask_sensitive: bool = True,
    log_file: Optional[str] = None,
) -> None:
    """配置日志
    
    Args:
        debug: 是否启用调试模式
        mask_sensitive: 是否脱敏敏感信息
        log_file: 日志文件路径（可选）
    """
    # 移除默认处理器
    logger.remove()
    
    # 日志级别
    level = "DEBUG" if debug else "INFO"
    
    # 日志格式
    format_str = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )
    
    # 简化格式（非调试模式）
    simple_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<level>{message}</level>"
    )
    
    # 选择格式
    fmt = format_str if debug else simple_format
    
    # 过滤器
    filter_func = SensitiveFilter() if mask_sensitive else None
    
    # 添加 stderr 处理器
    logger.add(
        sys.stderr,
        format=fmt,
        level=level,
        colorize=True,
        filter=filter_func,
    )
    
    # 添加文件处理器（如果指定）
    if log_file:
        logger.add(
            log_file,
            format=format_str,
            level=level,
            rotation="10 MB",
            retention="7 days",
            compression="gz",
            filter=filter_func,
        )


def get_logger(name: str = None):
    """获取日志记录器
    
    Args:
        name: 模块名称
    
    Returns:
        logger 实例
    """
    if name:
        return logger.bind(name=name)
    return logger
