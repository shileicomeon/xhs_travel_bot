"""
小红书MCP客户端

用于调用小红书MCP服务的各种功能
"""

import os
import asyncio
from typing import List, Dict, Optional
from langchain_mcp_adapters.client import MultiServerMCPClient
from ..utils.logger import logger


class XhsMcpClient:
    """小红书MCP客户端"""
    
    def __init__(self):
        self.mcp_url = os.getenv("XHS_MCP_URL", "http://localhost:18060/mcp")
        self.transport = os.getenv("MCP_TRANSPORT", "http")
        self.client = None
        self.tools = None
    
    async def _ensure_connected(self):
        """确保MCP客户端已连接"""
        if self.client is None:
            logger.info("连接小红书MCP服务...")
            self.client = MultiServerMCPClient({
                "xiaohongshu-mcp": {
                    "transport": self.transport,
                    "url": self.mcp_url,
                }
            })
            self.tools = await self.client.get_tools()
            logger.info(f"✅ 已连接，获取到 {len(self.tools)} 个工具")
    
    def _get_tool(self, tool_name: str):
        """获取指定工具"""
        if self.tools is None:
            raise RuntimeError("MCP客户端未连接")
        
        for tool in self.tools:
            if getattr(tool, "name", "") == tool_name:
                return tool
        
        raise ValueError(f"未找到工具: {tool_name}")
    
    async def check_login_status(self) -> Dict:
        """检查登录状态"""
        await self._ensure_connected()
        
        logger.info("检查小红书登录状态...")
        tool = self._get_tool("check_login_status")
        result = await tool.ainvoke({})
        
        logger.info(f"登录状态: {result}")
        
        # 解析MCP返回的登录状态
        # MCP返回格式: [{'type': 'text', 'text': '✅ 已登录\n用户名: xxx...'}]
        is_logged_in = False
        if isinstance(result, list) and len(result) > 0:
            first_item = result[0]
            if isinstance(first_item, dict):
                text = first_item.get('text', '')
                is_logged_in = '已登录' in text or 'logged in' in text.lower()
        elif isinstance(result, dict):
            # 兼容字典格式
            is_logged_in = result.get('is_login', False) or result.get('logged_in', False)
        elif isinstance(result, str):
            # 兼容字符串格式
            is_logged_in = '已登录' in result or 'logged in' in result.lower()
        
        return {
            "is_login": is_logged_in,
            "raw_result": result
        }
    
    async def get_login_qrcode(self, save_path: str = None) -> Dict:
        """
        获取登录二维码（用于无显示器环境）
        
        Args:
            save_path: 二维码保存路径，如果为None则返回base64编码
        
        Returns:
            包含二维码信息的字典
        """
        await self._ensure_connected()
        
        logger.info("获取小红书登录二维码...")
        try:
            import asyncio
            tool = self._get_tool("get_login_qrcode")
            
            # 添加超时控制（60秒，MCP 生成二维码需要时间）
            logger.info("⏱️  等待 MCP 服务生成二维码（可能需要 10-30 秒）...")
            result = await asyncio.wait_for(
                tool.ainvoke({}),
                timeout=60.0
            )
            
            # 处理返回结果，提取base64图片数据
            qr_base64 = None
            if isinstance(result, list):
                # 遍历列表查找image类型的项
                for item in result:
                    if isinstance(item, dict) and item.get('type') == 'image':
                        qr_base64 = item.get('base64')
                        break
            elif isinstance(result, dict):
                qr_base64 = result.get('qrcode') or result.get('qr_code') or result.get('image') or result.get('base64')
            
            # 保存二维码图片
            if save_path and qr_base64:
                import base64
                import os
                
                # 确保目录存在
                save_dir = os.path.dirname(save_path)
                if save_dir:
                    os.makedirs(save_dir, exist_ok=True)
                
                # 如果是data URL格式，移除前缀
                if isinstance(qr_base64, str) and qr_base64.startswith('data:image'):
                    qr_base64 = qr_base64.split(',')[1] if ',' in qr_base64 else qr_base64
                
                # 保存图片
                if isinstance(qr_base64, str):
                    with open(save_path, 'wb') as f:
                        f.write(base64.b64decode(qr_base64))
                    logger.info(f"✅ 二维码已保存到: {save_path}")
                    
                    # 将保存路径添加到结果中
                    if isinstance(result, dict):
                        result['saved_path'] = save_path
            
            logger.info(f"✅ 获取登录二维码成功")
            return result
            
        except asyncio.TimeoutError:
            logger.error("❌ 获取登录二维码超时（60秒）")
            logger.warning("⚠️  MCP 服务可能卡住了")
            logger.info("💡 解决方案：")
            logger.info("   1. 运行修复脚本: bash tools/quick_fix_mcp.sh")
            logger.info("   2. 或手动重启: pkill -9 -f xiaohongshu-mcp && cd ~/xiaohongshu-mcp && xvfb-run -a go run . -headless=true &")
            return {"error": "timeout"}
        except ValueError:
            logger.warning("⚠️  MCP服务不支持 get_login_qrcode 工具")
            logger.info("请使用浏览器访问 http://localhost:18060 进行登录")
            return {"error": "get_login_qrcode tool not available"}
    
    async def search_feeds(self, keyword: str, limit: int = 10) -> List[Dict]:
        """
        搜索小红书内容
        
        Args:
            keyword: 搜索关键词
            limit: 返回数量限制
        
        Returns:
            搜索结果列表
        """
        await self._ensure_connected()
        
        logger.info(f"搜索小红书内容: {keyword}")
        tool = self._get_tool("search_feeds")
        result = await tool.ainvoke({"keyword": keyword})
        
        # 解析结果
        feeds = self._parse_search_result(result, limit)
        logger.info(f"✅ 找到 {len(feeds)} 个相关内容")
        
        return feeds
    
    async def get_feed_detail(self, feed_id: str, xsec_token: str) -> Dict:
        """
        获取帖子详情
        
        Args:
            feed_id: 帖子ID
            xsec_token: 安全令牌
        
        Returns:
            帖子详情
        """
        await self._ensure_connected()
        
        logger.info(f"获取帖子详情: {feed_id}")
        tool = self._get_tool("get_feed_detail")
        result = await tool.ainvoke({
            "feed_id": feed_id,
            "xsec_token": xsec_token
        })
        
        detail = self._parse_feed_detail(result)
        logger.info(f"✅ 获取到帖子: {detail.get('title', 'N/A')[:30]}")
        
        return detail
    
    async def publish_content(self, title: str, content: str, images: List[str], tags: Optional[List[str]] = None) -> Dict:
        """
        发布图文内容
        
        Args:
            title: 标题
            content: 正文
            images: 图片列表（本地路径或URL）
            tags: 标签列表（可选）
        
        Returns:
            发布结果
        """
        await self._ensure_connected()
        
        logger.info(f"发布内容: {title}")
        logger.info(f"  图片数: {len(images)}")
        if tags:
            logger.info(f"  标签数: {len(tags)}")
        
        # 构建发布参数
        publish_params = {
            "title": title,
            "content": content,
            "images": images
        }
        
        # 如果有标签，添加到content末尾（小红书格式）
        if tags:
            tags_str = " ".join(tags)
            publish_params["content"] = f"{content}\n\n{tags_str}"
        
        tool = self._get_tool("publish_content")
        result = await tool.ainvoke(publish_params)
        
        logger.info(f"✅ 发布成功")
        return result
    
    def _parse_search_result(self, result, limit: int) -> List[Dict]:
        """解析搜索结果"""
        feeds = []
        
        logger.info(f"🔍 搜索结果类型: {type(result)}")
        logger.info(f"🔍 搜索结果内容（前1000字符）: {str(result)[:1000]}")
        
        # 根据实际返回格式解析
        if isinstance(result, list):
            # 如果返回的是列表
            for item in result[:limit]:
                if isinstance(item, dict):
                    # 检查是否是MCP返回的包装格式
                    if item.get('type') == 'text' and 'text' in item:
                        # 解析JSON字符串
                        import json
                        try:
                            data = json.loads(item['text'])
                            if 'feeds' in data:
                                for feed in data['feeds'][:limit]:
                                    feeds.append({
                                        'feed_id': feed.get('id'),
                                        'xsec_token': feed.get('xsecToken') or feed.get('xsec_token') or ''  # 注意驼峰命名
                                    })
                        except:
                            pass
                    else:
                        feeds.append({
                            'feed_id': item.get('id') or item.get('note_id') or item.get('feed_id'),
                            'xsec_token': item.get('xsecToken') or item.get('xsec_token') or item.get('token') or ''  # 支持驼峰命名
                        })
                elif isinstance(item, str):
                    # 如果列表项是字符串，尝试解析
                    import json
                    try:
                        parsed = json.loads(item)
                        feeds.append({
                            'feed_id': parsed.get('id') or parsed.get('note_id'),
                            'xsec_token': parsed.get('xsec_token') or ''
                        })
                    except:
                        pass
        
        elif isinstance(result, dict):
            # 如果返回的是字典
            items = result.get('items') or result.get('notes') or result.get('feeds') or []
            for item in items[:limit]:
                feeds.append({
                    'feed_id': item.get('id') or item.get('note_id') or item.get('feed_id'),
                    'xsec_token': item.get('xsec_token') or item.get('token') or ''
                })
        
        elif isinstance(result, str):
            # 如果返回的是字符串，尝试提取信息
            import re
            import json
            
            # 尝试解析为JSON
            try:
                parsed = json.loads(result)
                return self._parse_search_result(parsed, limit)
            except:
                pass
            
            # 正则提取
            feed_ids = re.findall(r'(?:feed_id|note_id|id)["\s:]+([a-zA-Z0-9]+)', result)
            tokens = re.findall(r'xsec_token["\s:]+([a-zA-Z0-9_-]+)', result)
            
            for i, feed_id in enumerate(feed_ids[:limit]):
                token = tokens[i] if i < len(tokens) else ''
                feeds.append({
                    'feed_id': feed_id,
                    'xsec_token': token
                })
        
        logger.info(f"解析出 {len(feeds)} 个帖子")
        return feeds
    
    def _parse_feed_detail(self, result) -> Dict:
        """解析帖子详情"""
        logger.info(f"🔍 帖子详情原始数据类型: {type(result)}")
        logger.info(f"🔍 帖子详情原始数据（前3000字符）: {str(result)[:3000]}")
        
        detail = {
            'title': '',
            'content': '',
            'images': [],
            'tags': []
        }
        
        # 根据实际返回格式解析
        if isinstance(result, list) and len(result) > 0:
            # MCP可能返回列表格式
            first_item = result[0]
            if isinstance(first_item, dict) and first_item.get('type') == 'text':
                # 解析JSON字符串
                import json
                try:
                    data = json.loads(first_item['text'])
                    
                    # 数据结构是嵌套的：data.note.xxx
                    note_data = data.get('data', {}).get('note', {})
                    
                    # 提取标题
                    detail['title'] = note_data.get('title', '')
                    detail['content'] = note_data.get('desc', '')
                    
                    # 提取图片（从imageList中获取urlDefault）
                    if 'imageList' in note_data:
                        detail['images'] = [
                            img.get('urlDefault') or img.get('url') or img.get('urlPre') 
                            for img in note_data['imageList'] 
                            if img.get('urlDefault') or img.get('url') or img.get('urlPre')
                        ]
                    
                    # 提取标签（从desc中提取#话题）
                    import re
                    tags = re.findall(r'#([^#\[]+)\[话题\]', note_data.get('desc', ''))
                    detail['tags'] = [f"#{tag.strip()}" for tag in tags]
                    
                    logger.info(f"✅ 解析出标题: {detail['title']}")
                    logger.info(f"✅ 解析出 {len(detail['images'])} 张图片")
                    logger.info(f"✅ 解析出 {len(detail['tags'])} 个标签")
                except Exception as e:
                    logger.error(f"❌ JSON解析失败: {e}")
        
        elif isinstance(result, str):
            import re
            
            # 提取标题
            title_match = re.search(r'title["\s:]+([^\n"]+)', result)
            if title_match:
                detail['title'] = title_match.group(1).strip()
            
            # 提取图片URL
            image_urls = re.findall(r'https?://[^\s"]+\.(?:jpg|jpeg|png|webp)', result)
            detail['images'] = image_urls
            
            # 提取标签
            tags = re.findall(r'#([^\s#]+)', result)
            detail['tags'] = [f"#{tag}" for tag in tags]
        
        return detail


def run_async(coro):
    """运行异步函数的同步包装"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(coro)

