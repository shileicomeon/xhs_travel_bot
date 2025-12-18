# 快速参考卡片

## 🚀 阿里云Ubuntu部署（5分钟）

```bash
# 1. 上传代码
scp -r xhs_travel_bot/* user@server:/opt/xhs_travel_bot/

# 2. 一键部署
ssh user@server
/opt/xhs_travel_bot/deploy/aliyun_install.sh

# 3. 配置
vim /opt/xhs_travel_bot/config/.env

# 4. 启动
sudo systemctl start xhs-mcp

# 5. 登录
/opt/xhs_travel_bot/login_xhs.sh

# 6. 测试
/opt/xhs_travel_bot/test_publish.sh
```

## 📱 Ubuntu无界面登录（3种方式）

### 方式1: SSH隧道（推荐）
```bash
# 本地执行
ssh -L 18060:localhost:18060 user@server
# 浏览器访问 http://localhost:18060
```

### 方式2: 下载二维码
```bash
# 本地执行
scp user@server:/opt/xhs_travel_bot/login_qrcode.png ~/Downloads/
# 用小红书App扫描
```

### 方式3: 临时开放端口（不推荐）
```bash
# 服务器执行
sudo ufw allow 18060/tcp
# 浏览器访问 http://server-ip:18060
# 登录后立即关闭
sudo ufw delete allow 18060/tcp
```

## 🔧 常用命令

### 服务管理
```bash
sudo systemctl start xhs-mcp      # 启动
sudo systemctl stop xhs-mcp       # 停止
sudo systemctl restart xhs-mcp    # 重启
sudo systemctl status xhs-mcp     # 状态
sudo journalctl -u xhs-mcp -f     # 日志
```

### 应用操作
```bash
cd /opt/xhs_travel_bot
source venv/bin/activate

# 手动发布
python3 src/scheduler_v2.py --force

# 指定城市
python3 src/scheduler_v2.py --city 杭州 --force

# 查看日志
tail -f logs/xhs_bot_$(date +%Y-%m-%d).log
```

### 快捷脚本
```bash
/opt/xhs_travel_bot/start_mcp.sh     # 启动MCP
/opt/xhs_travel_bot/login_xhs.sh     # 登录
/opt/xhs_travel_bot/test_publish.sh  # 测试
```

## 🐛 故障排查速查

### MCP服务问题
```bash
sudo systemctl status xhs-mcp
sudo lsof -i :18060
sudo systemctl restart xhs-mcp
```

### 登录问题
```bash
/opt/xhs_travel_bot/login_xhs.sh
# 检查二维码: ls -lh login_qrcode.png
```

### 图片问题
```bash
df -h                                    # 磁盘空间
rm -rf /opt/xhs_travel_bot/temp_images/* # 清理
```

### 字体问题
```bash
sudo apt install fonts-wqy-microhei -y
fc-list :lang=zh
```

### 网络问题
```bash
ping xhscdn.com
ping baidu.com
```

## 📊 飞书通知错误类型

| 错误类型 | 关键词 | 排查方向 |
|---------|--------|---------|
| 🔌 MCP服务 | MCP, Session | 检查服务、登录状态 |
| ⏱️ 超时 | timeout | 检查网络连接 |
| 🔐 权限 | Permission, Access | 检查权限配置 |
| 🌐 网络 | Network, Connection | 检查网络、防火墙 |
| 🖼️ 图片 | Image, 图片 | 检查磁盘、权限 |
| 🤖 AI服务 | AI, API, DeepSeek | 检查密钥、额度 |
| 🔤 字体 | Font, 字体 | 安装中文字体 |

## 📁 重要文件位置

```
/opt/xhs_travel_bot/
├── config/.env              # 配置文件
├── logs/                    # 日志目录
├── temp_images/             # 临时图片
├── login_qrcode.png         # 登录二维码
├── start_mcp.sh             # 启动MCP
├── login_xhs.sh             # 登录助手
└── test_publish.sh          # 测试发布
```

## 🔑 环境变量模板

```bash
# AI服务（二选一）
DEEPSEEK_API_KEY=sk-xxx
# 或
QWEN_API_KEY=sk-xxx
AI_PROVIDER=deepseek

# 飞书
FEISHU_APP_ID=cli_xxx
FEISHU_APP_SECRET=xxx
FEISHU_WEBHOOK_URL=https://xxx
FEISHU_WEBHOOK_SECRET=xxx
FEISHU_TABLE_ID=xxx

# MCP（默认）
XHS_MCP_URL=http://localhost:18060/mcp
MCP_TRANSPORT=http
```

## ⏰ 定时任务

```bash
crontab -e
```

添加：
```
# 每天9-11点每小时执行
0 9-11 * * * /opt/xhs_travel_bot/venv/bin/python3 /opt/xhs_travel_bot/src/scheduler_v2.py >> /var/log/xhs_bot.log 2>&1
```

## 🧪 测试命令

```bash
cd /opt/xhs_travel_bot
source venv/bin/activate

# 测试失败通知
python tools/test_failure_notification.py

# 测试登录
python tools/login_helper.py

# 测试发布
python src/scheduler_v2.py --force
```

## 📚 文档索引

- [阿里云快速开始](deploy/ALIYUN_QUICKSTART.md) ⭐
- [Ubuntu完整部署](deploy/UBUNTU_DEPLOY.md)
- [Ubuntu优化说明](UBUNTU_IMPROVEMENTS.md)
- [MCP服务配置](MCP_SETUP.md)
- [飞书表格设置](FEISHU_TABLE_SETUP.md)
- [项目说明](README.md)
- [完成总结](SUMMARY.md)

---

**提示**: 将此文件打印或保存为书签，随时查阅！


