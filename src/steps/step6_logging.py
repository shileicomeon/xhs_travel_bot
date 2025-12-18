"""
Step 6: 飞书记录

记录发布结果到飞书表格和发送通知
"""

from datetime import datetime
from ..utils.logger import logger
from ..services.feishu_client import FeishuClient


def log_to_feishu(ctx, result):
    """
    记录到飞书
    
    Args:
        ctx: 上下文
        result: 发布结果
    """
    logger.info("Step 6: 记录到飞书")
    
    # 创建飞书客户端
    feishu = FeishuClient()
    
    # 发送通知
    if result.get("status") == "success":
        feishu.send_success_notification(ctx, result)
    else:
        error = result.get("error", "未知错误")
        feishu.send_failure_notification(ctx, error)
    
    # 记录到表格
    is_success = result.get("status") == "success"
    
    # 将日期转换为Unix时间戳（毫秒）
    now = datetime.now()
    date_timestamp = int(now.replace(hour=0, minute=0, second=0, microsecond=0).timestamp() * 1000)
    
    record = {
        "日期": date_timestamp,  # Unix时间戳（毫秒）
        "发布时间": result.get("publish_time", now.strftime("%H:%M:%S")),
        "标题": result.get("title", "N/A"),
        "城市": ctx.get("city", "N/A"),
        "模式": "旅游攻略" if ctx.get("city") != "文字卡片" else "文字卡片",
        "状态": "✅ 成功" if is_success else "❌ 失败",
        "笔记ID": result.get("note_id", "N/A"),
        "耗时": f"{result.get('duration', 'N/A')}秒" if result.get('duration') else "N/A",
        "图片数": ctx.get('image_count', 6),  # 直接使用数字
        "失败原因": result.get("error", "")[:200] if not is_success else ""  # 限制长度
    }
    
    feishu.append_table_record(record)
    
    logger.info("✅ 飞书记录完成")

