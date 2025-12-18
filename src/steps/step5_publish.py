"""
Step 5: 发布到小红书

使用小红书MCP工具发布内容
"""

import os
import asyncio
from datetime import datetime
from langchain_mcp_adapters.client import MultiServerMCPClient
from ..utils.logger import logger
from .step4_assembly import cleanup_local_images


# 初始化小红书MCP客户端
def _get_mcp_client():
    """获取小红书MCP客户端"""
    return MultiServerMCPClient(
        {
            "xiaohongshu-mcp": {
                "transport": os.getenv("MCP_TRANSPORT", "sse"),
                "url": os.getenv("XHS_MCP_URL", "http://localhost:18060/mcp"),
            }
        }
    )


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
    client = _get_mcp_client()
    
    try:
        # 获取MCP工具
        logger.info("正在连接小红书MCP服务...")
        tools = await client.get_tools()
        tool_map = {getattr(t, "name", ""): t for t in tools}
        
        logger.debug(f"可用MCP工具: {list(tool_map.keys())}")
        
        # 查找发布工具
        publish_tool = tool_map.get("publish_content")
        if publish_tool is None:
            raise Exception("未找到 publish_content 工具，请确认MCP服务是否正常运行")
        
        # 构建发布参数
        payload = {
            "title": post["title"],
            "content": post["content"],
            "images": post["images"],
        }
        
        # 如果有标签，添加到正文末尾（小红书格式）
        if post.get("tags"):
            tags_str = " ".join(post["tags"])
            payload["content"] = f"{post['content']}\n\n{tags_str}"
        
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
                
                # 方式3: 检查是否包含"发布成功"但ID确实为空
                if not note_id or len(note_id) < 10:
                    if '发布成功' in text or 'success' in text.lower():
                        # MCP说发布成功但没有返回ID，可能是草稿箱
                        logger.warning("⚠️  MCP返回'发布成功'但未找到PostID")
                        logger.warning("   可能原因：内容进入草稿箱，或MCP返回格式变化")
                        logger.warning(f"   完整响应: {text}")
                        
                        # 尝试从浏览器或MCP界面获取最新发布的笔记ID
                        logger.info("💡 建议：访问 http://localhost:18060 查看最新发布记录")
                        
                        # 暂时标记为成功，但note_id为特殊值
                        note_id = "draft_or_pending"
                        post_status = "success_no_id"
                
                # 提取Status
                if 'Status:' in text:
                    status_part = text.split('Status:')[1].strip()
                    post_status = status_part.split(' ')[0].strip()
                
                # 最终检查
                if not note_id or note_id == "draft_or_pending":
                    logger.warning(f"⚠️  发布可能成功，但未获取到PostID")
                    logger.warning(f"   返回状态: {post_status}")
                    # 不再抛出异常，允许继续
                elif len(note_id) < 10 and note_id != "draft_or_pending":
                    logger.error("❌ PostID格式异常")
                    raise ValueError(f"发布失败：PostID格式异常: {note_id}\n\n完整响应: {text[:300]}")
        
        elif isinstance(result, str):
            note_id = result if result and len(result) > 10 else None
            if not note_id:
                raise ValueError(f"发布失败：MCP返回的note_id无效。响应: {result[:200]}")
        elif isinstance(result, dict):
            note_id = result.get("note_id") or result.get("id")
            if not note_id or len(note_id) < 10:
                raise ValueError(f"发布失败：MCP返回的note_id无效。响应: {str(result)[:200]}")
        else:
            logger.error(f"未知的MCP返回格式: {type(result)}")
            raise ValueError(f"发布失败：无法解析MCP返回结果。类型: {type(result)}")
        
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

