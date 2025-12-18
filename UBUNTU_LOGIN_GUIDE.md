# Ubuntu 无显示器环境登录指南

## 问题背景

在 Ubuntu 服务器等无显示器环境下，无法直接通过浏览器访问 `http://localhost:18060` 来扫码登录小红书。

## 解决方案

### 方案 1：使用登录辅助工具（推荐）⭐

我们提供了专门的登录辅助工具 `tools/login_helper.py`，可以自动调用小红书 MCP 的 `get_login_qrcode` 工具获取登录二维码。

#### 使用步骤

**1. 在服务器上运行登录辅助工具**

```bash
cd /opt/xhs_travel_bot
source venv/bin/activate
python tools/login_helper.py
```

**2. 工具会自动执行以下操作**

- ✅ 检查当前登录状态
- ✅ 调用 `get_login_qrcode` 获取二维码
- ✅ 将二维码保存为 `login_qrcode.png`
- ✅ 提供后续步骤指引

**3. 下载二维码到本地**

```bash
# 在本地电脑执行
scp user@server-ip:/opt/xhs_travel_bot/login_qrcode.png .
```

**4. 使用小红书 App 扫描二维码**

- 打开小红书 App
- 扫描下载的二维码图片
- 确认登录

**5. 验证登录状态**

```bash
# 在服务器上再次运行登录辅助工具
python tools/login_helper.py
```

如果显示 "✅ 已登录！"，说明登录成功。

---

### 方案 2：使用 SSH 隧道

如果 MCP 服务不支持 `get_login_qrcode` 工具，可以使用 SSH 隧道。

#### 使用步骤

**1. 在本地电脑建立 SSH 隧道**

```bash
ssh -L 18060:localhost:18060 user@server-ip
```

保持这个 SSH 连接不要断开。

**2. 在本地浏览器访问**

```
http://localhost:18060
```

**3. 扫码登录**

使用小红书 App 扫描浏览器中的二维码。

**4. 登录成功后**

可以断开 SSH 隧道，登录状态会保持在服务器上。

---

### 方案 3：临时开放端口（不推荐）

⚠️ **安全警告**：此方法会暴露 MCP 服务端口，仅在必要时使用，登录后立即关闭端口。

```bash
# 1. 开放端口
sudo ufw allow 18060

# 2. 在浏览器访问
# http://server-ip:18060

# 3. 扫码登录

# 4. 登录后立即关闭端口
sudo ufw delete allow 18060
```

---

## 技术实现

### MCP 工具：get_login_qrcode

小红书 MCP 服务提供了 `get_login_qrcode` 工具，专门用于无显示器环境获取登录二维码。

**工具参数**：

- 无参数（或可选的保存路径参数）

**返回值**：

- `qrcode` / `qr_code` / `image`: 二维码数据（base64 编码或 URL）
- 其他登录相关信息

### Python 实现

在 `src/services/xhs_mcp_client.py` 中实现了 `get_login_qrcode` 方法：

```python
async def get_login_qrcode(self, save_path: str = None) -> Dict:
    """
    获取登录二维码（用于无显示器环境）

    Args:
        save_path: 二维码保存路径

    Returns:
        包含二维码信息的字典
    """
    tool = self._get_tool("get_login_qrcode")
    result = await tool.ainvoke({})

    # 如果指定了保存路径，保存二维码图片
    if save_path:
        # 解析base64编码的二维码
        # 保存为PNG文件
        ...

    return result
```

### 登录辅助工具

`tools/login_helper.py` 是一个命令行工具，封装了登录流程：

```python
# 1. 检查登录状态
status = await client.check_login_status()

# 2. 如果未登录，获取二维码
if not is_logged_in:
    result = await client.get_login_qrcode(save_path="login_qrcode.png")

# 3. 提供后续步骤指引
print("下载二维码: scp user@server:login_qrcode.png .")
```

---

## 常见问题

### Q1: MCP 服务不支持 get_login_qrcode 怎么办？

**A**: 使用 SSH 隧道方案（方案 2）。

### Q2: 二维码过期了怎么办？

**A**: 重新运行登录辅助工具生成新的二维码：

```bash
python tools/login_helper.py
```

### Q3: 登录后需要保持 MCP 服务运行吗？

**A**: 是的，MCP 服务必须持续运行才能发布内容。建议使用 systemd 配置开机自启。

### Q4: 如何验证登录状态？

**A**: 运行登录辅助工具：

```bash
python tools/login_helper.py
```

或手动检查：

```bash
python -c "
import asyncio
from src.services.xhs_mcp_client import XhsMcpClient

async def check():
    client = XhsMcpClient()
    status = await client.check_login_status()
    print('登录状态:', status)

asyncio.run(check())
"
```

### Q5: 登录会话会过期吗？

**A**: 会的。如果长时间未使用，可能需要重新登录。定期运行登录辅助工具检查状态。

---

## 完整部署流程（Ubuntu）

```bash
# 1. 安装依赖
sudo apt install python3 python3-pip python3-venv nodejs -y

# 2. 部署应用
cd /opt/xhs_travel_bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. 配置环境变量
cp config/env.example config/.env
vim config/.env  # 填写API密钥

# 4. 启动MCP服务（使用systemd）
sudo systemctl start xhs-mcp

# 5. 登录小红书（使用登录辅助工具）
python tools/login_helper.py
# 下载二维码，扫码登录

# 6. 验证登录
python tools/login_helper.py

# 7. 测试发布
python src/scheduler_v2.py --city 杭州 --force

# 8. 配置定时任务
crontab -e
# 添加: 0 9-11 * * * cd /opt/xhs_travel_bot && venv/bin/python3 src/scheduler_v2.py >> /var/log/xhs_bot.log 2>&1
```

---

## 相关文档

- **完整部署指南**: `deploy/UBUNTU_DEPLOY.md`
- **MCP 服务配置**: `MCP_SETUP.md`
- **项目说明**: `README.md`

---

**更新时间**: 2025-12-17  
**适用版本**: V2 Pure Mode
