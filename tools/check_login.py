#!/usr/bin/env python3
"""
小红书登录状态检查与二维码获取工具

用于无GUI环境（如Ubuntu服务器）的登录检查和二维码获取
"""

import os
import sys
import asyncio
import json
import httpx

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from dotenv import load_dotenv
from src.utils.logger import logger
from src.services.xhs_mcp_client import XhsMcpClient
from src.services.feishu_client import FeishuClient

# MCP 服务地址
MCP_URL = os.getenv("XHS_MCP_URL", "http://localhost:18060")

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


async def get_qrcode_direct_http() -> dict:
    """
    直接通过 HTTP 调用 MCP 获取登录二维码
    绕过 langchain_mcp_adapters，避免 SSE 流式响应问题
    
    Returns:
        dict: 包含 base64 数据的字典，或 error 字段
    """
    try:
        logger.info("🔗 使用直接 HTTP 调用获取二维码...")
        
        # 构建 JSON-RPC 请求
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "get_login_qrcode",
                "arguments": {}
            }
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            # 发送请求，监听 SSE 流
            async with client.stream(
                "POST",
                f"{MCP_URL}/mcp",
                json=payload,
                headers={"Accept": "text/event-stream"}
            ) as response:
                # 读取所有 SSE 事件
                full_response = ""
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]  # 移除 "data: " 前缀
                        try:
                            result = json.loads(data)
                            if "result" in result and "content" in result["result"]:
                                # 找到最终结果
                                content = result["result"]["content"]
                                for item in content:
                                    if isinstance(item, dict) and item.get("type") == "image":
                                        # MCP 返回的是 "data" 字段
                                        base64_data = item.get("data") or item.get("base64")
                                        if base64_data:
                                            logger.info("✅ 直接 HTTP 调用成功获取二维码")
                                            return {"base64": base64_data}
                        except json.JSONDecodeError:
                            continue
                
                logger.warning("⚠️  SSE 响应中未找到二维码数据")
                return {"error": "no_qrcode_in_response"}
                
    except httpx.TimeoutException:
        logger.error("❌ 直接 HTTP 调用超时（60秒）")
        return {"error": "timeout"}
    except Exception as e:
        logger.error(f"❌ 直接 HTTP 调用失败: {e}")
        return {"error": str(e)}


async def check_login_status_direct_http() -> dict:
    """
    直接通过 HTTP 调用 MCP 检查登录状态
    """
    try:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "check_login_status",
                "arguments": {}
            }
        }
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            async with client.stream(
                "POST",
                f"{MCP_URL}/mcp",
                json=payload,
                headers={"Accept": "text/event-stream"}
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        try:
                            result = json.loads(data)
                            if "result" in result and "content" in result["result"]:
                                content = result["result"]["content"]
                                for item in content:
                                    if isinstance(item, dict) and item.get("type") == "text":
                                        text = item.get("text", "")
                                        is_login = "已登录" in text or "logged in" in text.lower()
                                        return {"is_login": is_login, "message": text}
                        except json.JSONDecodeError:
                            continue
        
        return {"is_login": False, "message": "未知状态"}
        
    except Exception as e:
        logger.error(f"❌ 检查登录状态失败: {e}")
        return {"is_login": False, "error": str(e)}


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
        logger.info("=" * 60)
        logger.info("🔍 使用直接 HTTP 方式检查登录状态...")
        logger.info("=" * 60)
        
        # 直接 HTTP 检查登录状态（更稳定）
        status = await check_login_status_direct_http()
        
        if status.get('error'):
            logger.warning(f"⚠️  检查登录状态出错: {status.get('error')}")
            logger.info("尝试使用 langchain_mcp_adapters 方式...")
            # 降级到旧方式
            mcp = XhsMcpClient()
            if not await check_mcp_connection(mcp):
                logger.error("❌ 无法连接到 MCP 服务")
                return False
            try:
                status = await asyncio.wait_for(mcp.check_login_status(), timeout=15.0)
            except asyncio.TimeoutError:
                logger.error("❌ 检查登录状态超时")
                return False
        
        if status.get('is_login'):
            logger.info("✅ 已登录小红书")
            if status.get('message'):
                logger.info(f"📝 {status.get('message')}")
            return True
        
        # 未登录，获取二维码
        logger.warning("❌ 未登录小红书")
        logger.info("")
        logger.info("=" * 60)
        logger.info("📱 正在生成登录二维码...")
        logger.info("=" * 60)
        
        # 直接 HTTP 获取二维码（绕过 langchain_mcp_adapters 的 SSE 问题）
        logger.info("⏱️  这可能需要 10-30 秒，请耐心等待...")
        qr_result = await get_qrcode_direct_http()
        
        # 处理错误
        if qr_result.get('error'):
            error_type = qr_result['error']
            logger.error(f"❌ 获取二维码失败: {error_type}")
            
            if error_type == 'timeout':
                logger.warning("⚠️  MCP 服务获取二维码超时")
                logger.info("建议：重启 MCP 服务后重试")
            
            # 发送失败通知到飞书
            feishu = FeishuClient()
            feishu.send_webhook_message(
                "🔐 小红书登录",
                f"⚠️ 自动获取二维码失败: {error_type}\n\n请使用 SSH 端口转发登录:\nssh -L 18060:localhost:18060 root@server\n然后访问 http://localhost:18060",
                color="red"
            )
            return False
        
        # 提取 base64 数据
        qr_base64 = qr_result.get('base64')
        
        if not qr_base64:
            logger.error("❌ 未能从结果中提取二维码数据")
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
    logger.info(f"  MCP URL: {MCP_URL}")
    
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
