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
    
    def send_failure_notification(self, ctx, error, title=None):
        """发送失败通知"""
        # 获取标题
        if not title:
            title = ctx.get('title', f"{ctx.get('city', 'N/A')}旅游攻略")
        
        content_lines = [
            f"标题: {title}",
            f"状态: ❌ 发布失败"
        ]
        
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

