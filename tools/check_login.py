#!/usr/bin/env python3
"""
检查小红书登录状态并显示二维码
"""

import sys
import asyncio
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# 加载环境变量
env_path = Path(__file__).parent.parent / "config" / ".env"
load_dotenv(env_path)

from src.utils.logger import logger
from src.services.xhs_mcp_client import XhsMcpClient


async def check_and_login():
    """检查登录状态并生成二维码"""
    client = XhsMcpClient()
    
    logger.info("="*60)
    logger.info("🔐 检查小红书登录状态...")
    logger.info("="*60)
    
    try:
        # 检查登录状态
        status = await client.check_login_status()
        
        if status['is_login']:
            logger.info("✅ 已登录小红书")
            logger.info(f"原始结果: {status['raw_result']}")
            return True
        else:
            logger.warning("❌ 未登录小红书")
            logger.info("正在生成登录二维码...")
            
            # 生成二维码（不保存本地文件）
            qr_result = await client.get_login_qrcode()
            
            logger.info(f"二维码结果类型: {type(qr_result)}")
            
            # 提取base64图片数据
            import base64
            qr_base64 = None
            if isinstance(qr_result, list):
                for item in qr_result:
                    if isinstance(item, dict) and item.get('type') == 'image':
                        qr_base64 = item.get('base64')
                        break
            
            if qr_base64:
                logger.info("✅ 获取到二维码数据")
                
                # 解码base64为二进制数据
                qr_image_data = base64.b64decode(qr_base64)
                logger.info(f"图片大小: {len(qr_image_data)} bytes")
                
                # 通过飞书发送二维码图片
                try:
                    from src.services.feishu_client import FeishuClient
                    import requests
                    import time
                    
                    feishu = FeishuClient()
                    
                    # 直接上传图片数据到飞书（不保存本地）
                    logger.info("正在上传二维码图片到飞书...")
                    image_key = feishu.upload_image(image_data=qr_image_data)
                    
                    if image_key and feishu.webhook_url:
                        # 发送带图片的消息卡片
                        card = {
                            "msg_type": "interactive",
                            "card": {
                                "header": {
                                    "title": {
                                        "tag": "plain_text",
                                        "content": "🔐 小红书登录二维码"
                                    },
                                    "template": "blue"
                                },
                                "elements": [
                                    {
                                        "tag": "div",
                                        "text": {
                                            "tag": "plain_text",
                                            "content": "📱 请使用小红书App扫描下方二维码登录"
                                        }
                                    },
                                    {
                                        "tag": "img",
                                        "img_key": image_key,
                                        "alt": {
                                            "tag": "plain_text",
                                            "content": "登录二维码"
                                        }
                                    },
                                    {
                                        "tag": "note",
                                        "elements": [
                                            {
                                                "tag": "plain_text",
                                                "content": f"⏰ 二维码有效期：4分钟\n📂 图片路径: {os.path.abspath(qr_path)}"
                                            }
                                        ]
                                    }
                                ]
                            }
                        }
                        
                        # 添加签名（如果有）
                        webhook_secret = os.getenv("FEISHU_WEBHOOK_SECRET")
                        if webhook_secret:
                            timestamp = str(int(time.time()))
                            sign = feishu._generate_sign(timestamp, webhook_secret)
                            card["timestamp"] = timestamp
                            card["sign"] = sign
                        
                        response = requests.post(feishu.webhook_url, json=card, timeout=10)
                        result = response.json()
                        
                        if result.get("code") == 0 or result.get("StatusCode") == 0:
                            logger.info("✅ 二维码图片已发送到飞书")
                        else:
                            logger.warning(f"⚠️  发送飞书消息失败: {result}")
                    else:
                        # 如果图片上传失败，发送文本提示
                        content_lines = [
                            "🔐 小红书登录二维码",
                            "",
                            f"📂 图片路径: {os.path.abspath(qr_path)}",
                            "",
                            "下载命令:",
                            f"scp root@server:{os.path.abspath(qr_path)} .",
                            "",
                            "⏰ 二维码有效期：4分钟"
                        ]
                        feishu.send_webhook_message("🔐 小红书登录二维码", content_lines)
                        logger.info("✅ 二维码路径已发送到飞书")
                    
                except Exception as e:
                    logger.warning(f"⚠️  发送飞书通知失败: {e}")
                    import traceback
                    logger.debug(traceback.format_exc())
                
                logger.info(f"\n二维码图片已保存到: {qr_path}")
                logger.info("如果在远程服务器上，也可以下载图片:")
                logger.info(f"  scp user@server:{os.path.abspath(qr_path)} .")
                logger.info("\n扫码登录后，请重新运行此脚本验证")
                logger.info("="*60)
            else:
                logger.error("❌ 二维码图片未生成")
                logger.info("请检查MCP服务是否正常运行")
            
            return False
            
    except Exception as e:
        logger.error(f"检查登录状态失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def main():
    """主函数"""
    result = asyncio.run(check_and_login())
    
    if result:
        logger.info("\n✅ 登录检查通过，可以开始发布内容")
        sys.exit(0)
    else:
        logger.info("\n❌ 需要登录后才能继续")
        sys.exit(1)


if __name__ == "__main__":
    main()

