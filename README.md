# 小红书旅游博主自动发布系统

基于小红书 MCP 和 AI 的自动内容生成与发布系统。

## 功能特性

- 🎯 **双模式发布**：80% 旅游攻略模式 + 20% 文字卡片模式
- 🤖 **AI 生成内容**：支持 DeepSeek / Qwen 大模型
- 📸 **自动图片处理**：搜索、下载、去水印、尺寸调整
- 📊 **飞书集成**：自动记录发布结果、失败通知
- ⏰ **智能调度**：随机时间发布，避免被识别为机器人
- 🌍 **多城市支持**：配置化的城市主题库

## 快速开始

### 1. 环境要求

- Python 3.10+
- Node.js 18+（用于 xiaohongshu-mcp）
- 阿里云 Ubuntu 服务器（可选，用于定时任务）

### 2. 本地安装

```bash
# 克隆项目
git clone https://github.com/shileicomeon/xhs_travel_bot.git
cd xhs_travel_bot

# 安装依赖
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 配置环境变量
cp config/env.example config/.env
vim config/.env  # 填入 API 密钥
```

### 3. 配置文件

编辑 `config/.env`：

```bash
# AI 服务（二选一）
DEEPSEEK_API_KEY=sk-your-key
# 或
QWEN_API_KEY=sk-your-key

# 飞书配置
FEISHU_APP_ID=cli_xxxxx
FEISHU_APP_SECRET=xxxxx
FEISHU_WEBHOOK_URL=https://open.feishu.cn/...
FEISHU_TABLE_ID=xxxxx

# 小红书 MCP（本地运行）
XHS_MCP_URL=http://localhost:18060
```

### 4. 启动 xiaohongshu-mcp

```bash
# 在本地 Mac 上
cd ~/xiaohongshu-mcp
go run .

# 浏览器访问 http://localhost:18060 扫码登录
```

### 5. 测试运行

```bash
# 测试模式（不实际发布）
python3 src/scheduler_v2.py --test

# 强制执行（忽略时间窗口）
python3 src/scheduler_v2.py --force

# 指定城市测试
python3 src/scheduler_v2.py --test --city 成都
```

## 服务器部署（Ubuntu）

### 一键部署

```bash
# 在服务器上运行
cd ~/xhs_travel_bot
bash deploy/aliyun_install.sh
```

### 配置定时任务

```bash
crontab -e

# 每天 9-11 点之间随机执行
0 9-11 * * * cd ~/xhs_travel_bot && source venv/bin/activate && python3 src/scheduler_v2.py >> logs/cron.log 2>&1
```

### MCP 服务配置

**重要**：MCP 服务建议在本地 Mac 运行，服务器通过 SSH 隧道或内网穿透访问。

如果必须在服务器运行 MCP（需要 headless 环境）：

```bash
# 启动虚拟显示
Xvfb :99 -screen 0 1920x1080x24 &

# 启动 MCP
cd ~/xiaohongshu-mcp
DISPLAY=:99 go run . -headless=true &

# 或使用 xvfb-run
xvfb-run -a go run . -headless=true &
```

## 工具脚本

### `tools/check_login.py`

检查小红书登录状态，未登录时生成二维码（发送到飞书）。

```bash
python3 tools/check_login.py
```

## 项目结构

```
xhs_travel_bot/
├── config/              # 配置文件
│   ├── .env            # 环境变量（需手动创建）
│   ├── cities.yaml     # 城市主题配置
│   ├── settings.yaml   # 系统设置
│   └── text_topics.yaml # 文字卡片主题
├── src/
│   ├── scheduler_v2.py  # 主调度器
│   ├── services/        # 服务层
│   │   ├── deepseek_client.py
│   │   ├── qwen_client.py
│   │   ├── xhs_mcp_client.py
│   │   ├── feishu_client.py
│   │   └── image_downloader.py
│   ├── steps/           # 流程步骤
│   │   ├── step0_context.py      # 生成上下文
│   │   ├── step1_search_xhs.py   # 搜索小红书
│   │   ├── step2_download_images.py # 下载图片
│   │   ├── step3_generate_guide.py  # 生成文案
│   │   ├── step5_publish.py      # 发布
│   │   ├── step6_logging.py      # 记录
│   │   └── text_card_mode.py     # 文字卡片模式
│   ├── prompts/         # AI 提示词
│   └── utils/           # 工具函数
├── deploy/
│   ├── aliyun_install.sh  # 阿里云一键部署
│   └── crontab.txt        # 定时任务示例
├── tools/
│   └── check_login.py     # 登录检查工具
├── requirements.txt
└── README.md
```

## 常见问题

### 1. MCP 连接失败

- 确认 MCP 服务已启动：`curl http://localhost:18060/health`
- 检查防火墙设置
- 使用 SSH 端口转发：`ssh -L 18060:localhost:18060 user@server`

### 2. Ubuntu headless 环境登录

MCP 在无显示器环境下获取二维码不稳定，推荐方案：

1. 在本地 Mac 登录后，复制 cookies 到服务器
2. 或使用 SSH 端口转发，浏览器访问本地 18060 端口

### 3. 图片下载失败

- 检查网络连接
- 确认小红书图片 URL 有效
- 图片处理需要 `libjpeg-dev` `zlib1g-dev` 等依赖

### 4. AI 生成失败

- 检查 API 密钥是否正确
- 确认 API 额度充足
- 查看日志：`tail -f logs/xhs_bot_$(date +%Y-%m-%d).log`

## License

MIT

## 作者

[@shileicomeon](https://github.com/shileicomeon)
