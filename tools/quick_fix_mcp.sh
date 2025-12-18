#!/bin/bash

# 快速修复 MCP 服务（清理浏览器状态）

echo "=========================================="
echo "🔧 快速修复 MCP 服务"
echo "=========================================="
echo ""

# 1. 强制停止所有相关进程
echo "1️⃣ 停止所有 MCP 相关进程..."
pkill -9 -f "xiaohongshu-mcp" 2>/dev/null
pkill -9 -f "go run.*headless" 2>/dev/null
pkill -9 -f "Xvfb" 2>/dev/null
pkill -9 -f "chromium" 2>/dev/null
sleep 2
echo "✅ 已停止"
echo ""

# 2. 清理浏览器缓存和 cookies
echo "2️⃣ 清理浏览器数据..."

# 查找 MCP 目录
if [ -d "$HOME/xiaohongshu-mcp" ]; then
    MCP_DIR="$HOME/xiaohongshu-mcp"
elif [ -d "/opt/xiaohongshu-mcp" ]; then
    MCP_DIR="/opt/xiaohongshu-mcp"
else
    echo "❌ 未找到 MCP 目录，请手动指定："
    echo "   export MCP_DIR=/path/to/xiaohongshu-mcp"
    echo "   bash tools/quick_fix_mcp.sh"
    exit 1
fi

echo "   MCP 目录: $MCP_DIR"

# 清理 cookies 和缓存
rm -f "$MCP_DIR/cookies.json" 2>/dev/null
rm -rf "$MCP_DIR/.cache" 2>/dev/null
rm -rf "$HOME/.cache/chromium" 2>/dev/null
rm -rf "/tmp/.X*" 2>/dev/null
echo "✅ 已清理"
echo ""

# 3. 重启 MCP 服务
echo "3️⃣ 重启 MCP 服务..."
cd "$MCP_DIR" || exit 1

# 使用 xvfb 启动（后台运行）
nohup xvfb-run -a go run . -headless=true > /tmp/mcp.log 2>&1 &
MCP_PID=$!
echo "✅ MCP 服务已启动 (PID: $MCP_PID)"
echo ""

# 4. 等待服务就绪
echo "4️⃣ 等待服务就绪..."
for i in {1..10}; do
    sleep 2
    
    # 检查端口
    if netstat -tln 2>/dev/null | grep -q ":18060" || ss -tln 2>/dev/null | grep -q ":18060"; then
        # 尝试 HTTP 请求
        if curl -s http://localhost:18060/mcp > /dev/null 2>&1; then
            echo "✅ MCP 服务已就绪！"
            echo ""
            echo "=========================================="
            echo "✅ 修复完成！"
            echo "=========================================="
            echo ""
            echo "现在可以重新尝试登录："
            echo "  python3 tools/check_login.py"
            echo ""
            exit 0
        fi
    fi
    echo "   等待中... ($i/10)"
done

echo ""
echo "❌ MCP 服务启动超时"
echo ""
echo "查看日志："
echo "  tail -50 /tmp/mcp.log"
echo ""
exit 1

