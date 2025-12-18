# 更新日志

## [2.0.0] - 2025-12-18

### ✨ 新增功能

#### 双模式发布系统

- **模式 1**: 旅游攻略模式（80%概率）
  - 从小红书搜索真实内容
  - 下载并处理图片（去水印、调整尺寸）
  - AI 生成攻略式文案
  - 包含 3 个景点详细介绍
- **模式 2**: 文字卡片模式（20%概率）
  - 生成纯色背景+一句话内容
  - 支持多种话题类型（职场、旅行、生活感悟等）
  - 自动生成配套文案和标签

#### 飞书完整集成

- 使用飞书官方 SDK（lark-oapi）
- 自动记录每次发布到飞书表格
- 支持 10 个字段的完整记录
- 发布成功/失败实时通知
- 表格字段自动创建工具

#### 工具脚本

- `login_helper.py` - 小红书登录辅助
- `add_feishu_fields_sdk.py` - 飞书表格字段创建
- `query_feishu_table.py` - 飞书表格查询

### 🔧 优化改进

#### 代码优化

- 删除旧的测试脚本
- 统一使用飞书 SDK
- 优化项目结构
- 完善文档说明

#### 数据格式

- 日期字段使用 Unix 时间戳（毫秒）
- 图片数使用数字类型
- 优化字段映射关系

### 📚 文档更新

- 新增 `tools/README.md` - 工具脚本说明
- 更新 `FEISHU_TABLE_SETUP.md` - 飞书表格设置指南
- 更新 `README.md` - 项目结构和依赖说明
- 新增 `CHANGELOG.md` - 更新日志

### 🐛 Bug 修复

- 修复飞书表格日期字段格式问题
- 修复权限检查逻辑
- 优化错误处理和日志输出

---

## [1.0.0] - 2025-12-17

### 初始版本

- 基础的旅游攻略自动发布功能
- 小红书 MCP 集成
- DeepSeek AI 内容生成
- 基础飞书通知功能

---

## 技术栈

### 核心依赖

- Python 3.8+
- 小红书 MCP 服务
- DeepSeek/Qwen AI
- 飞书开放平台
- 飞书 SDK (lark-oapi)

### 主要库

- `requests` - HTTP 客户端
- `pillow` - 图片处理
- `langchain` - MCP 集成
- `lark-oapi` - 飞书 SDK
- `openai` - AI 客户端
- `loguru` - 日志管理

---

## 升级指南

### 从 1.x 升级到 2.0

1. **安装新依赖**:

```bash
pip install lark-oapi>=1.4.0
```

2. **配置飞书表格**:

```bash
# 创建表格字段
python tools/add_feishu_fields_sdk.py

# 验证配置
python tools/query_feishu_table.py
```

3. **更新环境变量**:

```bash
# 确保 config/.env 包含以下变量
FEISHU_APP_ID=your_app_id
FEISHU_APP_SECRET=your_app_secret
FEISHU_TABLE_ID=your_base_id
FEISHU_TABLE_TABLE_ID=your_table_id  # 可选
```

4. **测试运行**:

```bash
python src/scheduler_v2.py --force
```

---

## 路线图

### 计划中的功能

- [ ] 支持更多内容模式（美食、探店等）
- [ ] 数据统计和分析面板
- [ ] 智能发布时间优化
- [ ] 多账号管理
- [ ] 内容质量评分系统
- [ ] A/B 测试功能

### 考虑中的功能

- [ ] 支持其他平台（抖音、快手等）
- [ ] 图片 AI 生成功能
- [ ] 视频内容支持
- [ ] 评论自动回复
- [ ] 数据备份和恢复

---

## 贡献指南

欢迎提交 Issue 和 Pull Request！

### 开发环境设置

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'feat: 添加某个功能'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 提交信息规范

遵循中文提交信息格式：

- `feat(模块): 新功能描述`
- `fix(模块): 修复bug描述`
- `docs(模块): 文档更新`
- `refactor(模块): 代码重构`
- `perf(模块): 性能优化`

---

## 许可证

MIT License

---

## 致谢

感谢所有为这个项目做出贡献的开发者！

特别感谢：

- 小红书 MCP 服务提供商
- DeepSeek AI 团队
- 飞书开放平台
- 所有开源库的维护者
