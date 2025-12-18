"""
日志模块

使用loguru实现结构化日志
"""

import sys
from pathlib import Path
from loguru import logger as _logger

# 移除默认handler
_logger.remove()

# 添加控制台输出（彩色）
_logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO",
    colorize=True
)

# 添加文件输出（JSON格式，按日期滚动）
log_dir = Path("/var/log/xhs_bot")
if not log_dir.exists():
    # 如果/var/log不可写，使用项目目录
    log_dir = Path(__file__).parent.parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)

_logger.add(
    log_dir / "xhs_bot_{time:YYYY-MM-DD}.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
    level="DEBUG",
    rotation="00:00",  # 每天午夜滚动
    retention="30 days",  # 保留30天
    compression="zip",  # 压缩旧日志
    serialize=False,  # 使用文本格式（更易读）
    encoding="utf-8"
)

# 导出logger
logger = _logger

# 添加辅助函数
def mask_sensitive(data):
    """脱敏敏感数据"""
    if isinstance(data, dict):
        masked = {}
        for k, v in data.items():
            if any(keyword in k.lower() for keyword in ['key', 'secret', 'password', 'token']):
                masked[k] = '***MASKED***'
            else:
                masked[k] = mask_sensitive(v)
        return masked
    return data

