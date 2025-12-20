#!/usr/bin/env python3
"""
测试脚本：获取小红书登录二维码

用途：
1. 检查 MCP 服务是否正常
2. 获取登录二维码
3. 上传到飞书（可选）
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from src.services.xhs_mcp_client import XhsMcpClient
from src.services.feishu_client import FeishuClient
from src.utils.logger import logger


async def main():
    """主函数"""
    print("=" * 70)
    print("🔐 小红书登录二维码获取工具")
    print("=" * 70)
    print()
    
    # 1. 创建 MCP 客户端
    logger.info("📡 连接 MCP 服务...")
    client = XhsMcpClient()
    
    try:
        # 2. 检查登录状态
        logger.info("🔍 检查登录状态...")
        status = await client.check_login_status()
        
        if status.get('is_login'):
            logger.info("✅ 已登录小红书")
            logger.info(f"   用户名: {status.get('username', 'N/A')}")
            print()
            print("=" * 70)
            print("✅ 已登录，无需扫码")
            print("=" * 70)
            return
        
        logger.info("❌ 未登录，正在生成二维码...")
        
        # 3. 生成二维码
        qr_path = "login_qrcode.png"
        logger.info(f"📸 生成二维码到: {qr_path}")
        
        result = await client.get_login_qrcode(save_path=qr_path)
        
        # 4. 检查结果
        if isinstance(result, dict) and result.get('error'):
            logger.error(f"❌ 生成二维码失败: {result['error']}")
            return
        
        # 5. 验证文件是否存在
        if os.path.exists(qr_path):
            file_size = os.path.getsize(qr_path)
            logger.info(f"✅ 二维码已保存: {qr_path} ({file_size} 字节)")
            
            print()
            print("=" * 70)
            print("✅ 二维码生成成功！")
            print("=" * 70)
            print()
            print(f"📁 本地路径: {os.path.abspath(qr_path)}")
            print()
            print("📱 扫码方式：")
            print("   1. 如果在本地：直接打开图片文件")
            print("   2. 如果在服务器：使用以下命令下载")
            print(f"      scp root@your-server:{os.path.abspath(qr_path)} ~/Downloads/")
            print()
            
            # 6. 询问是否上传到飞书
            try:
                upload = input("是否上传到飞书？(y/n): ").strip().lower()
                if upload == 'y':
                    logger.info("📤 上传到飞书...")
                    feishu = FeishuClient()
                    
                    # 读取图片
                    with open(qr_path, 'rb') as f:
                        image_data = f.read()
                    
                    # 上传图片
                    image_key = feishu.upload_image(image_data=image_data)
                    logger.info(f"✅ 图片已上传: {image_key}")
                    
                    # 发送消息
                    feishu.send_webhook_message(
                        "🔐 小红书登录二维码",
                        [
                            "请使用小红书 App 扫描以下二维码登录:",
                            "",
                            f"![二维码](https://open.feishu.cn/open-apis/image/v4/{image_key})",
                            "",
                            "⏰ 二维码有效期较短，请尽快扫描",
                            "❌ 如果二维码失效，请重新运行此工具"
                        ]
                    )
                    logger.info("✅ 已发送到飞书")
                    print()
                    print("✅ 二维码已发送到飞书群！")
            except KeyboardInterrupt:
                print("\n⏸️  跳过飞书上传")
            except Exception as e:
                logger.error(f"❌ 上传飞书失败: {e}")
        else:
            logger.error(f"❌ 二维码文件未生成: {qr_path}")
            logger.info("💡 可能原因：")
            logger.info("   1. MCP 服务未正常运行")
            logger.info("   2. Chrome/Chromium 启动失败")
            logger.info("   3. 网络连接问题")
        
        print()
        print("=" * 70)
        
    except asyncio.TimeoutError:
        logger.error("❌ 操作超时（60秒）")
        logger.info("💡 请检查 MCP 服务是否正常运行")
    except Exception as e:
        logger.exception(f"❌ 执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # 加载环境变量
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / "config" / ".env"
    load_dotenv(env_path)
    
    # 运行
    asyncio.run(main())

