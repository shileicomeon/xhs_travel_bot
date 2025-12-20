#!/bin/bash

# 小红书自动发布系统 - 启动脚本
# 用途：每天自动在 8:00-10:00 之间随机时间发布一条内容

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 获取脚本所在目录（项目根目录）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}🚀 小红书自动发布系统${NC}"
echo -e "${GREEN}======================================${NC}"

# 1. 检查虚拟环境
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ 虚拟环境不存在！${NC}"
    echo "请先运行: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# 2. 激活虚拟环境
echo -e "${YELLOW}📦 激活虚拟环境...${NC}"
source venv/bin/activate

# 3. 检查 Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 未找到！${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python 版本: $(python3 --version)${NC}"

# 4. 检查 MCP 服务
echo -e "${YELLOW}🔍 检查 MCP 服务...${NC}"
if curl -s http://localhost:18060/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ MCP 服务运行正常${NC}"
else
    echo -e "${RED}⚠️  MCP 服务未运行！${NC}"
    echo "请先启动 MCP 服务："
    echo "  cd xiaohongshu-mcp-main"
    echo "  nohup go run . server --addr 0.0.0.0:18060 --headless=true --bin /usr/bin/google-chrome-stable > mcp.log 2>&1 &"
fi

# 5. 运行调度器
echo -e "${YELLOW}🎯 启动调度器...${NC}"
echo ""

# 检查是否传入参数
if [ "$1" == "--test" ]; then
    echo -e "${YELLOW}🧪 测试模式（不实际发布）${NC}"
    python3 src/scheduler_v2.py --test
elif [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
    echo "用法："
    echo "  ./start_scheduler.sh           # 正常模式（直接发布）"
    echo "  ./start_scheduler.sh --test    # 测试模式（不实际发布）"
    echo ""
    echo "定时任务设置（每天 8:00 触发，随机等待 0-120 分钟后发布）："
    echo "  Cron 表达式: 0 0 8 * * ?"
    echo "  命令内容: sleep \$((RANDOM % 7200)) && cd /root/sal/xhs_travel_bot && ./start_scheduler.sh >> logs/cron.log 2>&1"
    exit 0
else
    echo -e "${GREEN}🚀 正常模式（直接发布）${NC}"
    python3 src/scheduler_v2.py
fi

# 6. 检查执行结果
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}======================================${NC}"
    echo -e "${GREEN}✅ 执行完成${NC}"
    echo -e "${GREEN}======================================${NC}"
else
    echo ""
    echo -e "${RED}======================================${NC}"
    echo -e "${RED}❌ 执行失败，请查看日志${NC}"
    echo -e "${RED}======================================${NC}"
    exit 1
fi

