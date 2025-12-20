"""
Step 5: 发布到小红书

使用小红书MCP工具发布内容
"""

import asyncio
from datetime import datetime
from ..utils.logger import logger
from .step4_assembly import cleanup_local_images
from ..services.xhs_mcp_client import XhsMcpClient


def publish_to_xhs(post):
    """
    发布到小红书
    
    Args:
        post: 组装好的内容
            {
                "images": [...],  # 图片URL或本地路径列表
                "title": "标题",
                "content": "正文",
                "tags": ["标签1", "标签2"],
                "is_local": False  # 是否为本地文件
            }
    
    Returns:
        {
            "status": "success",
            "note_id": "xxx",
            "publish_time": "2025-12-18 09:35:42"
        }
    """
    logger.info("Step 5: 发布到小红书")
    
    logger.info(f"准备发布:")
    logger.info(f"  标题: {post['title']}")
    logger.info(f"  图片数: {len(post['images'])}")
    logger.info(f"  标签数: {len(post['tags'])}")
    
    try:
        # 调用异步发布
        result = asyncio.run(_publish_via_mcp_async(post))
        
        # 如果使用了本地文件，发布后清理
        if post.get("is_local"):
            cleanup_local_images(post["images"])
        
        logger.info("✅ 发布成功")
        logger.info(f"  笔记ID: {result.get('note_id', 'N/A')}")
        
        return result
    
    except Exception as e:
        logger.error(f"❌ 发布失败: {e}")
        
        # 即使失败也清理临时文件
        if post.get("is_local"):
            cleanup_local_images(post["images"])
        
        raise


async def _publish_via_mcp_async(post):
    """
    通过MCP异步发布到小红书
    """
    client = XhsMcpClient()
    
    try:
        # 确保连接并获取工具
        logger.info("正在连接小红书MCP服务...")
        await client._ensure_connected()
        
        # 查找发布工具
        publish_tool = None
        for tool in client.tools:
            if getattr(tool, "name", "") == "publish_content":
                publish_tool = tool
                break
        
        if publish_tool is None:
            raise Exception("未找到 publish_content 工具，请确认MCP服务是否正常运行")
        
        # 构建发布参数
        payload = {
            "title": post["title"],
            "content": post["content"],
            "images": post["images"],
        }
        
        # 如果有标签，清理并作为独立参数传递
        if post.get("tags"):
            logger.info(f"📌 原始标签: {post['tags']}")
            # 清理标签：移除已有的 # 和其他符号，只保留纯文本
            clean_tags = []
            for tag in post["tags"]:
                # 移除 #、[话题]、空格等符号
                clean_tag = tag.strip().replace('#', '').replace('[话题]', '').replace('[', '').replace(']', '').strip()
                if clean_tag:
                    clean_tags.append(clean_tag)
            
            logger.info(f"📌 清理后的标签（纯字符串数组）: {clean_tags}")
            # 直接传递纯字符串数组给 MCP，让 MCP 自己处理成话题格式
            payload["tags"] = clean_tags
        
        # 过滤参数（仅保留工具支持的字段）
        if hasattr(publish_tool, "args_schema") and publish_tool.args_schema:
            try:
                schema_obj = publish_tool.args_schema
                if hasattr(schema_obj, "model_json_schema"):
                    properties = schema_obj.model_json_schema().get("properties", {})
                elif isinstance(schema_obj, dict):
                    properties = schema_obj.get("properties", {})
                else:
                    properties = {}
                
                if properties:
                    payload = {k: v for k, v in payload.items() if k in properties}
                    logger.debug(f"过滤后的参数: {list(payload.keys())}")
            except Exception as e:
                logger.warning(f"读取工具参数定义失败: {e}")
        
        # 调用发布工具
        logger.info("正在调用MCP发布工具...")
        result = await publish_tool.ainvoke(payload)
        
        logger.info(f"MCP返回结果类型: {type(result)}")
        logger.info(f"MCP返回内容（前1000字符）: {str(result)[:1000]}")
        
        # 解析结果 - MCP返回格式: [{'type': 'text', 'text': '...PostID:xxx...'}]
        note_id = None
        post_status = "unknown"
        
        if isinstance(result, list) and len(result) > 0:
            first_item = result[0]
            if isinstance(first_item, dict) and 'text' in first_item:
                text = first_item['text']
                logger.info(f"🔍 解析MCP响应文本（完整）: {text}")
                
                # 多种方式尝试提取PostID
                import re
                
                # 方式1: 标准格式 PostID:xxxx
                if 'PostID:' in text:
                    post_id_part = text.split('PostID:')[1].strip()
                    # 提取第一个非空部分
                    note_id = post_id_part.split('}')[0].strip() if '}' in post_id_part else post_id_part.strip()
                    if note_id and len(note_id) > 10:
                        logger.info(f"✅ 从PostID:字段提取到ID: {note_id}")
                
                # 方式2: 尝试从响应中提取类似note_id的长字符串
                if not note_id or len(note_id) < 10:
                    # 匹配类似 note_id 的模式（16-32位字母数字）
                    matches = re.findall(r'\b[a-f0-9]{16,32}\b', text)
                    if matches:
                        note_id = matches[0]
                        logger.info(f"✅ 从正则匹配提取到ID: {note_id}")
                
                # 提取Status
                if 'Status:' in text:
                    status_part = text.split('Status:')[1].strip()
                    post_status = status_part.split(' ')[0].strip()
                
                # 检查是否发布成功（不再强制要求PostID）
                if '发布成功' in text or '发布完成' in text or 'success' in text.lower():
                    if not note_id or len(note_id) < 10:
                        logger.warning("⚠️  MCP返回发布成功，但未获取到PostID")
                        logger.warning("   内容可能在草稿箱或已发布但ID未返回")
                        note_id = "no_id_returned"  # 标记为无ID但成功
                    logger.info(f"✅ 发布成功，PostID: {note_id}")
                else:
                    # 只有明确失败才抛出异常
                    if '失败' in text or 'error' in text.lower() or 'fail' in text.lower():
                        logger.error(f"❌ 发布失败: {text}")
                        raise ValueError(f"发布失败：{text}")
                    else:
                        # 状态不明确，但不抛出异常
                        logger.warning(f"⚠️  发布状态不明确: {text[:200]}")
                        if not note_id:
                            note_id = "unknown_status"
        
        elif isinstance(result, str):
            note_id = result if result and len(result) > 10 else "no_id_returned"
            logger.info(f"✅ MCP返回字符串结果: {result[:100]}")
        elif isinstance(result, dict):
            note_id = result.get("note_id") or result.get("id") or "no_id_returned"
            logger.info(f"✅ MCP返回字典结果，PostID: {note_id}")
        else:
            logger.warning(f"⚠️  未知的MCP返回格式: {type(result)}")
            note_id = "unknown_format"
        
        return {
            "status": post_status if post_status != "unknown" else "success",
            "note_id": note_id,
            "publish_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "raw_result": result
        }
    
    except Exception as e:
        # 提供更详细的错误提示
        error_msg = str(e)
        if "405 Method Not Allowed" in error_msg or "Connection refused" in error_msg:
            logger.error("无法连接到小红书MCP服务，请确认:")
            logger.error("  1. MCP服务是否已启动（http://localhost:18060/mcp）")
            logger.error("  2. 检查 XHS_MCP_URL 和 MCP_TRANSPORT 配置")
            logger.error("  3. 如果服务不支持SSE，请将 MCP_TRANSPORT 改为 'http'")
        
        logger.error(f"MCP发布失败: {e}")
        raise

