#!/usr/bin/env python3
"""
小红书登录辅助工具

用于在无显示器的服务器环境下获取登录二维码
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.services.xhs_mcp_client import XhsMcpClient
from src.utils.logger import logger


async def main():
    """主函数"""
    print("=" * 60)
    print("小红书登录辅助工具")
    print("=" * 60)
    print()
    
    # 创建MCP客户端
    client = XhsMcpClient()
    
    # 检查登录状态
    print("1. 检查当前登录状态...")
    try:
        status = await client.check_login_status()
        
        if isinstance(status, dict):
            is_logged_in = status.get('is_login') or status.get('logged_in') or status.get('status') == 'logged_in'
            
            if is_logged_in:
                print("✅ 已登录！")
                user_info = status.get('user') or status.get('user_info') or {}
                if user_info:
                    print(f"   用户: {user_info.get('nickname', '未知')}")
                    print(f"   ID: {user_info.get('user_id', '未知')}")
                return
            else:
                print("❌ 未登录")
        else:
            print("⚠️  无法确定登录状态")
    
    except Exception as e:
        print(f"⚠️  检查登录状态失败: {e}")
    
    print()
    print("2. 获取登录二维码...")
    
    # 二维码保存路径
    qr_path = "login_qrcode.png"
    
    try:
        result = await client.get_login_qrcode(save_path=qr_path)
        
        if 'error' in result:
            print(f"❌ {result['error']}")
            print()
            print("请使用以下方式之一登录：")
            print()
            print("方式1: SSH隧道（推荐）")
            print("  在本地电脑执行:")
            print("  ssh -L 18060:localhost:18060 user@server-ip")
            print("  然后在本地浏览器访问: http://localhost:18060")
            print()
            print("方式2: 端口转发")
            print("  配置防火墙允许18060端口访问")
            print("  在浏览器访问: http://server-ip:18060")
            return
        
        if 'saved_path' in result:
            print(f"✅ 二维码已保存到: {result['saved_path']}")
            print()
            print("下一步:")
            print("1. 将二维码下载到本地:")
            print(f"   scp user@server-ip:{os.path.abspath(qr_path)} .")
            print()
            print("2. 使用小红书App扫描二维码登录")
            print()
            print("3. 登录后再次运行此脚本验证:")
            print("   python tools/login_helper.py")
        else:
            print("✅ 二维码获取成功")
            print(result)
    
    except Exception as e:
        print(f"❌ 获取二维码失败: {e}")
        logger.exception("获取二维码异常")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n已取消")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        logger.exception("登录辅助工具异常")

