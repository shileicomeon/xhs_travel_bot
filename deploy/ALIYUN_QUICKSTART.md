# 阿里云 Ubuntu 一键部署指南

## 📦 快速开始

### 1. 上传代码到服务器

```bash
# 方式A: 在本地打包上传
cd /path/to/xhs_travel_bot
tar -czf xhs_travel_bot.tar.gz .
scp xhs_travel_bot.tar.gz username@your-server:/tmp/

# 在服务器上解压
ssh username@your-server
sudo mkdir -p /opt/xhs_travel_bot
sudo chown $USER:$USER /opt/xhs_travel_bot
cd /opt/xhs_travel_bot
tar -xzf /tmp/xhs_travel_bot.tar.gz
```

```bash
# 方式B: 使用Git（如果有仓库）
ssh username@your-server
sudo mkdir -p /opt/xhs_travel_bot
sudo chown $USER:$USER /opt/xhs_travel_bot
cd /opt/xhs_travel_bot
git clone <your-repo-url> .
```

### 2. 运行一键部署脚本

```bash
# 确保脚本有执行权限
chmod +x /opt/xhs_travel_bot/deploy/aliyun_install.sh

# 运行部署脚本
/opt/xhs_travel_bot/deploy/aliyun_install.sh
```

脚本会自动完成：

- ✅ 配置阿里云镜像源（APT、pip、npm）
- ✅ 安装 Python 3、Node.js 和所有依赖
- ✅ 安装中文字体（文泉驿）
- ✅ 创建虚拟环境
- ✅ 安装小红书 MCP 工具
- ✅ 创建 systemd 服务
- ✅ 生成快捷管理脚本

### 3. 配置环境变量

```bash
vim /opt/xhs_travel_bot/config/.env
```

填入以下配置：

```bash
# AI服务（二选一）
DEEPSEEK_API_KEY=sk-your-deepseek-key
# 或
QWEN_API_KEY=sk-your-qwen-key
AI_PROVIDER=deepseek  # 或 qwen

# 飞书配置
FEISHU_APP_ID=cli_xxxxx
FEISHU_APP_SECRET=xxxxx
FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/xxxxx
FEISHU_WEBHOOK_SECRET=xxxxx
FEISHU_TABLE_ID=xxxxx

# 小红书MCP配置（默认即可）
XHS_MCP_URL=http://localhost:18060/mcp
MCP_TRANSPORT=http
```

保存后按 `Esc` 然后输入 `:wq` 回车。

### 4. 启动 MCP 服务

```bash
# 启动服务
sudo systemctl start xhs-mcp

# 查看状态
sudo systemctl status xhs-mcp

# 查看日志
sudo journalctl -u xhs-mcp -f
```

### 5. 登录小红书账号

```bash
# 运行登录助手
/opt/xhs_travel_bot/login_xhs.sh
```

**Ubuntu 无界面登录方式：**

#### 方式 1：SSH 隧道（推荐）

在**本地电脑**执行：

```bash
# 建立SSH隧道
ssh -L 18060:localhost:18060 username@your-server-ip

# 保持连接，然后在本地浏览器访问
# http://localhost:18060

# 使用小红书App扫描页面上的二维码
```

#### 方式 2：下载二维码（适合 Ubuntu）

在**本地电脑**执行：

```bash
# 下载二维码
scp username@your-server-ip:/opt/xhs_travel_bot/login_qrcode.png ~/Downloads/

# 打开图片，用小红书App扫描
# 扫描后等待10-30秒

# 验证登录状态
ssh username@your-server-ip
/opt/xhs_travel_bot/login_xhs.sh
```

### 6. 测试发布

```bash
# 测试发布一条内容
/opt/xhs_travel_bot/test_publish.sh
```

查看日志：

```bash
tail -f /opt/xhs_travel_bot/logs/xhs_bot_$(date +%Y-%m-%d).log
```

### 7. 配置定时任务

```bash
crontab -e
```

添加以下内容：

```bash
# 每天9-11点之间每小时执行一次
0 9-11 * * * /opt/xhs_travel_bot/venv/bin/python3 /opt/xhs_travel_bot/src/scheduler_v2.py >> /var/log/xhs_bot.log 2>&1
```

保存后按 `Esc` 然后输入 `:wq` 回车。

验证定时任务：

```bash
crontab -l
```

## 🔧 常用命令

### MCP 服务管理

```bash
# 启动
sudo systemctl start xhs-mcp

# 停止
sudo systemctl stop xhs-mcp

# 重启
sudo systemctl restart xhs-mcp

# 查看状态
sudo systemctl status xhs-mcp

# 查看日志
sudo journalctl -u xhs-mcp -f

# 开机自启（已默认启用）
sudo systemctl enable xhs-mcp
```

### 应用管理

```bash
# 手动发布
cd /opt/xhs_travel_bot
source venv/bin/activate
python3 src/scheduler_v2.py --force

# 指定城市发布
python3 src/scheduler_v2.py --city 杭州 --force

# 查看日志
tail -f logs/xhs_bot_$(date +%Y-%m-%d).log

# 查看最近100行日志
tail -n 100 logs/xhs_bot_$(date +%Y-%m-%d).log

# 搜索错误日志
grep "ERROR" logs/xhs_bot_*.log
```

### 快捷脚本

```bash
# 启动MCP服务
/opt/xhs_travel_bot/start_mcp.sh

# 登录小红书
/opt/xhs_travel_bot/login_xhs.sh

# 测试发布
/opt/xhs_travel_bot/test_publish.sh
```

## 🐛 故障排查

### 1. MCP 服务无法启动

```bash
# 检查端口占用
sudo lsof -i :18060

# 如果被占用，杀死进程
sudo kill -9 <PID>

# 重启服务
sudo systemctl restart xhs-mcp
```

### 2. 图片下载失败

```bash
# 检查磁盘空间
df -h

# 清理临时图片
rm -rf /opt/xhs_travel_bot/temp_images/*

# 检查网络
ping xhscdn.com
```

### 3. 飞书通知失败

```bash
# 测试Webhook
curl -X POST "YOUR_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{"msg_type":"text","content":{"text":"测试消息"}}'

# 检查配置
cat /opt/xhs_travel_bot/config/.env | grep FEISHU
```

### 4. 文字卡片中文显示为方框

```bash
# 安装中文字体
sudo apt install fonts-wqy-microhei fonts-wqy-zenhei -y

# 验证字体安装
fc-list :lang=zh

# 重启应用测试
/opt/xhs_travel_bot/test_publish.sh
```

### 5. Python 依赖安装失败

```bash
# 更新pip
cd /opt/xhs_travel_bot
source venv/bin/activate
pip install --upgrade pip

# 使用阿里云镜像重新安装
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# 安装系统依赖
sudo apt install python3-dev libjpeg-dev zlib1g-dev
```

### 6. 查看详细错误信息

```bash
# 查看应用日志
tail -f /opt/xhs_travel_bot/logs/xhs_bot_$(date +%Y-%m-%d).log

# 查看MCP服务日志
sudo journalctl -u xhs-mcp -n 100

# 查看Cron日志
tail -f /var/log/xhs_bot.log

# 查看系统日志
sudo tail -f /var/log/syslog | grep xhs
```

## 📊 监控和维护

### 日志管理

```bash
# 查看今天的日志
tail -f /opt/xhs_travel_bot/logs/xhs_bot_$(date +%Y-%m-%d).log

# 清理30天前的日志
find /opt/xhs_travel_bot/logs/ -name "*.log" -mtime +30 -delete

# 日志轮转（可选）
sudo vim /etc/logrotate.d/xhs_bot
```

添加以下内容：

```
/opt/xhs_travel_bot/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
}
```

### 定期检查

```bash
# 检查MCP服务状态
sudo systemctl status xhs-mcp

# 检查磁盘空间
df -h /opt/xhs_travel_bot

# 检查登录状态
/opt/xhs_travel_bot/login_xhs.sh

# 查看最近发布记录
tail -n 50 /opt/xhs_travel_bot/logs/xhs_bot_$(date +%Y-%m-%d).log | grep "发布成功"
```

## 🔄 更新升级

```bash
cd /opt/xhs_travel_bot

# 拉取最新代码
git pull

# 激活虚拟环境
source venv/bin/activate

# 更新依赖
pip install -r requirements.txt --upgrade -i https://mirrors.aliyun.com/pypi/simple/

# 重启MCP服务
sudo systemctl restart xhs-mcp

# 测试
./test_publish.sh
```

## 🔐 安全建议

### 1. 保护配置文件

```bash
chmod 600 /opt/xhs_travel_bot/config/.env
chmod 700 /opt/xhs_travel_bot/logs
```

### 2. 防火墙配置

```bash
# 检查防火墙状态
sudo ufw status

# MCP服务仅本地访问，不需要开放18060端口
# 如果误开放了，关闭它
sudo ufw delete allow 18060
```

### 3. 定期备份

```bash
# 备份配置
cp /opt/xhs_travel_bot/config/.env /opt/xhs_travel_bot/config/.env.backup.$(date +%Y%m%d)

# 备份数据（可选）
tar -czf xhs_bot_backup_$(date +%Y%m%d).tar.gz \
  /opt/xhs_travel_bot/config/.env \
  /opt/xhs_travel_bot/logs/
```

## 📚 相关文档

- [Ubuntu 完整部署指南](UBUNTU_DEPLOY.md)
- [MCP 服务配置](../MCP_SETUP.md)
- [飞书表格设置](../FEISHU_TABLE_SETUP.md)
- [项目说明](../README.md)

## 💬 获取帮助

如遇到问题：

1. 查看日志文件
2. 参考故障排查章节
3. 查看相关文档
4. 检查飞书通知中的错误详情（已优化，包含详细排查建议）

---

**部署完成！** 🎉

系统将在每天 9-11 点之间自动发布内容到小红书。
