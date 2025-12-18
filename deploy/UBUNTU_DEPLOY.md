# Ubuntu 部署快速指南（V2 版本）

本指南适用于在 Ubuntu 服务器上部署小红书旅游博主自动发布系统 V2 版本。

## 前置要求

- Ubuntu 20.04+ 服务器
- 有 sudo 权限的用户
- 稳定的网络连接
- 小红书账号

## 一、系统准备

### 1. 更新系统

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. 安装 Python 和依赖

```bash
# 安装Python 3.8+
sudo apt install python3 python3-pip python3-venv python3-dev -y

# 安装图像处理库依赖
sudo apt install libjpeg-dev zlib1g-dev -y

# 验证Python版本
python3 --version  # 应该 >= 3.8
```

## 二、部署应用

### 1. 创建部署目录

```bash
sudo mkdir -p /opt/xhs_travel_bot
sudo chown $USER:$USER /opt/xhs_travel_bot
cd /opt/xhs_travel_bot
```

### 2. 上传代码

**方式 A：使用 Git**

```bash
git clone <your-repo-url> .
```

**方式 B：使用 SCP**

```bash
# 在本地执行
scp -r /local/path/xhs_travel_bot/* user@server:/opt/xhs_travel_bot/
```

### 3. 创建虚拟环境

```bash
cd /opt/xhs_travel_bot
python3 -m venv venv
source venv/bin/activate
```

### 4. 安装 Python 依赖

```bash
# 使用国内镜像加速
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 5. 配置环境变量

```bash
# 复制配置模板
cp config/env.example config/.env

# 编辑配置文件
vim config/.env
```

**必需配置项**：

```bash
# AI服务（二选一）
DEEPSEEK_API_KEY=sk-your-deepseek-key
# 或
QWEN_API_KEY=zsk-your-qwen-key
AI_PROVIDER=deepseek  # 或 qwen

# 飞书配置
FEISHU_APP_ID=cli_xxxxx
FEISHU_APP_SECRET=xxxxx
FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/xxxxx
FEISHU_WEBHOOK_SECRET=xxxxx
FEISHU_TABLE_ID=xxxxx

# 小红书MCP配置
XHS_MCP_URL=http://localhost:18060/mcp
MCP_TRANSPORT=http
```

保存后设置权限：

```bash
chmod 600 config/.env
```

## 三、部署小红书 MCP 服务

V2 版本**必须**运行小红书 MCP 服务才能正常工作。

### 1. 安装 Node.js（MCP 服务依赖）

```bash
# 安装Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# 验证安装
node --version
npm --version
```

### 2. 安装小红书 MCP 工具

```bash
# 全局安装
sudo npm install -g @modelcontextprotocol/server-xiaohongshu

# 或本地安装
npm install @modelcontextprotocol/server-xiaohongshu
```

### 3. 启动 MCP 服务

**方式 A：使用 systemd（推荐，开机自启）**

创建服务文件：

```bash
sudo vim /etc/systemd/system/xhs-mcp.service
```

内容：

```ini
[Unit]
Description=Xiaohongshu MCP Service
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/opt/xhs_travel_bot
ExecStart=/usr/bin/npx @modelcontextprotocol/server-xiaohongshu
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable xhs-mcp
sudo systemctl start xhs-mcp

# 查看状态
sudo systemctl status xhs-mcp
```

**方式 B：使用 screen（临时）**

```bash
# 安装screen
sudo apt install screen -y

# 启动screen会话
screen -S xhs-mcp

# 在screen中启动MCP服务
npx @modelcontextprotocol/server-xiaohongshu

# 按 Ctrl+A 然后按 D 退出screen
# 恢复screen: screen -r xhs-mcp
```

### 4. 登录小红书账号

MCP 服务启动后，需要登录小红书账号。Ubuntu 服务器通常没有显示器，有以下几种登录方式：

#### 方式 A：使用登录辅助工具（推荐，适合无显示器）

```bash
cd /opt/xhs_travel_bot
source venv/bin/activate

# 运行登录辅助工具
python tools/login_helper.py
```

工具会自动：

1. 检查当前登录状态
2. 获取登录二维码并保存为 `login_qrcode.png`
3. 提供下载和扫码指引

**下载二维码到本地**：

```bash
# 在本地电脑执行
scp user@server-ip:/opt/xhs_travel_bot/login_qrcode.png .
```

然后使用小红书 App 扫描二维码登录。

#### 方式 B：使用 SSH 隧道

```bash
# 在本地电脑执行
ssh -L 18060:localhost:18060 user@server-ip

# 保持SSH连接，然后在本地浏览器访问
# http://localhost:18060
# 使用小红书扫码登录
```

#### 方式 C：临时开放端口（不推荐）

```bash
# 配置防火墙允许18060端口
sudo ufw allow 18060

# 在浏览器访问
# http://server-ip:18060

# 登录后立即关闭端口
sudo ufw delete allow 18060
```

### 5. 验证 MCP 服务

```bash
# 测试MCP连接
curl http://localhost:18060/mcp

# 应该返回MCP服务信息
```

## 四、测试运行

### 1. 激活虚拟环境

```bash
cd /opt/xhs_travel_bot
source venv/bin/activate
```

### 2. 测试发布

```bash
# 强制执行（不检查时间窗口）
python3 src/scheduler_v2.py --city 杭州 --force

# 查看日志
tail -f logs/xhs_bot_$(date +%Y-%m-%d).log
```

### 3. 检查结果

- 查看终端输出，确认各步骤执行成功
- 登录小红书查看是否发布成功
- 检查飞书是否收到通知

## 五、配置定时任务

### 1. 编辑 Crontab

```bash
crontab -e
```

### 2. 添加定时任务

```bash
# 每天9-11点之间每小时执行一次
0 9-11 * * * cd /opt/xhs_travel_bot && /opt/xhs_travel_bot/venv/bin/python3 src/scheduler_v2.py >> /var/log/xhs_bot_cron.log 2>&1
```

### 3. 验证 Cron 任务

```bash
# 查看已安装的任务
crontab -l

# 查看Cron日志
tail -f /var/log/xhs_bot_cron.log
```

## 六、监控和维护

### 1. 查看应用日志

```bash
# 实时查看
tail -f /opt/xhs_travel_bot/logs/xhs_bot_$(date +%Y-%m-%d).log

# 查看错误
grep "ERROR" /opt/xhs_travel_bot/logs/xhs_bot_*.log

# 查看最近100行
tail -n 100 /opt/xhs_travel_bot/logs/xhs_bot_$(date +%Y-%m-%d).log
```

### 2. 查看 MCP 服务状态

```bash
# 使用systemd
sudo systemctl status xhs-mcp

# 查看MCP日志
sudo journalctl -u xhs-mcp -f

# 重启MCP服务
sudo systemctl restart xhs-mcp
```

### 3. 手动触发发布

```bash
cd /opt/xhs_travel_bot
source venv/bin/activate
python3 src/scheduler_v2.py --city 北京 --force
```

## 七、常见问题

### 1. MCP 服务无法启动

```bash
# 检查端口占用
sudo lsof -i :18060

# 检查Node.js版本
node --version  # 需要 >= 18

# 查看详细错误
sudo journalctl -u xhs-mcp -n 50
```

### 2. 图片下载失败

```bash
# 检查网络连接
ping xhscdn.com

# 检查磁盘空间
df -h

# 清理临时图片
rm -rf /opt/xhs_travel_bot/temp_images/*
```

### 3. 飞书通知失败

```bash
# 测试飞书Webhook
curl -X POST "YOUR_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{"msg_type":"text","content":{"text":"测试消息"}}'

# 检查飞书权限
# 登录飞书开放平台确认权限已开通
```

### 4. 依赖安装失败

```bash
# 更新pip
pip install --upgrade pip

# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 安装系统依赖
sudo apt install python3-dev libjpeg-dev zlib1g-dev
```

## 八、安全建议

### 1. 保护敏感文件

```bash
chmod 600 /opt/xhs_travel_bot/config/.env
chmod 700 /opt/xhs_travel_bot/logs
```

### 2. 配置防火墙

```bash
# 如果MCP服务只在本地访问，不需要开放端口
# 如果需要远程访问，使用SSH隧道而不是直接开放端口

# 使用ufw（如果启用）
sudo ufw status
```

### 3. 定期备份

```bash
# 备份配置
cp /opt/xhs_travel_bot/config/.env /opt/xhs_travel_bot/config/.env.backup.$(date +%Y%m%d)

# 备份日志（可选）
tar -czf logs_backup_$(date +%Y%m%d).tar.gz /opt/xhs_travel_bot/logs/
```

### 4. 日志轮转

```bash
# 清理30天前的日志
find /opt/xhs_travel_bot/logs/ -name "*.log" -mtime +30 -delete
```

## 九、升级

```bash
cd /opt/xhs_travel_bot
source venv/bin/activate

# 拉取最新代码
git pull

# 更新依赖
pip install -r requirements.txt --upgrade -i https://pypi.tuna.tsinghua.edu.cn/simple

# 重启MCP服务（如果有更新）
sudo systemctl restart xhs-mcp
```

## 十、卸载

```bash
# 停止并删除Cron任务
crontab -e
# 删除相关行

# 停止并删除MCP服务
sudo systemctl stop xhs-mcp
sudo systemctl disable xhs-mcp
sudo rm /etc/systemd/system/xhs-mcp.service
sudo systemctl daemon-reload

# 删除应用
sudo rm -rf /opt/xhs_travel_bot

# 删除日志
sudo rm -rf /var/log/xhs_bot*
```

## 技术支持

如遇到问题，请查看：

- 应用日志：`/opt/xhs_travel_bot/logs/`
- MCP 日志：`sudo journalctl -u xhs-mcp`
- 项目文档：`README.md`、`MCP_SETUP.md`

---

**部署完成！** 🎉

系统将在每天 9-11 点之间自动发布内容到小红书。
