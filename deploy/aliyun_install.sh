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
INSTALL_DIR="/opt/xhs_travel_bot"
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
    screen

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

# 步骤5：创建安装目录
echo -e "${GREEN}[5/10] 创建安装目录...${NC}"
if [ ! -d "$INSTALL_DIR" ]; then
    sudo mkdir -p "$INSTALL_DIR"
    sudo chown $CURRENT_USER:$CURRENT_USER "$INSTALL_DIR"
    echo "✅ 目录创建完成: $INSTALL_DIR"
else
    echo "⚠️  目录已存在，将使用现有目录"
fi

cd "$INSTALL_DIR"

# 步骤6：检查代码
echo -e "${GREEN}[6/10] 检查项目代码...${NC}"
if [ ! -f "src/scheduler_v2.py" ]; then
    echo -e "${RED}❌ 未找到项目代码！${NC}"
    echo "请先将代码上传到 $INSTALL_DIR"
    echo ""
    echo "上传方式："
    echo "1. 使用Git: git clone <your-repo> $INSTALL_DIR"
    echo "2. 使用SCP: scp -r /local/path/* $CURRENT_USER@server:$INSTALL_DIR/"
    echo "3. 使用SFTP或其他工具上传"
    exit 1
else
    echo "✅ 项目代码已就绪"
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

# 步骤9：安装小红书MCP工具
echo -e "${GREEN}[9/10] 安装小红书MCP工具...${NC}"
npm install -g @modelcontextprotocol/server-xiaohongshu

echo "✅ MCP工具安装完成"

# 步骤10：创建必要的目录
echo -e "${GREEN}[10/10] 创建必要的目录...${NC}"
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

# 创建systemd服务
echo ""
echo -e "${YELLOW}=========================================="
echo "🔧 创建MCP服务"
echo "==========================================${NC}"

sudo tee /etc/systemd/system/xhs-mcp.service > /dev/null <<EOF
[Unit]
Description=Xiaohongshu MCP Service
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/npx @modelcontextprotocol/server-xiaohongshu
Restart=always
RestartSec=10
Environment="NODE_ENV=production"

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable xhs-mcp

echo "✅ MCP服务已创建"
echo ""
echo "启动MCP服务: sudo systemctl start xhs-mcp"
echo "查看状态: sudo systemctl status xhs-mcp"
echo "查看日志: sudo journalctl -u xhs-mcp -f"

# 创建快捷脚本
echo ""
echo -e "${GREEN}创建快捷管理脚本...${NC}"

# 启动脚本
cat > "$INSTALL_DIR/start_mcp.sh" <<'EOF'
#!/bin/bash
sudo systemctl start xhs-mcp
echo "✅ MCP服务已启动"
sudo systemctl status xhs-mcp
EOF
chmod +x "$INSTALL_DIR/start_mcp.sh"

# 测试脚本
cat > "$INSTALL_DIR/test_publish.sh" <<'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python3 src/scheduler_v2.py --force
EOF
chmod +x "$INSTALL_DIR/test_publish.sh"

# 登录脚本
cat > "$INSTALL_DIR/login_xhs.sh" <<'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python3 tools/login_helper.py
EOF
chmod +x "$INSTALL_DIR/login_xhs.sh"

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
echo ""
echo "2️⃣  启动MCP服务："
echo "   $INSTALL_DIR/start_mcp.sh"
echo "   或: sudo systemctl start xhs-mcp"
echo ""
echo "3️⃣  登录小红书账号："
echo "   $INSTALL_DIR/login_xhs.sh"
echo "   然后下载二维码: scp $CURRENT_USER@server:$INSTALL_DIR/login_qrcode.png ."
echo ""
echo "4️⃣  测试发布："
echo "   $INSTALL_DIR/test_publish.sh"
echo ""
echo "5️⃣  配置定时任务："
echo "   crontab -e"
echo "   添加: 0 9-11 * * * $INSTALL_DIR/venv/bin/python3 $INSTALL_DIR/src/scheduler_v2.py >> /var/log/xhs_bot.log 2>&1"
echo ""
echo -e "${GREEN}=========================================="
echo "📚 文档位置：${NC}"
echo "   - Ubuntu部署: $INSTALL_DIR/deploy/UBUNTU_DEPLOY.md"
echo "   - MCP配置: $INSTALL_DIR/MCP_SETUP.md"
echo "   - 项目说明: $INSTALL_DIR/README.md"
echo ""
echo -e "${GREEN}🔧 常用命令：${NC}"
echo "   启动MCP: sudo systemctl start xhs-mcp"
echo "   查看状态: sudo systemctl status xhs-mcp"
echo "   查看日志: tail -f $INSTALL_DIR/logs/xhs_bot_\$(date +%Y-%m-%d).log"
echo "   手动发布: cd $INSTALL_DIR && source venv/bin/activate && python3 src/scheduler_v2.py --force"
echo ""
echo -e "${GREEN}部署成功！✨${NC}"

