# 定时任务设置指南

## 📋 概述

本系统通过**外部定时任务**控制随机发布时间，代码本身不做时间检查。

---

## 🎯 阿里云定时任务设置

### 方式 1：使用阿里云定时任务界面

#### 1. 基本配置

- **定时执行方式**：选择 `基于时钟的 Cron表达式`
- **Cron 表达式**：`0 0 8 * * ?`（每天 8:00 触发）
- **时区**：`(GMT+08:00) Asia/Shanghai`

#### 2. 命令内容（Shell 标签页）

```bash
# 随机等待 0-120 分钟（0-7200 秒）
sleep $((RANDOM % 7200))

# 执行发布脚本
cd /root/sal/xhs_travel_bot && ./start_scheduler.sh >> logs/cron.log 2>&1
```

#### 3. 工作流程

1. ⏰ 每天 8:00 触发
2. 🎲 随机等待 0-120 分钟（8:00-10:00）
3. 🚀 执行发布脚本
4. ✅ 发布完成，记录日志

---

### 方式 2：使用系统 crontab

```bash
# 编辑 crontab
crontab -e

# 添加以下内容
0 8 * * * sleep $((RANDOM % 7200)) && cd /root/sal/xhs_travel_bot && ./start_scheduler.sh >> /root/sal/xhs_travel_bot/logs/cron.log 2>&1

# 保存退出
# - vim: 按 ESC，输入 :wq，回车
# - nano: 按 Ctrl+X，按 Y，回车

# 查看设置
crontab -l
```

---

## 🧪 本地测试

### 1. 测试发布（不实际发布）

```bash
cd ~/sal/xhs_travel_bot
./start_scheduler.sh --test
```

### 2. 立即发布（真实发布）

```bash
./start_scheduler.sh
```

### 3. 查看帮助

```bash
./start_scheduler.sh --help
```

---

## 📊 查看日志

### 查看定时任务日志

```bash
# 查看最近 100 行
tail -100 ~/sal/xhs_travel_bot/logs/cron.log

# 实时查看
tail -f ~/sal/xhs_travel_bot/logs/cron.log
```

### 查看应用日志

```bash
# 查看今天的日志
tail -100 ~/sal/xhs_travel_bot/logs/xhs_bot_$(date +%Y-%m-%d).log

# 实时查看
tail -f ~/sal/xhs_travel_bot/logs/xhs_bot_$(date +%Y-%m-%d).log
```

---

## ⚙️ MCP 服务管理

### 启动 MCP 服务

```bash
cd ~/sal/xhs_travel_bot/xiaohongshu-mcp-main
nohup go run . server --addr 0.0.0.0:18060 --headless=true --bin /usr/bin/google-chrome-stable > mcp.log 2>&1 &
```

### 检查 MCP 服务状态

```bash
ps aux | grep xiaohongshu-mcp | grep -v grep
```

### 查看 MCP 日志

```bash
tail -50 ~/sal/xhs_travel_bot/xiaohongshu-mcp-main/mcp.log
```

### 重启 MCP 服务

```bash
# 停止
pkill -f "go run"

# 启动
cd ~/sal/xhs_travel_bot/xiaohongshu-mcp-main
nohup go run . server --addr 0.0.0.0:18060 --headless=true --bin /usr/bin/google-chrome-stable > mcp.log 2>&1 &
```

---

## 🔐 登录管理

### 检查登录状态

```bash
cd ~/sal/xhs_travel_bot
source venv/bin/activate
python3 tools/check_login.py
```

### 获取登录二维码

```bash
python3 test_qrcode.py
```

---

## 🐛 故障排查

### 1. 定时任务未执行

```bash
# 检查 crontab 是否设置
crontab -l

# 检查 cron 服务
systemctl status cron
```

### 2. 发布失败

```bash
# 查看错误日志
tail -50 ~/sal/xhs_travel_bot/logs/cron.log

# 检查 MCP 服务
ps aux | grep xiaohongshu-mcp

# 检查登录状态
python3 tools/check_login.py
```

### 3. MCP 服务异常

```bash
# 查看 MCP 日志
tail -50 ~/sal/xhs_travel_bot/xiaohongshu-mcp-main/mcp.log

# 重启 MCP 服务
pkill -f "go run"
cd ~/sal/xhs_travel_bot/xiaohongshu-mcp-main
nohup go run . server --addr 0.0.0.0:18060 --headless=true --bin /usr/bin/google-chrome-stable > mcp.log 2>&1 &
```

---

## 📞 技术支持

如有问题，请查看：

1. 应用日志：`logs/xhs_bot_*.log`
2. 定时任务日志：`logs/cron.log`
3. MCP 服务日志：`xiaohongshu-mcp-main/mcp.log`
