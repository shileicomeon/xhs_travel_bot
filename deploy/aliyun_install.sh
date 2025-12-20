#!/bin/bash
#
# 阿里云Ubuntu一键部署脚本
# 适用于：Ubuntu 20.04/22.04
# 用途：小红书旅游博主自动发布系统
#

set -e  # 遇到错误立即退出

echo "=========================================="
echo "🚀 小红书自动发布系统 - 阿里云部署"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置变量
# 如果环境变量中指定了INSTALL_DIR，则使用指定的目录，否则使用默认的/opt/xhs_travel_bot
INSTALL_DIR="${INSTALL_DIR:-/opt/xhs_travel_bot}"
CURRENT_USER=$(whoami)

echo -e "${GREEN}📋 部署配置${NC}"
echo "安装目录: $INSTALL_DIR"
echo "当前用户: $CURRENT_USER"
echo ""

# 步骤1：配置阿里云镜像源
echo -e "${GREEN}[1/10] 配置阿里云镜像源...${NC}"

# 备份原有sources.list
sudo cp /etc/apt/sources.list /etc/apt/sources.list.backup.$(date +%Y%m%d) 2>/dev/null || true

# 检测Ubuntu版本
UBUNTU_VERSION=$(lsb_release -cs)
echo "检测到Ubuntu版本: $UBUNTU_VERSION"

# 写入阿里云镜像源
sudo tee /etc/apt/sources.list > /dev/null <<EOF
# 阿里云Ubuntu镜像源
deb http://mirrors.aliyun.com/ubuntu/ $UBUNTU_VERSION main restricted universe multiverse
deb http://mirrors.aliyun.com/ubuntu/ $UBUNTU_VERSION-security main restricted universe multiverse
deb http://mirrors.aliyun.com/ubuntu/ $UBUNTU_VERSION-updates main restricted universe multiverse
deb http://mirrors.aliyun.com/ubuntu/ $UBUNTU_VERSION-backports main restricted universe multiverse

# deb-src http://mirrors.aliyun.com/ubuntu/ $UBUNTU_VERSION main restricted universe multiverse
# deb-src http://mirrors.aliyun.com/ubuntu/ $UBUNTU_VERSION-security main restricted universe multiverse
# deb-src http://mirrors.aliyun.com/ubuntu/ $UBUNTU_VERSION-updates main restricted universe multiverse
# deb-src http://mirrors.aliyun.com/ubuntu/ $UBUNTU_VERSION-backports main restricted universe multiverse
EOF

echo "✅ 阿里云镜像源配置完成"

# 步骤2：更新系统
echo -e "${GREEN}[2/10] 更新系统包...${NC}"
sudo apt update
echo "✅ 系统包列表更新完成"

# 步骤3：安装Python和依赖
echo -e "${GREEN}[3/10] 安装Python和系统依赖...${NC}"

# 根据Ubuntu版本选择不同的包
UBUNTU_VERSION_NUM=$(lsb_release -rs | cut -d. -f1)

if [ "$UBUNTU_VERSION_NUM" -ge 24 ]; then
    # Ubuntu 24.04+ 使用新的包名
    echo "检测到 Ubuntu 24.04+，使用新包名..."
    sudo apt install -y \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        libjpeg-dev \
        zlib1g-dev \
        libtiff-dev \
        libfreetype-dev \
        fonts-wqy-microhei \
        fonts-wqy-zenhei \
        git \
        curl \
        wget \
        screen \
        xvfb \
        libgbm1 \
        libasound2t64
else
    # Ubuntu 20.04/22.04 使用旧的包名
    echo "检测到 Ubuntu 20.04/22.04，使用旧包名..."
    sudo apt install -y \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        libjpeg-dev \
        zlib1g-dev \
        libtiff-dev \
        libfreetype6-dev \
        fonts-wqy-microhei \
        fonts-wqy-zenhei \
        git \
        curl \
        wget \
        screen \
        xvfb \
        libgbm1 \
        libasound2
fi

echo "✅ 系统依赖安装完成"

# 验证Python版本
PYTHON_VERSION=$(python3 --version)
echo "Python版本: $PYTHON_VERSION"

# 步骤4：安装Node.js（使用阿里云镜像）
echo -e "${GREEN}[4/10] 安装Node.js...${NC}"

if ! command -v node &> /dev/null; then
    echo "从阿里云镜像安装Node.js 18..."
    curl -fsSL https://mirrors.aliyun.com/nodesource/setup_18.x | sudo -E bash -
    sudo apt install -y nodejs
else
    echo "Node.js已安装，跳过"
fi

NODE_VERSION=$(node --version)
NPM_VERSION=$(npm --version)
echo "Node.js版本: $NODE_VERSION"
echo "NPM版本: $NPM_VERSION"

# 配置npm使用阿里云镜像
echo "配置npm阿里云镜像..."
npm config set registry https://registry.npmmirror.com
echo "✅ Node.js安装完成"

# 步骤5：准备安装目录
echo -e "${GREEN}[5/10] 准备安装目录...${NC}"

# 检查是否在项目目录中运行
if [ -f "src/scheduler_v2.py" ] && [ -f "requirements.txt" ]; then
    echo "✅ 检测到在项目目录中运行"
    INSTALL_DIR=$(pwd)
    echo "使用当前目录: $INSTALL_DIR"
else
    # 不在项目目录中，使用指定的INSTALL_DIR
    if [ ! -d "$INSTALL_DIR" ]; then
        sudo mkdir -p "$INSTALL_DIR"
        sudo chown $CURRENT_USER:$CURRENT_USER "$INSTALL_DIR"
        echo "✅ 目录创建完成: $INSTALL_DIR"
    else
        echo "⚠️  目录已存在，将使用现有目录"
    fi
    cd "$INSTALL_DIR"
fi

# 步骤6：检查项目代码
echo -e "${GREEN}[6/10] 检查项目代码...${NC}"
echo "当前工作目录: $(pwd)"
echo "检查文件: src/scheduler_v2.py $([ -f "src/scheduler_v2.py" ] && echo "✅" || echo "❌")"
echo "检查文件: requirements.txt $([ -f "requirements.txt" ] && echo "✅" || echo "❌")"

if [ -f "src/scheduler_v2.py" ] && [ -f "requirements.txt" ]; then
    echo "✅ 项目代码已就绪，跳过克隆步骤"
else
    echo -e "${RED}❌ 未找到项目代码！${NC}"
    echo ""
    echo "目录内容："
    ls -la
    echo ""
    echo "建议操作："
    echo "1. 确保在项目根目录运行: cd ~/sal/xhs_travel_bot && bash deploy/aliyun_install.sh"
    echo "2. 或先克隆代码: git clone https://github.com/shileicomeon/xhs_travel_bot.git"
    exit 1
fi

# 步骤7：创建Python虚拟环境
echo -e "${GREEN}[7/10] 创建Python虚拟环境...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ 虚拟环境创建完成"
else
    echo "⚠️  虚拟环境已存在，跳过创建"
fi

# 激活虚拟环境
source venv/bin/activate

# 配置pip使用阿里云镜像
echo "配置pip阿里云镜像..."
pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/
pip config set install.trusted-host mirrors.aliyun.com

# 步骤8：安装Python依赖
echo -e "${GREEN}[8/10] 安装Python依赖包...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Python依赖安装完成"

# 步骤9：创建必要的目录
echo -e "${GREEN}[9/10] 创建必要的目录...${NC}"
mkdir -p logs
mkdir -p temp_images
mkdir -p data

echo "✅ 目录结构创建完成"

# 配置环境变量
echo ""
echo -e "${YELLOW}=========================================="
echo "⚙️  配置环境变量"
echo "==========================================${NC}"

if [ ! -f "config/.env" ]; then
    if [ -f "config/env.example" ]; then
        cp config/env.example config/.env
        echo "✅ 已创建 config/.env 配置文件"
    else
        echo "⚠️  未找到 config/env.example，请手动创建 config/.env"
    fi
    
    echo ""
    echo -e "${YELLOW}请编辑 config/.env 文件，填入以下配置：${NC}"
    echo ""
    echo "1. AI服务配置（二选一）："
    echo "   DEEPSEEK_API_KEY=sk-your-key"
    echo "   或 QWEN_API_KEY=sk-your-key"
    echo ""
    echo "2. 飞书配置："
    echo "   FEISHU_APP_ID=cli_xxxxx"
    echo "   FEISHU_APP_SECRET=xxxxx"
    echo "   FEISHU_WEBHOOK_URL=https://..."
    echo "   FEISHU_TABLE_ID=xxxxx"
    echo ""
    echo "编辑命令: vim $INSTALL_DIR/config/.env"
    echo ""
else
    echo "✅ config/.env 已存在"
fi

# 设置文件权限
chmod 600 config/.env 2>/dev/null || true
chmod 700 logs 2>/dev/null || true

# 创建快捷脚本
echo ""
echo -e "${GREEN}创建快捷管理脚本...${NC}"

# 测试脚本
cat > "$INSTALL_DIR/test_publish.sh" <<'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python3 src/scheduler_v2.py --force
EOF
chmod +x "$INSTALL_DIR/test_publish.sh"

echo "✅ 快捷脚本创建完成"

# 完成
echo ""
echo -e "${GREEN}=========================================="
echo "🎉 部署完成！"
echo "==========================================${NC}"
echo ""
echo -e "${YELLOW}📋 后续步骤：${NC}"
echo ""
echo "1️⃣  配置环境变量："
echo "   vim $INSTALL_DIR/config/.env"
echo "   需要配置: AI API密钥、飞书配置等"
echo ""
echo "2️⃣  测试发布（确保本地MCP服务已启动）："
echo "   $INSTALL_DIR/test_publish.sh"
echo ""
echo "3️⃣  配置定时任务："
echo "   crontab -e"
echo "   添加: 0 9-11 * * * $INSTALL_DIR/venv/bin/python3 $INSTALL_DIR/src/scheduler_v2.py >> $INSTALL_DIR/logs/cron.log 2>&1"
echo ""
echo -e "${YELLOW}⚠️  重要提示：${NC}"
echo "   MCP服务需要在本地（Mac）运行，不在服务器上"
echo "   服务器只负责运行定时任务和发布逻辑"
echo ""
echo -e "${GREEN}=========================================="
echo "📚 文档位置：${NC}"
echo "   - 项目说明: $INSTALL_DIR/README.md"
echo "   - 配置参考: $INSTALL_DIR/config/settings.yaml"
echo ""
echo -e "${GREEN}🔧 常用命令：${NC}"
echo "   启动MCP: sudo systemctl start xhs-mcp"
echo "   查看状态: sudo systemctl status xhs-mcp"
echo "   查看日志: tail -f $INSTALL_DIR/logs/xhs_bot_\$(date +%Y-%m-%d).log"
echo "   手动发布: cd $INSTALL_DIR && source venv/bin/activate && python3 src/scheduler_v2.py --force"
echo ""
echo -e "${GREEN}部署成功！✨${NC}"

