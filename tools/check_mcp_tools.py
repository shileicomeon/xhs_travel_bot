#!/usr/bin/env python3
"""
检查 MCP 服务支持的工具列表

用于诊断 MCP 服务是否正常工作，以及支持哪些工具
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

# 加载环境变量
load_dotenv(os.path.join(project_root, 'config', '.env'))


async def check_mcp_tools():
    """检查 MCP 服务支持的工具"""
    try:
        logger.info("初始化 MCP 客户端...")
        mcp = XhsMcpClient()
        
        # 连接到 MCP
        logger.info("连接到 MCP 服务...")
        await asyncio.wait_for(mcp._ensure_connected(), timeout=10.0)
        logger.info("✅ 连接成功")
        
        # 获取工具列表
        logger.info("\n📋 MCP 服务支持的工具列表：")
        logger.info("=" * 80)
        
        if mcp.tools:
            for i, tool in enumerate(mcp.tools, 1):
                tool_name = getattr(tool, 'name', 'unknown')
                tool_desc = getattr(tool, 'description', '无描述')
                
                logger.info(f"\n{i}. 工具名称: {tool_name}")
                logger.info(f"   描述: {tool_desc}")
                
                # 尝试获取工具的参数信息
                if hasattr(tool, 'args_schema'):
                    logger.info(f"   参数: {tool.args_schema}")
        else:
            logger.warning("⚠️  未找到任何工具")
        
        logger.info("\n" + "=" * 80)
        
        # 检查关键工具
        critical_tools = ['check_login_status', 'get_login_qrcode', 'search_feeds', 'publish_content']
        logger.info("\n🔍 检查关键工具：")
        
        available_tools = [getattr(tool, 'name', '') for tool in mcp.tools] if mcp.tools else []
        
        for tool_name in critical_tools:
            if tool_name in available_tools:
                logger.info(f"   ✅ {tool_name}")
            else:
                logger.error(f"   ❌ {tool_name} (缺失)")
        
        # 如果有 get_login_qrcode，尝试测试调用
        if 'get_login_qrcode' in available_tools:
            logger.info("\n🧪 测试调用 get_login_qrcode...")
            try:
                tool = mcp._get_tool('get_login_qrcode')
                logger.info(f"   工具对象: {tool}")
                logger.info(f"   工具类型: {type(tool)}")
                
                # 尝试调用（设置较短超时）
                logger.info("   正在调用工具（超时10秒）...")
                result = await asyncio.wait_for(
                    tool.ainvoke({}),
                    timeout=10.0
                )
                logger.info(f"   ✅ 调用成功")
                logger.info(f"   返回类型: {type(result)}")
                logger.info(f"   返回内容（前500字符）: {str(result)[:500]}")
                
            except asyncio.TimeoutError:
                logger.error("   ❌ 调用超时（10秒）")
                logger.warning("   ⚠️  工具调用卡住了，这就是问题所在！")
            except Exception as e:
                logger.error(f"   ❌ 调用失败: {e}")
        
        return True
        
    except asyncio.TimeoutError:
        logger.error("❌ MCP 连接超时")
        return False
    except Exception as e:
        logger.error(f"❌ 执行失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def main():
    """主函数"""
    print("""
╔════════════════════════════════════════════════════════════════╗
║              🔧 MCP 服务工具检查 🔧                           ║
╚════════════════════════════════════════════════════════════════╝
""")
    
    # 检查环境变量
    mcp_url = os.getenv("XHS_MCP_URL", "http://localhost:18060/mcp")
    logger.info(f"MCP URL: {mcp_url}")
    
    # 执行检查
    try:
        result = asyncio.run(check_mcp_tools())
        sys.exit(0 if result else 1)
        
    except KeyboardInterrupt:
        logger.info("\n👋 用户中断")
        sys.exit(130)
    except Exception as e:
        logger.error(f"❌ 程序异常: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

