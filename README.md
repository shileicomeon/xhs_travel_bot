# 小红书旅游博主自动发布系统 V2

一个基于 Python 的无状态自动化系统，每天在 9:00-11:00 随机时间自动发布小红书旅游内容。

**V2 版本**：直接从小红书搜索真实内容，提取图片和灵感，生成攻略风格文案，确保内容质量和图片相关性。

## 功能特点

- ✅ **完全自动化** - 无需人工介入，定时自动发布
- ✅ **真实内容源** - 从小红书搜索真实帖子，提取高质量图片
- ✅ **智能内容生成** - AI 生成攻略风格文案，包含步骤和图标
- ✅ **图片质量保证** - 使用真实小红书图片，相关性 100%
- ✅ **防重复发布** - 城市加权选择，避免短期重复
- ✅ **内容合规检查** - 敏感词过滤，符合平台规范
- ✅ **飞书通知** - 发布结果实时通知，表格自动记录
- ✅ **跨平台支持** - 支持 macOS、Ubuntu、CentOS

## 技术架构（V2）

```
Cron定时 → 调度器 → 生成上下文 → 搜索小红书 → 下载图片 → AI生成攻略 → 组装 → MCP发布 → 飞书记录
```

## 核心依赖

- **Python 3.8+**
- **小红书 MCP 服务**（必需，用于搜索和发布）
- **DeepSeek/Qwen AI**（用于内容生成）
- **飞书开放平台**（用于通知和记录）
- **飞书 SDK (lark-oapi)**（用于表格操作）

## 快速开始

### 1. 创建虚拟环境并安装依赖

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 配置文件已创建在 config/.env
# 请确认以下密钥是否有效：
# - DEEPSEEK_API_KEY
# - FEISHU_APP_ID / FEISHU_APP_SECRET
# - 小红书MCP工具配置
```

### 3. 启动小红书 MCP 服务

V2 版本必须先启动 MCP 服务并登录才能运行。

```bash
# 1. 启动MCP服务
npx @modelcontextprotocol/server-xiaohongshu

# 2. 登录小红书账号

# 有显示器：访问 http://localhost:18060 扫码登录

# 无显示器（Ubuntu服务器）：使用登录辅助工具
python tools/login_helper.py
# 工具会生成二维码，下载到本地后用小红书App扫描

# 详细步骤请参考 MCP_SETUP.md
```

### 4. 测试运行

```bash
# 测试指定城市（强制执行，不检查时间窗口）
python src/scheduler_v2.py --city 杭州 --force

# 测试随机城市
python src/scheduler_v2.py --force

# 查看日志
tail -f logs/xhs_bot_$(date +%Y-%m-%d).log
```

### 5. 正式运行

```bash
# 手动运行一次（会检查时间窗口）
python src/scheduler_v2.py

# 或配置Cron定时任务（推荐）
crontab -e
# 添加: 0 9-11 * * * cd /path/to/xhs_travel_bot && /path/to/venv/bin/python src/scheduler_v2.py >> /var/log/xhs_bot.log 2>&1
```

## V2 测试结果

✅ **V2 系统已完成并真实运行成功！**

```
✅ Step 0: 生成上下文 - 成功
✅ Step 1: 搜索小红书内容 - 成功（获取真实图片）
✅ Step 2: 下载并处理图片 - 成功（6张）
✅ Step 3: AI生成攻略内容 - 成功
✅ Step 4: 组装发布数据 - 成功
✅ Step 5: MCP发布到小红书 - 成功（真实发布）
✅ Step 6: 飞书记录 - 成功（通知已发送）

总耗时: 101.8秒
```

## 已知问题

1. **飞书表格权限** - 需要在飞书后台开通以下权限：
   - `bitable:app:readonly`
   - `bitable:app`
   - `base:table:read`

详见 [V2_PURE_ONLY.md](V2_PURE_ONLY.md) 和 [FINAL_SUMMARY.md](FINAL_SUMMARY.md)

## 项目结构（V2）

```
xhs_travel_bot/
├── config/              # 配置文件
│   ├── cities.yaml      # 城市配置
│   ├── settings.yaml    # 系统配置
│   ├── text_topics.yaml # 文字卡片话题库
│   └── .env            # API密钥（不提交）
├── src/
│   ├── scheduler_v2.py  # V2主调度器（双模式）
│   ├── steps/          # 核心流程
│   │   ├── step0_context.py        # 上下文生成
│   │   ├── step1_search_xhs.py     # 搜索小红书
│   │   ├── step2_download_images.py # 下载图片
│   │   ├── step3_generate_guide.py  # 生成攻略
│   │   ├── step4_assembly.py       # 组装数据
│   │   ├── step5_publish.py        # MCP发布
│   │   ├── step6_logging.py        # 飞书记录
│   │   └── text_card_mode.py       # 文字卡片模式
│   ├── services/       # 服务层
│   │   ├── xhs_mcp_client.py       # 小红书MCP客户端
│   │   ├── image_downloader.py     # 图片下载器
│   │   ├── deepseek_client.py      # DeepSeek AI
│   │   ├── qwen_client.py          # Qwen AI
│   │   └── feishu_client.py        # 飞书客户端
│   ├── prompts/        # AI提示词
│   │   └── guide_content.py        # 攻略生成提示词
│   └── utils/          # 工具模块
│       ├── logger.py               # 日志工具
│       ├── random_helper.py        # 随机工具
│       ├── retry.py                # 重试机制
│       └── text_card_generator.py  # 文字卡片生成器
├── tools/              # 管理工具
│   ├── login_helper.py             # 小红书登录助手
│   ├── add_feishu_fields_sdk.py    # 飞书字段创建
│   ├── query_feishu_table.py       # 飞书表格查询
│   └── README.md                   # 工具说明文档
├── deploy/             # 部署脚本
│   ├── README.md       # 部署文档
│   ├── UBUNTU_DEPLOY.md # Ubuntu部署指南
│   ├── install.sh      # 安装脚本
│   └── crontab.txt     # Cron配置
├── requirements.txt    # 依赖包
├── MCP_SETUP.md       # MCP服务配置
├── FEISHU_TABLE_SETUP.md # 飞书表格设置指南
└── README.md
```

## 部署与配置

- **通用部署**: [deploy/README.md](deploy/README.md)
- **Ubuntu 部署**: [deploy/UBUNTU_DEPLOY.md](deploy/UBUNTU_DEPLOY.md)
- **MCP 服务配置**: [MCP_SETUP.md](MCP_SETUP.md)
- **飞书表格设置**: [FEISHU_TABLE_SETUP.md](FEISHU_TABLE_SETUP.md) ⭐ **新增**

## 许可证

MIT License

## 作者

Created with ❤️ by AI Assistant
