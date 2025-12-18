#!/usr/bin/env python3
"""
小红书登录状态检查与二维码获取工具

用于无GUI环境（如Ubuntu服务器）的登录检查和二维码获取
"""

import os
import sys
import asyncio

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from dotenv import load_dotenv
from src.utils.logger import logger
from src.services.xhs_mcp_client import XhsMcpClient
from src.services.feishu_client import FeishuClient

# 加载环境变量
load_dotenv(os.path.join(project_root, 'config', '.env'))


def print_banner():
    """打印欢迎横幅"""
    banner = """
╔════════════════════════════════════════════════════════════════╗
║                  🔐 小红书登录检查工具 🔐                    ║
║                                                                ║
║  功能：检查小红书登录状态，未登录时生成二维码                  ║
║  适用场景：Ubuntu 服务器等无 GUI 环境                         ║
╚════════════════════════════════════════════════════════════════╝
"""
    print(banner)


async def check_mcp_connection(mcp: XhsMcpClient) -> bool:
    """
    检查MCP服务连接
    
    Returns:
        True if connected, False otherwise
    """
    try:
        logger.info("🔍 检查 MCP 服务连接...")
        await asyncio.wait_for(mcp._ensure_connected(), timeout=10.0)
        logger.info("✅ MCP 服务连接正常")
        return True
    except asyncio.TimeoutError:
        logger.error("❌ MCP 服务连接超时（10秒）")
        logger.warning("⚠️  MCP 服务可能未启动或卡住")
        logger.info("📋 诊断步骤：")
        logger.info("   1. 检查 MCP 进程: ps aux | grep xiaohongshu-mcp")
        logger.info("   2. 检查端口占用: netstat -tulnp | grep 18060")
        logger.info("   3. 尝试重启 MCP:")
        logger.info("      pkill -f xiaohongshu-mcp")
        logger.info("      cd ~/xiaohongshu-mcp && xvfb-run -a go run . -headless=true &")
        return False
    except Exception as e:
        logger.error(f"❌ MCP 服务连接失败: {e}")
        return False


async def check_and_login():
    """检查登录状态，未登录则获取二维码"""
    try:
        logger.info("初始化 MCP 客户端...")
        mcp = XhsMcpClient()
        
        # 首先检查 MCP 连接
        if not await check_mcp_connection(mcp):
            logger.error("❌ 无法连接到 MCP 服务，请先启动 MCP 服务")
            return False
        
        # 检查登录状态（添加超时）
        logger.info("检查登录状态...")
        try:
            status = await asyncio.wait_for(
                mcp.check_login_status(),
                timeout=15.0
            )
        except asyncio.TimeoutError:
            logger.error("❌ 检查登录状态超时（15秒）")
            logger.warning("⚠️  MCP 服务的 check_login_status 工具可能卡住了")
            logger.info("建议：运行 tools/fix_mcp.sh 重启 MCP 服务")
            return False
        
        if status.get('is_login'):
            logger.info("✅ 已登录小红书")
            return True
        
        # 未登录，获取二维码
        logger.warning("❌ 未登录小红书")
        logger.info("正在生成登录二维码...")
        
        try:
            # 获取二维码（设置15秒超时，避免长时间卡住）
            logger.info("⏱️  设置15秒超时...")
            qr_result = await asyncio.wait_for(
                mcp.get_login_qrcode(),
                timeout=15.0  # 15秒足够了，超过说明有问题
            )
            
            # 处理超时或错误
            if isinstance(qr_result, dict) and qr_result.get('error'):
                error_type = qr_result['error']
                if error_type == 'timeout':
                    logger.error("❌ 获取二维码超时")
                    logger.info("建议：运行 tools/fix_mcp.sh 重启 MCP 服务")
                    return False
                elif error_type == 'get_login_qrcode tool not available':
                    logger.error("❌ MCP 服务不支持 get_login_qrcode 工具")
                    logger.info("请确保使用最新版本的 xiaohongshu-mcp")
                    return False
            
            # 提取 base64 数据
            qr_base64 = None
            if isinstance(qr_result, list):
                for item in qr_result:
                    if isinstance(item, dict) and item.get('type') == 'image':
                        qr_base64 = item.get('base64')
                        break
            elif isinstance(qr_result, dict):
                qr_base64 = qr_result.get('qrcode') or qr_result.get('qr_code') or qr_result.get('image') or qr_result.get('base64')
            
            if not qr_base64:
                logger.error("❌ 未能从结果中提取二维码数据")
                logger.info(f"原始结果: {str(qr_result)[:500]}")
                return False
            
            # 如果是 data URL 格式，移除前缀
            if isinstance(qr_base64, str) and qr_base64.startswith('data:image'):
                qr_base64 = qr_base64.split(',')[1] if ',' in qr_base64 else qr_base64
            
            logger.info("✅ 二维码生成成功")
            
            # 发送到飞书
            logger.info("正在发送二维码到飞书...")
            feishu = FeishuClient()
            
            # 直接上传 base64 数据到飞书（不保存本地文件）
            image_key = feishu.upload_image(qr_base64)
            
            if image_key:
                logger.info(f"✅ 二维码上传成功: {image_key}")
                
                # 发送交互式卡片
                success = feishu.send_webhook_message(
                    "🔐 小红书登录二维码",
                    "",
                    image_key=image_key,
                    color="red"
                )
                
                if success:
                    logger.info("✅ 二维码已发送到飞书")
                    logger.info("📱 请在手机上打开飞书，扫描二维码登录")
                    logger.info("⏰ 二维码有效期：4分钟")
                else:
                    logger.error("❌ 发送飞书消息失败")
            else:
                logger.warning("⚠️  二维码上传失败，发送文本提示到飞书")
                # 如果上传失败，发送文本提示
                feishu.send_webhook_message(
                    "🔐 小红书登录二维码",
                    "二维码已生成，但上传失败。请检查飞书机器人权限（需要 im:resource 或 im:resource:upload）",
                    color="red"
                )
            
            return False
            
        except asyncio.TimeoutError:
            logger.error("❌ 获取登录二维码超时（15秒）")
            logger.warning("⚠️  MCP 服务的 get_login_qrcode 工具在 headless 环境下可能不稳定")
            logger.info("")
            logger.info("📋 解决方案：使用浏览器登录")
            logger.info("=" * 70)
            logger.info("")
            
            # 发送到飞书
            logger.info("正在发送登录指引到飞书...")
            feishu = FeishuClient()
            
            # 获取服务器IP（尝试从环境变量或系统获取）
            import socket
            server_ip = os.getenv("SERVER_IP", "your-server-ip")
            if server_ip == "your-server-ip":
                try:
                    # 尝试获取本机IP
                    hostname = socket.gethostname()
                    server_ip = socket.gethostbyname(hostname)
                except:
                    server_ip = "your-server-ip"
            
            message = f"""🔐 小红书需要登录

⚠️ 自动获取二维码失败（MCP服务在headless环境下不稳定）

📋 登录方法（选择其一）：

方法1️⃣：SSH 端口转发（推荐）
```bash
# 在本地电脑运行
ssh -L 18060:localhost:18060 root@{server_ip}
```
然后浏览器访问：http://localhost:18060
扫码登录后，关闭 SSH 连接即可。

方法2️⃣：临时开放端口
```bash
# 在服务器上运行
sudo ufw allow 18060/tcp  # 临时开放端口
```
浏览器访问：http://{server_ip}:18060
登录后记得关闭端口：
```bash
sudo ufw deny 18060/tcp
```

⏰ 登录完成后，再次运行：
```bash
python3 tools/check_login.py
```"""
            
            feishu.send_webhook_message(
                "🔐 小红书登录指引",
                message,
                color="red"
            )
            
            logger.info("✅ 登录指引已发送到飞书")
            logger.info("")
            logger.info("💡 推荐方法：SSH 端口转发")
            logger.info(f"   ssh -L 18060:localhost:18060 root@{server_ip}")
            logger.info("   然后浏览器访问 http://localhost:18060")
            logger.info("")
            return False
        
    except Exception as e:
        logger.error(f"❌ 执行失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def main():
    """主函数"""
    print_banner()
    
    # 检查环境变量
    logger.info("检查环境配置...")
    mcp_url = os.getenv("XHS_MCP_URL", "http://localhost:18060/mcp")
    logger.info(f"  MCP URL: {mcp_url}")
    
    feishu_webhook = os.getenv("FEISHU_WEBHOOK_URL")
    if feishu_webhook:
        logger.info(f"  飞书 Webhook: 已配置 ✅")
    else:
        logger.warning("  飞书 Webhook: 未配置 ⚠️")
    
    # 执行检查
    try:
        result = asyncio.run(check_and_login())
        
        if result:
            logger.info("🎉 登录状态正常，可以开始发布内容")
            sys.exit(0)
        else:
            logger.warning("⚠️  需要登录小红书")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("\n👋 用户中断")
        sys.exit(130)
    except Exception as e:
        logger.error(f"❌ 程序异常: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
