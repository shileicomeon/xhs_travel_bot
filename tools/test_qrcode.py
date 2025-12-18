#!/usr/bin/env python3
"""
简单测试脚本：直接调用 MCP 获取登录二维码
"""

import asyncio
import json
import httpx

MCP_URL = "http://localhost:18060"


async def get_qrcode():
    """直接 HTTP 调用获取二维码"""
    
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "get_login_qrcode",
            "arguments": {}
        }
    }
    
    print(f"🔗 调用 {MCP_URL}/mcp ...")
    print("⏱️  等待中（可能需要 10-30 秒）...")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream(
            "POST",
            f"{MCP_URL}/mcp",
            json=payload,
            headers={"Accept": "text/event-stream"}
        ) as response:
            print(f"📡 响应状态: {response.status_code}")
            
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    try:
                        result = json.loads(data)
                        print(f"\n📦 收到数据:")
                        print(json.dumps(result, indent=2, ensure_ascii=False)[:500])
                        
                        if "result" in result and "content" in result["result"]:
                            content = result["result"]["content"]
                            for item in content:
                                if item.get("type") == "image":
                                    base64_data = item.get("data") or item.get("base64")
                                    if base64_data:
                                        print(f"\n✅ 成功获取二维码!")
                                        print(f"📊 Base64 长度: {len(base64_data)}")
                                        print(f"🔤 Base64 前50字符: {base64_data[:50]}...")
                                        return base64_data
                    except json.JSONDecodeError:
                        continue
    
    print("❌ 未获取到二维码")
    return None


if __name__ == "__main__":
    print("=" * 50)
    print("🧪 MCP 二维码获取测试")
    print("=" * 50)
    
    result = asyncio.run(get_qrcode())
    
    if result:
        print("\n🎉 测试成功!")
    else:
        print("\n❌ 测试失败")

