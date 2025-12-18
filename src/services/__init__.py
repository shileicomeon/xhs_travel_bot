"""服务层模块（V2）"""

import os
from .deepseek_client import DeepSeekClient
from .qwen_client import QwenClient
from .feishu_client import FeishuClient
from .xhs_mcp_client import XhsMcpClient
from .image_downloader import ImageDownloader


def get_ai_client():
    """
    根据配置获取AI客户端
    
    Returns:
        DeepSeekClient 或 QwenClient
    """
    provider = os.getenv("AI_PROVIDER", "deepseek").lower()
    
    if provider == "qwen":
        return QwenClient()
    else:
        return DeepSeekClient()


__all__ = [
    "DeepSeekClient",
    "QwenClient",
    "FeishuClient",
    "XhsMcpClient",
    "ImageDownloader",
    "get_ai_client"
]

