# 场景六：企业邮件（docker-mailserver + Roundcube，Outlook 平替）

提供 Outlook 的核心能力：**真·多账号邮箱，浏览器收发邮件**。用于模拟"给同事写邮件"，
以及 AI 通过标准 IMAP/SMTP 收发邮件。

## 能力对照（对标 Outlook / Exchange）

| Outlook 概念 | 本方案对应 |
|---|---|
| Exchange 邮箱服务器 | docker-mailserver（SMTP/IMAP） |
| Outlook 客户端 / OWA | Roundcube 网页邮箱（http://localhost:8086） |
| 邮箱账号 | 用 setup 命令创建的 `user@corp.local` |
| 收/发信协议 | IMAP(10143) / SMTP(10587)，供 AI 接入 |

> 说明：这是所有服务里**配置最重**的一个（邮件涉及域名与账号）。本地模拟已关闭 TLS
> 以降低复杂度；仅用于沙盒，切勿用于真实收发。

## 启动

```bash
cd enterprise-sim
cp .env.example .env
docker compose --profile mail up -d
```

## 创建邮箱账号（关键步骤）

邮件服务器没有默认账号，需手动创建。用内置 setup 命令：

```bash
# 建两个"同事"账号（域名 corp.local 为本地模拟域）
docker compose exec mailserver setup email add zhang@corp.local Passw0rd!
docker compose exec mailserver setup email add li@corp.local   Passw0rd!

# 查看已有账号
docker compose exec mailserver setup email list
```

## 登录网页邮箱（像 Outlook Web）

1. 打开 http://localhost:8086
2. 用户名填完整邮箱 `zhang@corp.local`，密码 `Passw0rd!`
3. 即可给 `li@corp.local` 写邮件，对方登录后能收到——模拟同事间往来。

## AI 演练点（标准协议，AI 好接）

| AI 任务 | 协议/接口 | 说明 |
|---|---|---|
| 发邮件 | SMTP `localhost:10587` | AI 自动发通知/周报给同事 |
| 读邮件 | IMAP `localhost:10143` | AI 读取收件箱、解析请求 |
| 自动回复 | IMAP 读 + SMTP 回 | 模拟邮件助理 |

Python 示例（发信）：

```python
import smtplib
from email.mime.text import MIMEText
msg = MIMEText("本周质量周报已生成，请查收。", _charset="utf-8")
msg["Subject"] = "质量周报 W35"
msg["From"] = "zhang@corp.local"
msg["To"] = "li@corp.local"
s = smtplib.SMTP("localhost", 10587)
s.login("zhang@corp.local", "Passw0rd!")
s.send_message(msg); s.quit()
```

## 与其他场景联动（配合 n8n）

- 出库完成 / 测试失败 / 质量周报 → n8n 通过 SMTP 自动发邮件通知相关同事。
- AI 定期扫收件箱，把邮件里的需求转成 Redmine 工单或 Kiwi 用例。

## 常见问题

- Roundcube 登录报连接错误：确认 `mailserver` 容器已就绪（首次启动稍慢），
  且账号已用 setup 命令创建。
- 想要更简单的"只收不发/纯测试"邮件：可改用 Mailpit（catch-all，带 Web+API），
  但那是共享收件箱、非多账号，不如本方案贴近 Outlook。
