# 小红书 MCP 集成说明

## 概述

本项目使用小红书 MCP（Model Context Protocol）工具进行内容发布。MCP 是一个标准化的协议，允许 AI 系统与外部工具进行交互。

## 前置条件

1. **启动小红书 MCP 服务**

   - 确保小红书 MCP 服务已在本地运行
   - 默认地址：`http://localhost:18060/mcp`
   - 服务需要支持 SSE（Server-Sent Events）或 HTTP 传输

2. **登录小红书账号**

   **有显示器环境（macOS/Windows）**：

   - 访问 `http://localhost:18060`
   - 使用小红书 App 扫码登录

   **无显示器环境（Ubuntu 服务器）**：

   - 使用 `get_login_qrcode` 工具获取二维码
   - 将二维码保存为图片或在本地查看
   - 使用小红书 App 扫码登录

3. **配置环境变量**

   在 `config/.env` 文件中配置：

   ```bash
   # 小红书MCP配置
   XHS_MCP_URL=http://localhost:18060/mcp
   MCP_TRANSPORT=http  # 推荐使用 'http'
   ```

## MCP 服务要求

### 必需的工具

MCP 服务必须提供以下工具：

1. **`publish_content`** - 发布内容到小红书

   参数：

   - `title` (string): 笔记标题
   - `content` (string): 笔记正文（标签会自动附加到正文末尾）
   - `images` (array): 图片 URL 列表或本地文件路径列表

   返回：

   - 成功：返回笔记 ID 或包含 `note_id`/`id` 字段的对象
   - 失败：抛出异常

### 可选的工具

- `check_login_status` - 检查登录状态（推荐）
- `get_login_qrcode` - 获取登录二维码（用于无显示器环境）
- `get_user_info` - 获取用户信息（可选）
- `search_feeds` - 搜索小红书内容
- `get_feed_detail` - 获取帖子详情

## 登录指南

### 有显示器环境（macOS/Windows）

1. 启动 MCP 服务后，访问 `http://localhost:18060`
2. 使用小红书 App 扫描页面上的二维码
3. 确认登录

### 无显示器环境（Ubuntu 服务器）

#### 方法 1：使用登录辅助工具（推荐）

```bash
# 运行登录辅助工具
python tools/login_helper.py
```

工具会：

1. 检查当前登录状态
2. 调用 `get_login_qrcode` 获取二维码
3. 将二维码保存为 `login_qrcode.png`
4. 提供后续步骤指引

然后：

```bash
# 下载二维码到本地
scp user@server:/path/to/login_qrcode.png .

# 使用小红书App扫描二维码登录
```

#### 方法 2：使用 SSH 隧道

```bash
# 在本地电脑执行
ssh -L 18060:localhost:18060 user@server-ip

# 在本地浏览器访问
http://localhost:18060

# 使用小红书App扫码登录
```

#### 方法 3：手动调用 MCP 工具

```python
import asyncio
from src.services.xhs_mcp_client import XhsMcpClient

async def get_qrcode():
    client = XhsMcpClient()
    result = await client.get_login_qrcode(save_path="qrcode.png")
    print(f"二维码已保存: {result}")

asyncio.run(get_qrcode())
```

### 验证登录状态

```bash
# 使用登录辅助工具
python tools/login_helper.py

# 或手动检查
python -c "
import asyncio
from src.services.xhs_mcp_client import XhsMcpClient

async def check():
    client = XhsMcpClient()
    status = await client.check_login_status()
    print(status)

asyncio.run(check())
"
```

## 使用示例

### 基本发布流程

```python
from src.steps import publish_to_xhs

# 准备发布内容
post = {
    "title": "厦门一日游攻略",
    "content": "今天带大家打卡厦门最美的景点...",
    "tags": ["#厦门旅行", "#吃喝玩乐", "#周末去哪玩"],
    "images": [
        "https://example.com/image1.jpg",
        "https://example.com/image2.jpg",
    ],
    "is_local": False  # 如果是本地文件路径，设为True
}

# 发布
result = publish_to_xhs(post)
print(f"发布成功！笔记ID: {result['note_id']}")
```

### 使用本地图片

如果图片需要处理（裁剪、压缩等），系统会自动保存到本地临时文件：

```python
post = {
    "title": "美食探店",
    "content": "今天的美食分享...",
    "tags": ["#美食", "#探店"],
    "images": [
        "/tmp/xhs_images/processed_1.jpg",
        "/tmp/xhs_images/processed_2.jpg",
    ],
    "is_local": True  # 标记为本地文件
}

result = publish_to_xhs(post)
# 发布后会自动清理临时文件
```

## 故障排查

### 1. 连接失败（405 Method Not Allowed）

**错误信息：**

```
httpx.HTTPStatusError: Client error '405 Method Not Allowed' for url 'http://localhost:18060/mcp'
```

**解决方案：**

- 检查 MCP 服务是否已启动
- 确认 MCP 服务 URL 是否正确
- 尝试将 `MCP_TRANSPORT` 从 `sse` 改为 `http`

### 2. 找不到发布工具

**错误信息：**

```
未找到 publish_content 工具，请确认MCP服务是否正常运行
```

**解决方案：**

- 确认 MCP 服务已正确实现 `publish_content` 工具
- 检查工具名称是否完全匹配（区分大小写）
- 查看 MCP 服务日志确认工具已注册

### 3. 图片上传失败

**可能原因：**

- 图片 URL 无法访问
- 本地文件路径不存在
- 图片格式不支持
- 图片尺寸超出限制

**解决方案：**

- 使用 `step4_assembly` 中的图片处理功能
- 确保图片符合小红书规范（1000x1000 到 4096x4096，≤5MB）

## 测试 MCP 连接

可以使用以下命令测试 MCP 服务是否正常：

```bash
cd /Users/shialei/PycharmProjects/xhs_travel_bot
source venv/bin/activate

python -c "
import asyncio
from src.steps.step5_publish import _get_mcp_client

async def test():
    client = _get_mcp_client()
    tools = await client.get_tools()
    print('可用工具:', [getattr(t, 'name', '') for t in tools])

asyncio.run(test())
"
```

## 参考资料

- [MCP 官方文档](https://modelcontextprotocol.io/)
- [LangChain MCP 适配器](https://github.com/langchain-ai/langchain-mcp-adapters)
- 小红书 MCP 服务文档（请参考您的 MCP 服务提供商）

## 技术架构

```
┌─────────────────┐
│  调度器         │
│  (scheduler.py) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  发布模块       │
│  (step5_publish)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────┐
│  MCP客户端      │─────▶│  MCP服务     │
│  (langchain-mcp)│◀─────│  (localhost) │
└─────────────────┘      └──────┬───────┘
                                │
                                ▼
                         ┌──────────────┐
                         │  小红书API   │
                         └──────────────┘
```

## 更新日志

- **2025-12-17**: 初始版本，集成小红书 MCP 发布功能
