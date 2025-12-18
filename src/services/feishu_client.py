"""
飞书客户端

用于发送通知和记录数据到飞书表格
"""

import os
import json
import time
import hmac
import hashlib
import base64
import requests
from datetime import datetime
from ..utils.logger import logger
from ..utils.retry import retry_on_failure


class FeishuClient:
    """飞书客户端"""
    
    def __init__(self):
        self.app_id = os.getenv("FEISHU_APP_ID")
        self.app_secret = os.getenv("FEISHU_APP_SECRET")
        self.webhook_url = os.getenv("FEISHU_WEBHOOK_URL")
        self.base_id = os.getenv("FEISHU_TABLE_ID")  # 这是base_id（多维表格ID）
        self.table_id = os.getenv("FEISHU_TABLE_TABLE_ID")  # 具体的table_id
        
        if not self.webhook_url:
            logger.warning("FEISHU_WEBHOOK_URL 未设置，将跳过飞书通知")
        
        self._access_token = None
        self._token_expires_at = 0
    
    def get_access_token(self):
        """获取访问令牌"""
        if not self.app_id or not self.app_secret:
            return None
        
        # 检查token是否过期
        now = datetime.now().timestamp()
        if self._access_token and now < self._token_expires_at:
            return self._access_token
        
        # 获取新token
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        data = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        
        try:
            response = requests.post(url, json=data, timeout=10)
            result = response.json()
            
            if result.get("code") == 0:
                self._access_token = result["tenant_access_token"]
                self._token_expires_at = now + result.get("expire", 7200) - 60  # 提前1分钟过期
                logger.debug("飞书access_token获取成功")
                return self._access_token
            else:
                logger.error(f"获取飞书access_token失败: {result}")
                return None
        
        except Exception as e:
            logger.error(f"获取飞书access_token异常: {e}")
            return None
    
    def _generate_sign(self, timestamp, secret):
        """生成飞书Webhook签名"""
        if not secret:
            return None
        
        # 拼接timestamp和secret
        string_to_sign = f"{timestamp}\n{secret}"
        
        # 使用HmacSHA256算法计算签名
        hmac_code = hmac.new(
            string_to_sign.encode("utf-8"),
            digestmod=hashlib.sha256
        ).digest()
        
        # 对签名进行base64编码
        sign = base64.b64encode(hmac_code).decode('utf-8')
        return sign
    
    def upload_image(self, image_path=None, image_data=None):
        """
        上传图片到飞书获取image_key
        
        Args:
            image_path: 本地图片路径（可选）
            image_data: 图片二进制数据（可选）
        
        Returns:
            image_key: 飞书图片key，失败返回None
        """
        access_token = self.get_access_token()
        if not access_token:
            logger.warning("无法获取access_token，跳过图片上传")
            return None
        
        url = "https://open.feishu.cn/open-apis/im/v1/images"
        
        try:
            # 准备图片数据
            if image_data:
                # 直接使用提供的二进制数据
                import io
                files = {
                    'image': ('qrcode.png', io.BytesIO(image_data), 'image/png')
                }
            elif image_path:
                # 从文件读取
                with open(image_path, 'rb') as f:
                    files = {
                        'image': f
                    }
            else:
                logger.error("必须提供 image_path 或 image_data")
                return None
            
            data = {
                'image_type': 'message'
            }
            headers = {
                'Authorization': f'Bearer {access_token}'
            }
            
            response = requests.post(
                url,
                headers=headers,
                data=data,
                files=files if not image_data else files,
                timeout=30
            )
            
            result = response.json()
            
            if result.get("code") == 0:
                image_key = result.get("data", {}).get("image_key")
                logger.info(f"✅ 图片上传成功: {image_key}")
                return image_key
            else:
                logger.error(f"图片上传失败: {result}")
                return None
        
        except Exception as e:
            logger.error(f"图片上传异常: {e}")
            return None
    
    @retry_on_failure(max_attempts=2)
    def send_webhook_message(self, title, content_lines):
        """
        发送Webhook消息（支持签名验证）
        
        Args:
            title: 消息标题
            content_lines: 内容行列表
        """
        if not self.webhook_url:
            logger.warning("Webhook URL未设置，跳过发送")
            return
        
        # 获取签名密钥（如果配置了）
        webhook_secret = os.getenv("FEISHU_WEBHOOK_SECRET")
        
        # 生成时间戳和签名
        timestamp = str(int(time.time()))
        sign = None
        if webhook_secret:
            sign = self._generate_sign(timestamp, webhook_secret)
        
        # 构建消息卡片
        card = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": title
                    },
                    "template": "blue"
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "plain_text",
                            "content": line
                        }
                    }
                    for line in content_lines
                ]
            }
        }
        
        # 添加签名（如果有）
        if sign:
            card["timestamp"] = timestamp
            card["sign"] = sign
        
        try:
            response = requests.post(
                self.webhook_url,
                json=card,
                timeout=10
            )
            result = response.json()
            
            if result.get("code") == 0 or result.get("StatusCode") == 0:
                logger.info("✅ 飞书通知发送成功")
            else:
                logger.warning(f"飞书通知发送失败: {result}")
        
        except Exception as e:
            logger.error(f"飞书通知发送异常: {e}")
    
    def send_success_notification(self, ctx, result):
        """发送成功通知"""
        # 获取标题（从result或ctx中）
        title = result.get('title') or ctx.get('title', f"{ctx.get('city', 'N/A')}旅游攻略")
        
        content_lines = [
            f"标题: {title}",
            f"状态: ✅ 发布成功"
        ]
        
        self.send_webhook_message("🎉 小红书发布成功", content_lines)
    
    def send_failure_notification(self, ctx, error, title=None, step=None):
        """
        发送失败通知（增强版，包含详细错误定位）
        
        Args:
            ctx: 上下文信息
            error: 错误信息
            title: 标题
            step: 失败的步骤名称
        """
        # 获取标题
        if not title:
            title = ctx.get('title', f"{ctx.get('city', 'N/A')}旅游攻略")
        
        # 分析错误原因
        error_str = str(error)
        error_type = type(error).__name__
        
        # 错误分类和建议
        error_category = "未知错误"
        suggestions = []
        
        if "MCP" in error_str or "Session" in error_str:
            error_category = "🔌 MCP服务问题"
            suggestions = [
                "检查MCP服务是否运行: sudo systemctl status xhs-mcp",
                "检查是否已登录: 访问 http://localhost:18060",
                "重启MCP服务: sudo systemctl restart xhs-mcp"
            ]
        elif "timeout" in error_str.lower() or "Timeout" in error_str:
            error_category = "⏱️ 超时错误"
            suggestions = [
                "检查网络连接是否正常",
                "检查小红书服务器是否可访问",
                "增加超时时间配置"
            ]
        elif "Permission" in error_str or "Access denied" in error_str:
            error_category = "🔐 权限错误"
            suggestions = [
                "检查飞书应用权限是否完整",
                "检查文件/目录权限: ls -la",
                "检查API密钥是否有效"
            ]
        elif "Network" in error_str or "Connection" in error_str:
            error_category = "🌐 网络错误"
            suggestions = [
                "检查服务器网络连接",
                "检查防火墙设置",
                "测试外网连接: ping baidu.com"
            ]
        elif "Image" in error_str or "图片" in error_str:
            error_category = "🖼️ 图片处理错误"
            suggestions = [
                "检查磁盘空间: df -h",
                "检查temp_images目录权限",
                "检查图片下载链接是否有效"
            ]
        elif "AI" in error_str or "API" in error_str or "DeepSeek" in error_str or "Qwen" in error_str:
            error_category = "🤖 AI服务错误"
            suggestions = [
                "检查AI API密钥是否有效",
                "检查API额度是否充足",
                "检查AI服务是否可访问"
            ]
        elif "Font" in error_str or "字体" in error_str:
            error_category = "🔤 字体错误"
            suggestions = [
                "安装中文字体: sudo apt install fonts-wqy-microhei",
                "检查字体文件是否存在",
                "验证字体安装: fc-list :lang=zh"
            ]
        else:
            suggestions = [
                "查看完整日志: tail -f logs/xhs_bot_*.log",
                "检查配置文件: cat config/.env",
                "手动测试: python src/scheduler_v2.py --force"
            ]
        
        # 构建详细的通知内容
        content_lines = [
            f"📝 标题: {title}",
            f"🏙️ 城市: {ctx.get('city', 'N/A')}",
            f"📍 主题: {ctx.get('topic_name', ctx.get('topic', 'N/A'))}",
            "",
            f"❌ 状态: 发布失败",
            f"🔍 错误类型: {error_category}",
            f"⚙️ 异常类型: {error_type}",
        ]
        
        # 添加失败步骤
        if step:
            content_lines.append(f"📍 失败步骤: {step}")
        
        content_lines.append("")
        content_lines.append(f"💬 错误信息:")
        
        # 错误信息分行显示（限制长度）
        error_lines = error_str.split('\n')
        for line in error_lines[:3]:  # 只显示前3行
            if line.strip():
                content_lines.append(f"   {line[:100]}")
        
        if len(error_lines) > 3:
            content_lines.append(f"   ... (共{len(error_lines)}行)")
        
        # 添加建议
        if suggestions:
            content_lines.append("")
            content_lines.append("💡 排查建议:")
            for i, suggestion in enumerate(suggestions[:3], 1):  # 最多3条建议
                content_lines.append(f"   {i}. {suggestion}")
        
        # 添加时间戳
        content_lines.append("")
        content_lines.append(f"🕐 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        self.send_webhook_message("❌ 小红书发布失败", content_lines)
    
    def get_table_id(self):
        """
        获取多维表格中的第一个table_id
        如果已配置FEISHU_TABLE_TABLE_ID，直接使用
        """
        if self.table_id:
            return self.table_id
        
        if not self.base_id:
            return None
        
        access_token = self.get_access_token()
        if not access_token:
            return None
        
        # 获取表格列表
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.base_id}/tables"
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            result = response.json()
            
            if result.get("code") == 0 and result.get("data", {}).get("items"):
                # 使用第一个表格
                first_table = result["data"]["items"][0]
                self.table_id = first_table["table_id"]
                logger.info(f"自动获取到table_id: {self.table_id}")
                return self.table_id
            else:
                logger.warning(f"获取table_id失败: {result}")
                return None
        
        except Exception as e:
            logger.error(f"获取table_id异常: {e}")
            return None
    
    def append_table_record(self, record):
        """
        添加表格记录
        
        Args:
            record: {
                "日期": "2025-12-18",
                "城市": "成都",
                "状态": "成功",
                ...
            }
        """
        if not self.base_id:
            logger.warning("Base ID未设置，跳过表格记录")
            return
        
        access_token = self.get_access_token()
        if not access_token:
            logger.warning("无法获取access_token，跳过表格记录")
            return
        
        # 获取table_id
        table_id = self.get_table_id()
        if not table_id:
            logger.warning("无法获取table_id，跳过表格记录")
            return
        
        # 构建API请求
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.base_id}/tables/{table_id}/records"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # 转换字段格式
        fields = {}
        for key, value in record.items():
            fields[key] = value
        
        data = {
            "fields": fields
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=10)
            result = response.json()
            
            if result.get("code") == 0:
                logger.info("✅ 飞书表格记录成功")
            else:
                logger.warning(f"飞书表格记录失败: {result}")
        
        except Exception as e:
            logger.error(f"飞书表格记录异常: {e}")
    
    def query_recent_records(self, days=30):
        """
        查询最近的记录
        
        Args:
            days: 查询最近多少天
        
        Returns:
            记录列表
        """
        # TODO: 实现查询逻辑
        # 这里需要知道具体的表格ID和字段映射
        logger.warning("query_recent_records 未实现，返回空列表")
        return []

