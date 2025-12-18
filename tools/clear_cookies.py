#!/usr/bin/env python3
"""
清除小红书MCP的cookies

用于在登录卡住或需要重新登录时清除旧的登录信息
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.services.xhs_mcp_client import XhsMcpClient
from src.utils.logger import logger


async def clear_cookies():
    """清除cookies"""
    try:
        logger.info("="*60)
        logger.info("🧹 清除小红书Cookies")
        logger.info("="*60)
        logger.info("")
        
        client = XhsMcpClient()
        
        # 连接到MCP服务
        await client._ensure_connected()
        
        # 列出所有可用工具
        logger.info("📋 可用工具列表:")
        for i, tool in enumerate(client.tools, 1):
            tool_name = getattr(tool, "name", "unknown")
            logger.info(f"  {i}. {tool_name}")
        logger.info("")
        
        # 查找清除cookies的工具
        clear_tool = None
        for tool in client.tools:
            tool_name = getattr(tool, "name", "")
            # 可能的工具名称
            if tool_name in ["clear_cookies", "logout", "clear_login", "reset_cookies"]:
                clear_tool = tool
                break
        
        if clear_tool:
            tool_name = getattr(clear_tool, "name", "")
            logger.info(f"✅ 找到清除工具: {tool_name}")
            logger.info("正在清除cookies...")
            
            result = await clear_tool.ainvoke({})
            logger.info(f"✅ 清除成功")
            logger.info(f"结果: {result}")
        else:
            logger.warning("⚠️  未找到清除cookies的工具")
            logger.info("")
            logger.info("尝试手动删除cookies文件:")
            
            # 查找可能的cookies文件位置
            possible_paths = [
                "cookies.json",
                "~/xiaohongshu-mcp/cookies.json",
                "/tmp/xhs_cookies.json",
                os.path.expanduser("~/xiaohongshu-mcp/cookies.json"),
            ]
            
            deleted_any = False
            for path in possible_paths:
                abs_path = os.path.abspath(os.path.expanduser(path))
                if os.path.exists(abs_path):
                    try:
                        os.remove(abs_path)
                        logger.info(f"  ✅ 已删除: {abs_path}")
                        deleted_any = True
                    except Exception as e:
                        logger.error(f"  ❌ 删除失败 {abs_path}: {e}")
            
            if not deleted_any:
                logger.warning("  ⚠️  未找到cookies文件")
                logger.info("")
                logger.info("请检查MCP服务的工作目录中是否有cookies相关文件")
        
        logger.info("")
        logger.info("="*60)
        logger.info("✅ 操作完成")
        logger.info("="*60)
        logger.info("")
        logger.info("现在可以重新登录:")
        logger.info("  python3 tools/check_login.py")
        logger.info("")
        
    except Exception as e:
        logger.error(f"清除cookies失败: {e}")
        import traceback
        logger.error(f"详细错误:\n{traceback.format_exc()}")


def main():
    """主函数"""
    asyncio.run(clear_cookies())


if __name__ == "__main__":
    main()

