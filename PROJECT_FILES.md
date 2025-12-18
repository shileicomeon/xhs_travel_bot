# 项目文件清单

## 📁 核心代码文件（27 个 Python 文件）

### 主程序

- `src/scheduler_v2.py` - 主调度器，支持双模式发布

### 流程步骤（8 个文件）

- `src/steps/step0_context.py` - 生成上下文
- `src/steps/step1_search_xhs.py` - 搜索小红书内容
- `src/steps/step2_download_images.py` - 下载并处理图片
- `src/steps/step3_generate_guide.py` - 生成攻略文案
- `src/steps/step4_assembly.py` - 组装发布数据
- `src/steps/step5_publish.py` - MCP 发布到小红书
- `src/steps/step6_logging.py` - 飞书记录
- `src/steps/text_card_mode.py` - 文字卡片模式

### 服务层（5 个文件）

- `src/services/xhs_mcp_client.py` - 小红书 MCP 客户端
- `src/services/image_downloader.py` - 图片下载和处理
- `src/services/deepseek_client.py` - DeepSeek AI 客户端
- `src/services/qwen_client.py` - Qwen AI 客户端
- `src/services/feishu_client.py` - 飞书客户端（通知+表格）

### AI 提示词（1 个文件）

- `src/prompts/guide_content.py` - 攻略生成提示词模板

### 工具模块（4 个文件）

- `src/utils/logger.py` - 日志工具
- `src/utils/random_helper.py` - 随机工具（时间窗口、城市选择）
- `src/utils/retry.py` - 重试机制
- `src/utils/text_card_generator.py` - 文字卡片图片生成器

### 管理工具（3 个文件）

- `tools/login_helper.py` - 小红书登录辅助工具
- `tools/add_feishu_fields_sdk.py` - 飞书表格字段创建工具
- `tools/query_feishu_table.py` - 飞书表格查询工具

### 初始化文件（5 个文件）

- `src/__init__.py`
- `src/steps/__init__.py`
- `src/services/__init__.py`
- `src/prompts/__init__.py`
- `src/utils/__init__.py`

---

## 📄 配置文件（4 个）

- `config/cities.yaml` - 城市配置（权重、标签）
- `config/settings.yaml` - 系统配置
- `config/text_topics.yaml` - 文字卡片话题库
- `config/.env` - 环境变量（API 密钥，不提交到 Git）

---

## 📚 文档文件（9 个）

### 主要文档

- `README.md` - 项目主文档
- `CHANGELOG.md` - 更新日志
- `PROJECT_STRUCTURE.md` - 项目结构说明
- `PROJECT_FILES.md` - 本文件（文件清单）

### 配置指南

- `MCP_SETUP.md` - 小红书 MCP 服务配置指南
- `FEISHU_TABLE_SETUP.md` - 飞书表格设置指南
- `UBUNTU_LOGIN_GUIDE.md` - Ubuntu 服务器登录指南
- `V2_COMPLETE.md` - V2 版本完成说明

### 工具文档

- `tools/README.md` - 工具脚本使用说明

---

## 🚀 部署文件（4 个）

- `deploy/README.md` - 部署文档
- `deploy/UBUNTU_DEPLOY.md` - Ubuntu 部署指南
- `deploy/install.sh` - 自动安装脚本
- `deploy/crontab.txt` - Cron 定时任务配置

---

## 📦 依赖管理

- `requirements.txt` - Python 依赖包列表

---

## 📊 统计信息

### 代码统计

- **Python 文件**: 27 个
- **配置文件**: 4 个
- **文档文件**: 9 个
- **部署文件**: 4 个
- **总计**: 44 个核心文件

### 代码行数（估算）

- 核心代码: ~3000 行
- 工具脚本: ~500 行
- 配置文件: ~200 行
- 文档: ~2000 行

---

## 🗂️ 目录结构

```
xhs_travel_bot/
├── config/                 # 配置文件目录
│   ├── cities.yaml
│   ├── settings.yaml
│   ├── text_topics.yaml
│   └── .env
├── src/                    # 源代码目录
│   ├── scheduler_v2.py
│   ├── steps/             # 流程步骤
│   ├── services/          # 服务层
│   ├── prompts/           # AI提示词
│   └── utils/             # 工具模块
├── tools/                  # 管理工具
│   ├── login_helper.py
│   ├── add_feishu_fields_sdk.py
│   ├── query_feishu_table.py
│   └── README.md
├── deploy/                 # 部署脚本
│   ├── README.md
│   ├── UBUNTU_DEPLOY.md
│   ├── install.sh
│   └── crontab.txt
├── logs/                   # 日志目录（自动生成）
├── temp_images/            # 临时图片目录（自动生成）
├── venv/                   # 虚拟环境（不提交）
├── requirements.txt        # 依赖包
├── README.md              # 主文档
├── CHANGELOG.md           # 更新日志
├── MCP_SETUP.md          # MCP配置指南
├── FEISHU_TABLE_SETUP.md # 飞书配置指南
└── PROJECT_FILES.md      # 本文件
```

---

## 🔍 文件用途速查

### 需要配置的文件

1. `config/.env` - **必须配置**，包含所有 API 密钥
2. `config/cities.yaml` - 可选，自定义城市列表
3. `config/text_topics.yaml` - 可选，自定义文字卡片话题

### 需要运行的文件

1. `src/scheduler_v2.py` - 主程序，定时运行
2. `tools/login_helper.py` - 首次配置时运行
3. `tools/add_feishu_fields_sdk.py` - 首次配置飞书时运行

### 需要阅读的文件

1. `README.md` - 快速开始
2. `MCP_SETUP.md` - MCP 服务配置
3. `FEISHU_TABLE_SETUP.md` - 飞书表格配置
4. `tools/README.md` - 工具使用说明

---

## 📝 维护建议

### 定期检查

- 每周检查日志文件大小
- 每月检查临时图片目录
- 定期更新依赖包

### 备份建议

- 备份 `config/.env` 文件
- 备份飞书表格数据
- 备份日志文件（可选）

### 清理建议

```bash
# 清理日志（保留最近7天）
find logs/ -name "*.log" -mtime +7 -delete

# 清理临时图片
rm -rf temp_images/*

# 清理Python缓存
find . -type d -name "__pycache__" -exec rm -rf {} +
```

---

## 🎯 快速导航

- **开始使用**: 阅读 `README.md`
- **配置 MCP**: 阅读 `MCP_SETUP.md`
- **配置飞书**: 阅读 `FEISHU_TABLE_SETUP.md`
- **使用工具**: 阅读 `tools/README.md`
- **部署系统**: 阅读 `deploy/README.md`
- **查看更新**: 阅读 `CHANGELOG.md`
