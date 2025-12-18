#!/bin/bash
# 诊断 Ubuntu headless 环境问题

echo "=============================================="
echo "🔍 诊断 Headless 浏览器环境"
echo "=============================================="
echo ""

# 1. 检查 Xvfb
echo "📍 1. 检查 Xvfb..."
if command -v Xvfb &> /dev/null; then
    echo "   ✅ Xvfb 已安装"
    Xvfb -version 2>&1 | head -1
else
    echo "   ❌ Xvfb 未安装"
fi

# 2. 检查 DISPLAY 环境变量
echo ""
echo "📍 2. 检查 DISPLAY 环境变量..."
if [ -z "$DISPLAY" ]; then
    echo "   ⚠️  DISPLAY 未设置"
else
    echo "   ✅ DISPLAY = $DISPLAY"
fi

# 3. 检查 X11 相关进程
echo ""
echo "📍 3. 检查 X11 进程..."
if ps aux | grep -v grep | grep -q "Xvfb"; then
    echo "   ✅ Xvfb 进程运行中:"
    ps aux | grep -v grep | grep "Xvfb" | head -3
else
    echo "   ⚠️  没有 Xvfb 进程"
fi

# 4. 检查浏览器依赖
echo ""
echo "📍 4. 检查浏览器依赖..."
MISSING=""

for pkg in libgbm1 libasound2 libatk-bridge2.0-0 libgtk-3-0 libnss3 libxss1 libx11-xcb1; do
    if dpkg -l | grep -q "^ii  $pkg"; then
        echo "   ✅ $pkg"
    else
        echo "   ❌ $pkg (缺失)"
        MISSING="$MISSING $pkg"
    fi
done

if [ -n "$MISSING" ]; then
    echo ""
    echo "   💡 修复命令:"
    echo "   sudo apt install -y$MISSING"
fi

# 5. 检查 MCP 进程
echo ""
echo "📍 5. 检查 MCP 进程..."
if ps aux | grep -v grep | grep -q "xiaohongshu-mcp"; then
    echo "   ✅ MCP 进程运行中:"
    ps aux | grep -v grep | grep "xiaohongshu-mcp" | head -3
    
    # 检查 MCP 的环境变量
    MCP_PID=$(ps aux | grep -v grep | grep "xiaohongshu-mcp" | awk '{print $2}' | head -1)
    if [ -n "$MCP_PID" ]; then
        echo ""
        echo "   MCP 环境变量:"
        cat /proc/$MCP_PID/environ 2>/dev/null | tr '\0' '\n' | grep -E "DISPLAY|XAUTHORITY" || echo "   (无相关环境变量)"
    fi
else
    echo "   ⚠️  MCP 未运行"
fi

# 6. 检查端口
echo ""
echo "📍 6. 检查端口 18060..."
if netstat -tulnp 2>/dev/null | grep -q ":18060"; then
    echo "   ✅ 端口 18060 已监听"
    netstat -tulnp 2>/dev/null | grep ":18060"
else
    echo "   ❌ 端口 18060 未监听"
fi

# 7. 测试 MCP 连接
echo ""
echo "📍 7. 测试 MCP HTTP 连接..."
if curl -s -m 5 http://localhost:18060/health > /dev/null 2>&1; then
    echo "   ✅ MCP HTTP 可访问"
elif curl -s -m 5 http://localhost:18060 > /dev/null 2>&1; then
    echo "   ✅ MCP HTTP 可访问"
else
    echo "   ❌ MCP HTTP 不可访问"
fi

# 8. 检查 MCP 日志
echo ""
echo "📍 8. MCP 最新日志 (最后 10 行)..."
if [ -f "/tmp/mcp.log" ]; then
    echo "   --- /tmp/mcp.log ---"
    tail -10 /tmp/mcp.log 2>/dev/null
else
    echo "   ⚠️  日志文件不存在"
fi

# 9. 测试 xvfb-run
echo ""
echo "📍 9. 测试 xvfb-run..."
if xvfb-run -a echo "test" > /dev/null 2>&1; then
    echo "   ✅ xvfb-run 工作正常"
else
    echo "   ❌ xvfb-run 不工作"
fi

# 10. 生成修复建议
echo ""
echo "=============================================="
echo "🔧 修复建议"
echo "=============================================="

if [ -z "$DISPLAY" ]; then
    echo ""
    echo "⚠️  问题: DISPLAY 未设置"
    echo "   解决方案:"
    echo "   1. 手动启动 Xvfb:"
    echo "      Xvfb :99 -screen 0 1920x1080x24 > /dev/null 2>&1 &"
    echo "      export DISPLAY=:99"
    echo ""
    echo "   2. 或使用 xvfb-run 启动 MCP:"
    echo "      pkill -f xiaohongshu-mcp"
    echo "      cd ~/xiaohongshu-mcp"
    echo "      xvfb-run -a --server-args='-screen 0 1920x1080x24' go run . -headless=true > /tmp/mcp.log 2>&1 &"
fi

if [ -n "$MISSING" ]; then
    echo ""
    echo "⚠️  问题: 缺少浏览器依赖"
    echo "   解决方案:"
    echo "   sudo apt install -y$MISSING"
fi

if ! ps aux | grep -v grep | grep -q "Xvfb"; then
    echo ""
    echo "⚠️  问题: Xvfb 未运行"
    echo "   解决方案: 运行上面的 xvfb-run 命令"
fi

echo ""
echo "=============================================="
echo "完成诊断"
echo "=============================================="

