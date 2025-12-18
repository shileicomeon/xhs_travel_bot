#!/bin/bash

# 小红书旅游博主自动发布系统 - 安装脚本

set -e

echo "======================================"
echo "小红书旅游博主自动发布系统 - 安装"
echo "======================================"

# 检查Python版本
echo ""
echo "检查Python版本..."
python3 --version || {
    echo "❌ Python 3未安装"
    echo "请先安装: sudo apt install python3 python3-pip"
    exit 1
}

# 检查pip
echo ""
echo "检查pip..."
pip3 --version || {
    echo "❌ pip3未安装"
    echo "请先安装: sudo apt install python3-pip"
    exit 1
}

# 安装依赖
echo ""
echo "安装Python依赖..."
pip3 install -r requirements.txt || {
    echo "⚠️  使用国内镜像重试..."
    pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
}

# 检查配置文件
echo ""
echo "检查配置文件..."
if [ ! -f "config/.env" ]; then
    echo "❌ config/.env 不存在"
    echo "请复制 config/env.example 为 config/.env 并填入API密钥"
    exit 1
fi

# 创建日志目录
echo ""
echo "创建日志目录..."
mkdir -p logs
mkdir -p /tmp/xhs_images

# 测试运行
echo ""
echo "测试运行..."
python3 src/scheduler_v2.py --city 杭州 --force || {
    echo "❌ 测试失败"
    exit 1
}

echo ""
echo "======================================"
echo "✅ 安装完成！"
echo "======================================"
echo ""
echo "下一步："
echo "1. 启动小红书MCP服务（必需）:"
echo "   详见 MCP_SETUP.md"
echo ""
echo "2. 配置Cron定时任务:"
echo "   crontab -e"
echo "   添加: 0 9-11 * * * cd $(pwd) && /usr/bin/python3 src/scheduler_v2.py >> /var/log/xhs_bot_cron.log 2>&1"
echo ""
echo "3. 查看日志:"
echo "   tail -f logs/xhs_bot_$(date +%Y-%m-%d).log"
echo ""
echo "4. 手动测试:"
echo "   python3 src/scheduler_v2.py --city 杭州 --force"
echo ""

