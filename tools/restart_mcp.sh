#!/bin/bash

# 重启小红书MCP服务脚本

echo "=========================================="
echo "🔄 重启小红书MCP服务"
echo "=========================================="
echo ""

# 1. 停止现有服务
echo "1️⃣ 停止现有MCP服务..."
pkill -9 -f "xiaohongshu-mcp"
sleep 2

# 检查是否还有进程
MCP_PID=$(ps aux | grep "xiaohongshu-mcp" | grep -v grep | awk '{print $2}')
if [ -n "$MCP_PID" ]; then
    echo "⚠️  强制终止进程: $MCP_PID"
    kill -9 $MCP_PID 2>/dev/null
    sleep 1
fi

echo "✅ 已停止旧服务"
echo ""

# 2. 检查MCP目录
echo "2️⃣ 检查MCP安装..."
MCP_DIR="$HOME/xiaohongshu-mcp"

if [ ! -d "$MCP_DIR" ]; then
    echo "❌ MCP目录不存在: $MCP_DIR"
    echo ""
    echo "请确认MCP服务的安装位置，或修改本脚本中的 MCP_DIR 变量"
    exit 1
fi

cd "$MCP_DIR" || exit 1
echo "✅ MCP目录: $MCP_DIR"
echo ""

# 3. 检查依赖
echo "3️⃣ 检查依赖..."

if ! command -v go &> /dev/null; then
    echo "❌ Go未安装"
    exit 1
fi
echo "✅ Go已安装: $(go version)"

if ! command -v Xvfb &> /dev/null; then
    echo "⚠️  xvfb未安装，使用普通模式启动"
    USE_XVFB=false
else
    echo "✅ xvfb已安装"
    USE_XVFB=true
fi
echo ""

# 4. 启动服务
echo "4️⃣ 启动MCP服务..."

# 清理旧的日志文件
rm -f /tmp/mcp.log /tmp/mcp_error.log

if [ "$USE_XVFB" = true ]; then
    echo "使用xvfb启动（headless模式）..."
    nohup xvfb-run -a go run . -headless=true > /tmp/mcp.log 2>&1 &
else
    echo "使用普通模式启动..."
    nohup go run . -headless=true > /tmp/mcp.log 2>&1 &
fi

MCP_NEW_PID=$!
echo "✅ MCP服务已启动 (PID: $MCP_NEW_PID)"
echo ""

# 5. 等待服务启动
echo "5️⃣ 等待服务就绪..."
for i in {1..10}; do
    sleep 1
    
    # 检查进程是否还在运行
    if ! ps -p $MCP_NEW_PID > /dev/null 2>&1; then
        echo "❌ MCP服务启动失败！"
        echo ""
        echo "查看错误日志:"
        echo "  tail -20 /tmp/mcp.log"
        exit 1
    fi
    
    # 检查端口是否开始监听
    PORT_CHECK=$(netstat -tlnp 2>/dev/null | grep ":18060" || ss -tlnp 2>/dev/null | grep ":18060")
    if [ -n "$PORT_CHECK" ]; then
        echo "✅ 端口18060已就绪"
        break
    fi
    
    echo "   等待中... ($i/10)"
done

echo ""

# 6. 测试连接
echo "6️⃣ 测试MCP服务..."
HTTP_TEST=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:18060/mcp 2>/dev/null || echo "failed")

if [ "$HTTP_TEST" = "200" ]; then
    echo "✅ MCP服务HTTP接口正常"
elif [ "$HTTP_TEST" = "failed" ]; then
    echo "⚠️  无法测试HTTP连接（curl可能未安装）"
else
    echo "⚠️  MCP服务响应码: $HTTP_TEST"
fi

echo ""
echo "=========================================="
echo "✅ MCP服务重启完成"
echo "=========================================="
echo ""
echo "查看日志:"
echo "  tail -f /tmp/mcp.log"
echo ""
echo "检查服务状态:"
echo "  ps aux | grep xiaohongshu-mcp | grep -v grep"
echo ""
echo "停止服务:"
echo "  pkill -f xiaohongshu-mcp"
echo ""

