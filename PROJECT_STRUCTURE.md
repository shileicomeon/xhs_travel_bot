# 项目结构说明

## 核心文档

```
xhs_travel_bot/
├── README.md                    # 项目主文档
├── V2_COMPLETE.md              # V2完成总结
├── MCP_SETUP.md                # MCP服务配置指南
└── UBUNTU_LOGIN_GUIDE.md       # Ubuntu登录指南
```

## 部署文档

```
deploy/
├── README.md                    # 通用部署指南
├── UBUNTU_DEPLOY.md            # Ubuntu完整部署指南
├── install.sh                  # 安装脚本
└── crontab.txt                 # Cron配置示例
```

## 源代码

```
src/
├── scheduler_v2.py             # V2主调度器
│
├── steps/                      # 核心步骤（6个）
│   ├── step0_context.py        # 生成上下文
│   ├── step1_search_xhs.py     # 搜索小红书
│   ├── step2_download_images.py # 下载图片
│   ├── step3_generate_guide.py  # 生成攻略
│   ├── step4_assembly.py       # 组装数据
│   ├── step5_publish.py        # MCP发布
│   └── step6_logging.py        # 飞书记录
│
├── services/                   # 服务层（5个）
│   ├── xhs_mcp_client.py       # 小红书MCP客户端 ⭐
│   ├── image_downloader.py     # 图片下载器
│   ├── deepseek_client.py      # DeepSeek AI
│   ├── qwen_client.py          # Qwen AI
│   └── feishu_client.py        # 飞书客户端
│
├── prompts/                    # AI提示词
│   └── guide_content.py        # 攻略生成提示词
│
└── utils/                      # 工具模块
    ├── logger.py               # 日志
    ├── retry.py                # 重试机制
    └── random_helper.py        # 随机数生成
```

## 配置文件

```
config/
├── .env                        # 环境变量（API密钥）
├── env.example                 # 环境变量模板
├── cities.yaml                 # 城市配置
└── settings.yaml               # 系统配置
```

## 工具脚本

```
tools/
└── login_helper.py             # 登录辅助工具（Ubuntu无显示器）
```

## 文件说明

### 核心文档

- **README.md**: 项目主文档，包含快速开始、功能特点、使用方法
- **V2_COMPLETE.md**: V2 版本完成总结，包含技术实现、性能指标、部署支持
- **MCP_SETUP.md**: 小红书 MCP 服务配置和使用指南，包含登录方法
- **UBUNTU_LOGIN_GUIDE.md**: Ubuntu 无显示器环境登录专门指南

### 部署文档

- **deploy/README.md**: 通用部署文档，适用于所有平台
- **deploy/UBUNTU_DEPLOY.md**: Ubuntu 完整部署指南（从零开始）
- **deploy/install.sh**: 自动化安装脚本
- **deploy/crontab.txt**: Cron 定时任务配置示例

### 源代码

#### 主程序

- **scheduler_v2.py**: V2 版本主调度器，协调整个发布流程

#### 核心步骤

1. **step0_context.py**: 生成发布上下文（城市、主题、图片数）
2. **step1_search_xhs.py**: 从小红书搜索真实内容并提取图片
3. **step2_download_images.py**: 下载图片并处理（去水印、调整尺寸）
4. **step3_generate_guide.py**: AI 生成攻略风格内容
5. **step4_assembly.py**: 组装发布数据（标题、内容、图片、标签）
6. **step5_publish.py**: 通过 MCP 发布到小红书
7. **step6_logging.py**: 记录到飞书（通知+表格）

#### 服务层

- **xhs_mcp_client.py**: 小红书 MCP 客户端（核心）

  - `check_login_status()`: 检查登录状态
  - `get_login_qrcode()`: 获取登录二维码（Ubuntu）
  - `search_feeds()`: 搜索内容
  - `get_feed_detail()`: 获取帖子详情
  - `publish_content()`: 发布内容

- **image_downloader.py**: 图片下载和处理

  - 下载图片
  - 去水印（基础实现）
  - 调整尺寸（符合小红书要求）
  - 去重检查

- **deepseek_client.py**: DeepSeek AI 客户端

  - 生成攻略内容
  - 支持 JSON 格式输出

- **qwen_client.py**: Qwen AI 客户端（备选）

  - 与 DeepSeek 功能相同
  - 可通过环境变量切换

- **feishu_client.py**: 飞书客户端
  - 发送 Webhook 通知
  - 写入多维表格

#### 工具模块

- **logger.py**: 基于 loguru 的结构化日志
- **retry.py**: 基于 tenacity 的重试机制
- **random_helper.py**: 随机数生成辅助函数

### 配置文件

- **.env**: 环境变量（不提交到 Git）

  - API 密钥（DeepSeek/Qwen）
  - 飞书配置
  - MCP 服务地址

- **cities.yaml**: 城市配置

  - 地标关键词
  - 美食关键词
  - 氛围关键词

- **settings.yaml**: 系统配置
  - 发布时间窗口
  - 图片数量
  - 重试策略

### 工具脚本

- **login_helper.py**: 登录辅助工具
  - 检查登录状态
  - 获取登录二维码
  - 保存为 PNG 图片
  - 提供操作指引

## 核心依赖

```
Python 3.8+
langchain-mcp-adapters      # MCP客户端
pillow                      # 图片处理
requests                    # HTTP请求
pyyaml                      # YAML解析
python-dotenv               # 环境变量
loguru                      # 日志
tenacity                    # 重试
imagehash                   # 图片去重
```

## 数据流

```
Step 0: 生成上下文
  ↓
Step 1: 搜索小红书 (MCP)
  ↓
Step 2: 下载图片
  ↓
Step 3: AI生成攻略
  ↓
Step 4: 组装数据
  ↓
Step 5: MCP发布
  ↓
Step 6: 飞书记录
```

## 运行模式

### 测试模式（强制执行）

```bash
python src/scheduler_v2.py --city 杭州 --force
```

### 生产模式（检查时间窗口）

```bash
python src/scheduler_v2.py
```

### Cron 定时任务

```bash
0 9-11 * * * cd /path && python src/scheduler_v2.py
```

## 项目特点

✅ **纯 V2 模式**: 完全独立，不依赖 V1  
✅ **真实内容源**: 从小红书获取真实图片  
✅ **攻略风格**: 结构化内容，带步骤和图标  
✅ **跨平台**: macOS、Ubuntu、CentOS  
✅ **无显示器支持**: Ubuntu 服务器可用登录辅助工具  
✅ **生产就绪**: 真实运行成功，耗时~100 秒

---

**最后更新**: 2025-12-17  
**版本**: V2 Pure Mode
