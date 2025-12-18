# 工具脚本说明

本目录包含用于系统管理和维护的工具脚本。

## 📋 可用工具

### 1. login_helper.py

**用途**: 小红书 MCP 服务登录辅助工具

**使用场景**:

- 首次配置系统时登录小红书账号
- 在无显示器的服务器上登录（如 Ubuntu 服务器）
- 登录会话过期需要重新登录

**使用方法**:

```bash
python tools/login_helper.py
```

**功能**:

- 检查当前登录状态
- 生成登录二维码
- 保存二维码图片供扫描
- 提供登录指引

---

### 2. add_feishu_fields_sdk.py

**用途**: 为飞书表格添加字段

**使用场景**:

- 首次配置飞书表格时创建必需字段
- 表格字段缺失时补充字段
- 需要添加新字段时

**使用方法**:

```bash
python tools/add_feishu_fields_sdk.py
```

**功能**:

- 自动检测现有字段
- 创建缺失的必需字段
- 支持文本、数字、日期、单选等类型
- 验证字段创建结果

**创建的字段**:

- 日期（日期类型）
- 发布时间（文本）
- 标题（文本）
- 城市（文本）
- 模式（单选：旅游攻略/文字卡片）
- 状态（单选：✅ 成功/❌ 失败）
- 笔记 ID（文本）
- 耗时（文本）
- 图片数（数字）
- 失败原因（文本）

---

### 3. query_feishu_table.py

**用途**: 查询飞书表格信息

**使用场景**:

- 查看表格字段配置
- 查看最近的发布记录
- 检查表格状态
- 调试飞书集成

**使用方法**:

```bash
python tools/query_feishu_table.py
```

**功能**:

- 列出所有字段及其类型
- 显示最近 10 条记录
- 检查缺失字段
- 提供表格访问链接

---

## 🔧 使用前提

### 环境要求

- Python 3.8+
- 已安装项目依赖（`pip install -r requirements.txt`）
- 已配置环境变量（`config/.env`）

### 必需的环境变量

**小红书 MCP** (login_helper.py):

```bash
# MCP服务会自动使用默认配置
# 无需额外环境变量
```

**飞书 SDK** (add_feishu_fields_sdk.py, query_feishu_table.py):

```bash
FEISHU_APP_ID=your_app_id
FEISHU_APP_SECRET=your_app_secret
FEISHU_TABLE_ID=your_base_id
FEISHU_TABLE_TABLE_ID=your_table_id  # 可选，会自动获取
```

---

## 📖 使用流程

### 首次配置系统

1. **登录小红书**:

```bash
python tools/login_helper.py
```

2. **配置飞书表格**:

```bash
python tools/add_feishu_fields_sdk.py
```

3. **验证配置**:

```bash
python tools/query_feishu_table.py
```

4. **测试发布**:

```bash
python src/scheduler_v2.py --force
```

---

## 🆘 故障排查

### login_helper.py 问题

**问题**: 无法连接 MCP 服务

- 检查 MCP 服务是否已启动: `npx @modelcontextprotocol/server-xiaohongshu`
- 检查端口是否被占用: `lsof -i :18060`

**问题**: 二维码生成失败

- 确认 MCP 服务支持 `get_login_qrcode` 工具
- 查看 MCP 服务日志

### add_feishu_fields_sdk.py 问题

**问题**: 权限不足

- 确认已开通 `bitable:app` 和 `base:record:create` 权限
- 访问飞书开放平台权限管理页面检查

**问题**: 字段创建失败

- 检查字段名是否已存在
- 确认字段类型是否支持
- 查看详细错误信息

### query_feishu_table.py 问题

**问题**: 无法获取表格信息

- 检查 `FEISHU_TABLE_ID` 和 `FEISHU_TABLE_TABLE_ID` 是否正确
- 确认应用有读取权限

---

## 📚 相关文档

- [飞书表格设置指南](../FEISHU_TABLE_SETUP.md)
- [MCP 服务配置](../MCP_SETUP.md)
- [Ubuntu 部署指南](../deploy/UBUNTU_DEPLOY.md)

---

## 💡 提示

- 所有工具脚本都支持 `--help` 参数查看详细说明
- 建议在测试环境先运行一次，确认无误后再在生产环境使用
- 定期运行 `query_feishu_table.py` 检查系统状态
- 登录会话可能过期，需要定期使用 `login_helper.py` 重新登录
