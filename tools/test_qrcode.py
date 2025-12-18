#!/usr/bin/env python3
"""
简单测试脚本：直接调用 MCP 获取登录二维码
遵循 MCP 协议：initialize -> initialized -> tools/call
"""

import asyncio
import json
import httpx

MCP_URL = "http://localhost:18060"


async def get_qrcode():
    """完整 MCP 会话流程获取二维码"""
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        
        # Step 1: 初始化会话
        print("📡 Step 1: 初始化 MCP 会话...")
        init_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0"}
            }
        }
        
        resp = await client.post(
            f"{MCP_URL}/mcp",
            json=init_payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"   响应: {resp.status_code}")
        
        if resp.status_code != 200:
            print(f"   ❌ 初始化失败: {resp.text}")
            return None
        
        init_result = resp.json()
        print(f"   ✅ 服务器: {init_result.get('result', {}).get('serverInfo', {})}")
        
        # 获取 session ID（从响应头）
        session_id = resp.headers.get("mcp-session-id")
        print(f"   Session ID: {session_id}")
        
        # Step 2: 发送 initialized 通知
        print("\n📡 Step 2: 发送 initialized 通知...")
        initialized_payload = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        
        headers = {"Content-Type": "application/json"}
        if session_id:
            headers["mcp-session-id"] = session_id
        
        resp = await client.post(
            f"{MCP_URL}/mcp",
            json=initialized_payload,
            headers=headers
        )
        print(f"   响应: {resp.status_code}")
        
        # Step 3: 调用 get_login_qrcode
        print("\n📡 Step 3: 调用 get_login_qrcode...")
        print("   ⏱️  这可能需要 10-30 秒，请耐心等待...")
        
        call_payload = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "get_login_qrcode",
                "arguments": {}
            }
        }
        
        # 使用流式请求处理 SSE 响应
        async with client.stream(
            "POST",
            f"{MCP_URL}/mcp",
            json=call_payload,
            headers=headers
        ) as response:
            print(f"   响应状态: {response.status_code}")
            content_type = response.headers.get("content-type", "")
            print(f"   Content-Type: {content_type}")
            
            if "text/event-stream" in content_type:
                # SSE 流式响应
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        try:
                            result = json.loads(data)
                            if "result" in result and "content" in result["result"]:
                                content = result["result"]["content"]
                                for item in content:
                                    if item.get("type") == "text":
                                        print(f"   📝 {item.get('text')}")
                                    elif item.get("type") == "image":
                                        base64_data = item.get("data") or item.get("base64")
                                        if base64_data:
                                            print(f"\n✅ 成功获取二维码!")
                                            print(f"   📊 Base64 长度: {len(base64_data)}")
                                            return base64_data
                        except json.JSONDecodeError:
                            continue
            else:
                # 普通 JSON 响应
                text = await response.aread()
                try:
                    result = json.loads(text)
                    print(f"   响应: {json.dumps(result, indent=2, ensure_ascii=False)[:500]}")
                    
                    if "result" in result and "content" in result["result"]:
                        content = result["result"]["content"]
                        for item in content:
                            if item.get("type") == "image":
                                base64_data = item.get("data") or item.get("base64")
                                if base64_data:
                                    print(f"\n✅ 成功获取二维码!")
                                    print(f"   📊 Base64 长度: {len(base64_data)}")
                                    return base64_data
                except:
                    print(f"   响应内容: {text[:500]}")
    
    print("\n❌ 未获取到二维码")
    return None


if __name__ == "__main__":
    print("=" * 50)
    print("🧪 MCP 二维码获取测试")
    print("=" * 50)
    
    result = asyncio.run(get_qrcode())
    
    if result:
        print("\n🎉 测试成功!")
        print(f"🔤 Base64 前50字符: {result[:50]}...")
    else:
        print("\n❌ 测试失败")

