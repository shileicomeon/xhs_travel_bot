#!/usr/bin/env python3
"""
小红书登录指引
在 headless 服务器上，使用 SSH 端口转发登录
"""

import os
import sys
import socket

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from dotenv import load_dotenv
load_dotenv(os.path.join(project_root, 'config', '.env'))

from src.services.feishu_client import FeishuClient


def get_server_ip():
    """获取服务器 IP"""
    try:
        # 尝试获取公网 IP
        import urllib.request
        return urllib.request.urlopen('https://api.ipify.org', timeout=5).read().decode('utf8')
    except:
        pass
    
    try:
        # 获取本机 IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "your-server-ip"


def main():
    server_ip = get_server_ip()
    
    print("=" * 60)
    print("🔐 小红书登录指引")
    print("=" * 60)
    print()
    print("由于 headless 环境限制，请使用 SSH 端口转发登录：")
    print()
    print("📋 步骤：")
    print()
    print("1️⃣  在你的 Mac/电脑 上运行：")
    print(f"   ssh -L 18060:localhost:18060 root@{server_ip}")
    print()
    print("2️⃣  打开浏览器访问：")
    print("   http://localhost:18060")
    print()
    print("3️⃣  用小红书 App 扫描页面上的二维码")
    print()
    print("4️⃣  登录成功后，关闭 SSH 连接即可")
    print()
    print("=" * 60)
    
    # 发送到飞书
    try:
        feishu = FeishuClient()
        message = f"""🔐 小红书登录指引

由于服务器 headless 环境限制，请使用 SSH 端口转发登录：

📋 步骤：

1️⃣ 在你的 Mac/电脑 上运行：
```
ssh -L 18060:localhost:18060 root@{server_ip}
```

2️⃣ 打开浏览器访问：
http://localhost:18060

3️⃣ 用小红书 App 扫描页面上的二维码

4️⃣ 登录成功后，关闭 SSH 连接"""
        
        feishu.send_webhook_message("🔐 小红书登录指引", message, color="blue")
        print("✅ 登录指引已发送到飞书")
    except Exception as e:
        print(f"⚠️  飞书通知失败: {e}")


if __name__ == "__main__":
    main()

