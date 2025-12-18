#!/usr/bin/env python3
"""
小红书登录辅助工具（Ubuntu无界面优化版）

用于在无显示器的服务器环境下获取登录二维码
特别优化Ubuntu服务器部署场景
"""

import asyncio
import sys
import os
import socket

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.services.xhs_mcp_client import XhsMcpClient
from src.utils.logger import logger


def get_server_ip():
    """获取服务器IP地址"""
    try:
        # 创建一个UDP socket来获取本机IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "YOUR_SERVER_IP"


def print_banner():
    """打印横幅"""
    print("\n" + "=" * 70)
    print("🔐 小红书登录辅助工具 - Ubuntu无界面优化版")
    print("=" * 70)
    print()


def print_login_methods(server_ip, qr_path):
    """打印登录方法说明"""
    print("\n" + "=" * 70)
    print("📱 登录方式（推荐按顺序尝试）")
    print("=" * 70)
    print()
    
    # 方式1：SSH隧道（最安全）
    print("【方式1】SSH隧道（推荐，最安全）")
    print("-" * 70)
    print("1️⃣  在本地电脑打开终端，执行：")
    print(f"   ssh -L 18060:localhost:18060 user@{server_ip}")
    print()
    print("2️⃣  保持SSH连接，在本地浏览器访问：")
    print("   http://localhost:18060")
    print()
    print("3️⃣  使用小红书App扫描页面上的二维码登录")
    print()
    
    # 方式2：下载二维码（适合Ubuntu）
    print("【方式2】下载二维码扫描（适合Ubuntu服务器）")
    print("-" * 70)
    print("1️⃣  在本地电脑执行以下命令下载二维码：")
    print(f"   scp user@{server_ip}:{os.path.abspath(qr_path)} ~/Downloads/")
    print()
    print("2️⃣  打开下载的图片，使用小红书App扫描")
    print()
    print("3️⃣  扫描后等待10-30秒，然后运行此脚本验证：")
    print("   python tools/login_helper.py")
    print()
    
    # 方式3：临时开放端口（不推荐）
    print("【方式3】临时开放端口（不推荐，仅测试用）")
    print("-" * 70)
    print("⚠️  警告：此方式会暴露端口，登录后立即关闭！")
    print()
    print("1️⃣  开放端口（Ubuntu UFW）：")
    print("   sudo ufw allow 18060/tcp")
    print()
    print("2️⃣  在浏览器访问：")
    print(f"   http://{server_ip}:18060")
    print()
    print("3️⃣  登录后立即关闭端口：")
    print("   sudo ufw delete allow 18060/tcp")
    print()


def print_troubleshooting():
    """打印故障排查"""
    print("\n" + "=" * 70)
    print("🔧 故障排查")
    print("=" * 70)
    print()
    print("❌ 如果MCP服务未运行：")
    print("   sudo systemctl status xhs-mcp")
    print("   sudo systemctl start xhs-mcp")
    print()
    print("❌ 如果端口被占用：")
    print("   sudo lsof -i :18060")
    print("   sudo systemctl restart xhs-mcp")
    print()
    print("❌ 如果二维码过期：")
    print("   重新运行此脚本获取新二维码")
    print("   python tools/login_helper.py")
    print()
    print("❌ 查看MCP服务日志：")
    print("   sudo journalctl -u xhs-mcp -f")
    print()


async def main():
    """主函数"""
    print_banner()
    
    # 获取服务器IP
    server_ip = get_server_ip()
    
    # 创建MCP客户端
    client = XhsMcpClient()
    
    # 检查登录状态
    print("📡 步骤1: 检查当前登录状态...")
    print("-" * 70)
    try:
        status = await client.check_login_status()
        
        if isinstance(status, dict):
            is_logged_in = status.get('is_login') or status.get('logged_in') or status.get('status') == 'logged_in'
            
            if is_logged_in:
                print("✅ 已登录！")
                user_info = status.get('user') or status.get('user_info') or {}
                if user_info:
                    print(f"   👤 用户: {user_info.get('nickname', '未知')}")
                    print(f"   🆔 ID: {user_info.get('user_id', '未知')}")
                print()
                print("🎉 登录成功，可以开始使用系统了！")
                print()
                print("💡 测试发布：")
                print("   cd /opt/xhs_travel_bot")
                print("   source venv/bin/activate")
                print("   python src/scheduler_v2.py --force")
                return
            else:
                print("❌ 未登录，需要扫码登录")
        else:
            print("⚠️  无法确定登录状态，尝试获取二维码...")
    
    except Exception as e:
        print(f"⚠️  检查登录状态失败: {e}")
        print("   继续尝试获取二维码...")
    
    print()
    print("📱 步骤2: 获取登录二维码...")
    print("-" * 70)
    
    # 二维码保存路径
    qr_path = "login_qrcode.png"
    
    try:
        result = await client.get_login_qrcode(save_path=qr_path)
        
        if 'error' in result:
            print(f"❌ 获取二维码失败: {result['error']}")
            print()
            print("💡 可能原因：")
            print("   1. MCP服务未运行")
            print("   2. MCP服务端口不是18060")
            print("   3. 网络连接问题")
            print_troubleshooting()
            return
        
        if 'saved_path' in result:
            abs_path = os.path.abspath(qr_path)
            print(f"✅ 二维码已保存！")
            print(f"   📁 路径: {abs_path}")
            print(f"   📏 文件大小: {os.path.getsize(abs_path)} bytes")
            
            # 打印登录方法
            print_login_methods(server_ip, qr_path)
            
            # 打印快捷命令
            print("=" * 70)
            print("⚡ 快捷命令（复制使用）")
            print("=" * 70)
            print()
            print("# 下载二维码到本地：")
            print(f"scp user@{server_ip}:{abs_path} ~/Downloads/xhs_qrcode.png")
            print()
            print("# SSH隧道（保持连接）：")
            print(f"ssh -L 18060:localhost:18060 user@{server_ip}")
            print()
            print("# 验证登录状态：")
            print("python tools/login_helper.py")
            print()
        else:
            print("✅ 二维码获取成功")
            print(result)
    
    except Exception as e:
        print(f"❌ 获取二维码失败: {e}")
        logger.exception("获取二维码异常")
        print_troubleshooting()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n已取消")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        logger.exception("登录辅助工具异常")

