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


def display_qrcode_in_terminal(image_path):
    """在终端显示二维码图片"""
    try:
        from PIL import Image
        
        logger.info("\n" + "="*60)
        logger.info("📱 请使用小红书App扫描下方二维码登录")
        logger.info("="*60)
        
        # 读取图片
        img = Image.open(image_path)
        
        # 转换为黑白
        img = img.convert('L')
        
        # 缩放到合适的终端显示大小
        width, height = img.size
        aspect_ratio = height / width
        new_width = 60
        new_height = int(aspect_ratio * new_width * 0.5)  # 0.5是因为字符高度约为宽度的2倍
        img = img.resize((new_width, new_height))
        
        # 转换为ASCII
        pixels = img.getdata()
        ascii_chars = ['█', '▓', '▒', '░', ' ']
        
        ascii_art = []
        for i in range(0, len(pixels), new_width):
            row = pixels[i:i+new_width]
            ascii_row = ''.join([ascii_chars[min(pixel // 51, 4)] for pixel in row])
            ascii_art.append(ascii_row)
        
        print("\n" + "\n".join(ascii_art) + "\n")
        logger.info("="*60)
        
    except Exception as e:
        logger.warning(f"无法在终端显示二维码: {e}")
        logger.info(f"请查看保存的图片文件: {image_path}")


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
            
            # 生成二维码
            qr_path = "login_qrcode.png"
            qr_result = await client.get_login_qrcode(save_path=qr_path)
            
            logger.info(f"二维码结果类型: {type(qr_result)}")
            logger.info(f"二维码结果: {qr_result}")
            
            # 检查图片是否保存成功
            import os
            if os.path.exists(qr_path):
                logger.info(f"✅ 二维码图片已保存: {qr_path}")
                logger.info(f"图片大小: {os.path.getsize(qr_path)} bytes")
                
                # 在终端显示二维码图片
                display_qrcode_in_terminal(qr_path)
                
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

