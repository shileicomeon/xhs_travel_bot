#!/bin/bash

# 一键修复MCP服务

echo "=========================================="
echo "🔧 MCP服务快速修复"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# MCP目录（根据实际情况修改）
if [ -d "$HOME/xiaohongshu-mcp" ]; then
    MCP_DIR="$HOME/xiaohongshu-mcp"
elif [ -d "/opt/xiaohongshu-mcp" ]; then
    MCP_DIR="/opt/xiaohongshu-mcp"
else
    echo -e "${RED}❌ 未找到MCP目录${NC}"
    echo "请手动指定MCP安装目录："
    echo "  export MCP_DIR=/path/to/xiaohongshu-mcp"
    echo "  bash tools/fix_mcp.sh"
    exit 1
fi

echo -e "${GREEN}✅ MCP目录: $MCP_DIR${NC}"
echo ""

# 1. 强制停止所有MCP进程
echo "1️⃣ 停止MCP进程..."
pkill -9 -f "xiaohongshu-mcp" 2>/dev/null
pkill -9 -f "go run.*headless" 2>/dev/null
sleep 2
echo -e "${GREEN}✅ 已停止${NC}"
echo ""

# 2. 清理端口（如果有残留）
echo "2️⃣ 检查端口18060..."
PORT_PID=$(lsof -ti:18060 2>/dev/null || fuser 18060/tcp 2>/dev/null | awk '{print $1}')
if [ -n "$PORT_PID" ]; then
    echo -e "${YELLOW}⚠️  端口18060被进程占用: $PORT_PID${NC}"
    kill -9 $PORT_PID 2>/dev/null
    sleep 1
    echo -e "${GREEN}✅ 已释放端口${NC}"
else
    echo -e "${GREEN}✅ 端口空闲${NC}"
fi
echo ""

# 3. 清理cookies（可选）
echo "3️⃣ 清理旧的cookies..."
if [ -f "$MCP_DIR/cookies.json" ]; then
    rm -f "$MCP_DIR/cookies.json"
    echo -e "${GREEN}✅ 已删除 $MCP_DIR/cookies.json${NC}"
else
    echo -e "${YELLOW}⚠️  未找到cookies文件${NC}"
fi
echo ""

# 4. 检查依赖
echo "4️⃣ 检查依赖..."
if ! command -v go &> /dev/null; then
    echo -e "${RED}❌ Go未安装${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Go: $(go version | awk '{print $3}')${NC}"

if command -v Xvfb &> /dev/null; then
    USE_XVFB=true
    echo -e "${GREEN}✅ xvfb已安装${NC}"
else
    USE_XVFB=false
    echo -e "${YELLOW}⚠️  xvfb未安装（建议安装）${NC}"
    echo "   安装命令: sudo apt install xvfb -y"
fi
echo ""

# 5. 启动MCP服务
echo "5️⃣ 启动MCP服务..."
cd "$MCP_DIR" || exit 1

# 清理旧日志
rm -f /tmp/mcp.log

# 根据是否有xvfb选择启动方式
if [ "$USE_XVFB" = true ]; then
    echo "使用xvfb启动（推荐）..."
    nohup xvfb-run -a go run . -headless=true > /tmp/mcp.log 2>&1 &
else
    echo "使用普通模式启动..."
    nohup go run . -headless=true > /tmp/mcp.log 2>&1 &
fi

MCP_PID=$!
echo -e "${GREEN}✅ MCP服务已启动 (PID: $MCP_PID)${NC}"
echo ""

# 6. 等待服务就绪
echo "6️⃣ 等待服务就绪..."
SUCCESS=false

for i in {1..15}; do
    sleep 2
    
    # 检查进程
    if ! ps -p $MCP_PID > /dev/null 2>&1; then
        echo -e "${RED}❌ MCP进程已退出！${NC}"
        echo ""
        echo "查看错误日志："
        tail -30 /tmp/mcp.log
        exit 1
    fi
    
    # 检查端口
    if netstat -tln 2>/dev/null | grep -q ":18060" || ss -tln 2>/dev/null | grep -q ":18060"; then
        # 尝试HTTP请求
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:18060/mcp 2>/dev/null || echo "000")
        
        if [ "$HTTP_CODE" = "200" ]; then
            echo -e "${GREEN}✅ MCP服务已就绪！${NC}"
            SUCCESS=true
            break
        elif [ "$HTTP_CODE" = "000" ]; then
            echo "   等待中... ($i/15) - 服务启动中"
        else
            echo "   等待中... ($i/15) - HTTP $HTTP_CODE"
        fi
    else
        echo "   等待中... ($i/15) - 等待端口开启"
    fi
done

echo ""

if [ "$SUCCESS" = true ]; then
    echo "=========================================="
    echo -e "${GREEN}✅ MCP服务修复成功！${NC}"
    echo "=========================================="
    echo ""
    echo "现在可以进行登录了："
    echo "  cd ~/sal/xhs_travel_bot"
    echo "  source venv/bin/activate"
    echo "  python3 tools/check_login.py"
else
    echo "=========================================="
    echo -e "${RED}❌ MCP服务启动失败${NC}"
    echo "=========================================="
    echo ""
    echo "请检查日志："
    echo "  tail -50 /tmp/mcp.log"
    echo ""
    echo "常见问题："
    echo "  1. Go版本过低（需要1.19+）"
    echo "  2. 缺少依赖包（在MCP目录运行: go mod tidy）"
    echo "  3. 端口冲突（检查: netstat -tlnp | grep 18060）"
    exit 1
fi

echo ""
echo "📋 有用的命令："
echo "  查看日志: tail -f /tmp/mcp.log"
echo "  查看进程: ps aux | grep xiaohongshu-mcp"
echo "  停止服务: pkill -f xiaohongshu-mcp"
echo ""

