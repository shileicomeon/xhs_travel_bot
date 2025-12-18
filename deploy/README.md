# 部署文档（V2 版本）

## 环境要求

- Ubuntu 20.04+ / CentOS 7+ / macOS
- Python 3.8+
- 小红书 MCP 服务（必需，用于搜索和发布）
- 网络连接（访问 DeepSeek AI、飞书、小红书 MCP）

## 部署步骤

### 1. 安装 Python 和依赖

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Python 3
sudo apt install python3 python3-pip -y

# 验证版本
python3 --version  # 应该 >= 3.8
```

### 2. 上传代码

```bash
# 创建目录
sudo mkdir -p /opt/xhs_travel_bot
sudo chown $USER:$USER /opt/xhs_travel_bot

# 上传代码（使用git或scp）
cd /opt
git clone <your-repo-url> xhs_travel_bot

# 或使用scp
# scp -r /local/path/xhs_travel_bot user@server:/opt/
```

### 3. 安装依赖

```bash
cd /opt/xhs_travel_bot
pip3 install -r requirements.txt
```

### 4. 配置环境变量

```bash
# 复制配置模板
cp config/env.example config/.env

# 编辑.env文件
vim config/.env

# 必需配置项：
# - DEEPSEEK_API_KEY（或 QWEN_API_KEY）
# - FEISHU_APP_ID 和 FEISHU_APP_SECRET
# - FEISHU_WEBHOOK_URL 和 FEISHU_WEBHOOK_SECRET
# - FEISHU_TABLE_ID
# - XHS_MCP_URL（默认 http://localhost:18060/mcp）
```

### 5. 启动小红书 MCP 服务（必需）

V2 版本依赖小红书 MCP 服务来搜索和发布内容。

```bash
# 详细步骤请参考 MCP_SETUP.md

# 简要步骤：
# 1. 安装小红书MCP工具
# 2. 启动MCP服务（默认端口 18060）
# 3. 使用浏览器登录小红书账号
# 4. 验证MCP服务状态
```

**重要**：MCP 服务必须在后台持续运行，否则无法发布内容。

### 6. 测试运行

```bash
# 确保MCP服务已启动
# 然后运行测试（--force 跳过时间检查）

# 指定城市测试
python3 src/scheduler_v2.py --city 杭州 --force

# 查看日志确认运行结果
tail -f logs/xhs_bot_$(date +%Y-%m-%d).log
```

### 7. 配置 Cron 定时任务

```bash
# 编辑crontab
crontab -e

# 添加以下行（每天9-11点之间每小时执行一次）
0 9-11 * * * cd /opt/xhs_travel_bot && /usr/bin/python3 src/scheduler_v2.py >> /var/log/xhs_bot_cron.log 2>&1

# 或者使用随机城市模式（不指定城市，系统自动选择）
0 9-11 * * * cd /opt/xhs_travel_bot && /usr/bin/python3 src/scheduler_v2.py >> /var/log/xhs_bot_cron.log 2>&1
```

**注意**：

- V2 版本会在 9:00-11:00 时间窗口内自动随机选择发布时间
- 如果不在时间窗口内，可以使用 `--force` 参数强制执行
- 确保 MCP 服务在 Cron 任务执行时处于运行状态

### 8. 查看日志

```bash
# 查看应用日志
tail -f logs/xhs_bot_$(date +%Y-%m-%d).log

# 查看Cron日志
tail -f /var/log/xhs_bot_cron.log

# 查看MCP服务日志
# （根据MCP服务的启动方式查看相应日志）
```

## 常见问题

### 1. 权限问题

```bash
# 确保日志目录可写
sudo mkdir -p /var/log/xhs_bot
sudo chown $USER:$USER /var/log/xhs_bot

# 或使用项目目录下的logs
mkdir -p /opt/xhs_travel_bot/logs
```

### 2. 网络问题

```bash
# 测试网络连接
curl -I https://api.deepseek.com
curl -I https://open.feishu.cn

# 测试MCP服务连接
curl http://localhost:18060/mcp

# 如需代理，在.env中添加
# HTTP_PROXY=http://proxy:port
# HTTPS_PROXY=http://proxy:port
```

### 3. MCP 服务问题

```bash
# 检查MCP服务是否运行
ps aux | grep mcp

# 检查MCP端口是否监听
netstat -tuln | grep 18060
# 或
lsof -i :18060

# 重启MCP服务
# （根据MCP服务的启动方式重启）

# 检查MCP登录状态
# 访问 http://localhost:18060 查看状态页面
```

### 4. 依赖安装失败

```bash
# 使用国内镜像
pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 如果遇到编译错误（如 Pillow），安装系统依赖
sudo apt install python3-dev libjpeg-dev zlib1g-dev
```

## 监控和维护

### 查看运行状态

```bash
# 查看最近的日志
tail -n 100 logs/xhs_bot_$(date +%Y-%m-%d).log

# 查看是否有错误
grep "ERROR" logs/xhs_bot_$(date +%Y-%m-%d).log
```

### 手动触发

```bash
# 直接运行（强制执行，不检查时间）
cd /opt/xhs_travel_bot
python3 src/scheduler_v2.py --city 杭州 --force

# 或使用随机城市
python3 src/scheduler_v2.py --force
```

### 停止服务

```bash
# 删除Cron任务
crontab -e
# 注释或删除相关行
```

## 安全建议

1. **保护.env 文件**

   ```bash
   chmod 600 config/.env
   ```

2. **定期备份配置**

   ```bash
   cp config/.env config/.env.backup
   ```

3. **监控日志大小**
   ```bash
   # 日志会自动滚动，保留30天
   # 可手动清理旧日志
   find logs/ -name "*.log" -mtime +30 -delete
   ```

## 升级

```bash
cd /opt/xhs_travel_bot
git pull
pip3 install -r requirements.txt --upgrade
```

## 卸载

```bash
# 删除Cron任务
crontab -e

# 删除代码
sudo rm -rf /opt/xhs_travel_bot

# 删除日志
sudo rm -rf /var/log/xhs_bot
```
