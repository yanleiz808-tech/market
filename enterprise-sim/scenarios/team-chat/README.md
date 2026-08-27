# 场景五：团队沟通（Mattermost，Teams 平替）

用 Mattermost 提供 Teams 的核心能力：**团队 / 频道 / 私聊 / 文件分享 / 机器人集成**。
用于模拟同事间沟通，以及"在聊天里分享文档"的协作方式。

## 能力对照（对标 Teams）

| Teams 概念 | Mattermost 对应 |
|---|---|
| 团队 Team | Team |
| 频道 Channel | Channel（公开/私有） |
| 私聊/群聊 | Direct / Group Message |
| 文件分享 | 附件上传 + 链接（推荐贴 Nextcloud 分享链接） |
| Bot / 连接器 | Incoming/Outgoing Webhook、Bot Account、Slash Command |

## 启动

```bash
cd enterprise-sim
cp .env.example .env
docker compose --profile chat up -d
```

访问 http://localhost:8065 ，首次创建管理员账号并新建团队（如「Acme 通信」）。

## Teams 文档 = SharePoint 的复刻

微软里 Teams 频道的文件其实存在 SharePoint。沙盒里复刻这个关系的做法：
**聊天用 Mattermost，文档统一放 Nextcloud（场景三）**，在频道里贴 Nextcloud 分享链接，
既模拟了"在 Teams 分享文档"，又保持文档单一来源。

## 建议的频道结构

```
团队「Acme 通信」
├── #供应链-采购         采购/供应商沟通
├── #供应链-仓储物流     出入库协调
├── #研发-5G基站         研发讨论
├── #测试-缺陷跟踪       测试与缺陷（对接 Redmine）
└── #质量-周报          质量数据与报告（对接 Metabase/PPT）
```

## 方式 A：脚本建团队 + 频道

```bash
cd enterprise-sim/scenarios/team-chat
pip install requests
MM_URL=http://localhost:8065 \
MM_TOKEN=你的PersonalAccessToken \
python3 seed_mattermost.py
```

获取 Token：*头像 → 个人设置 → 安全 → 个人访问令牌*（需管理员在
*系统控制台 → 集成 → 集成管理* 里先开启「个人访问令牌」）。

## AI 演练点（用 API 而非点 UI）

| AI 任务 | 接口 | 说明 |
|---|---|---|
| 发通知/播报 | Incoming Webhook / `POST /api/v4/posts` | 出库完成、测试失败、日报播报到频道 |
| 读频道消息 | `GET /api/v4/channels/{id}/posts` | 让 Agent 理解讨论上下文 |
| 建频道/邀人 | `POST /api/v4/channels` | 按项目自动开频道 |
| 分享文档 | 贴 Nextcloud 分享链接 | 模拟 Teams 文档分享 |

配合 n8n：Kiwi 测试失败 → n8n 在 `#测试-缺陷跟踪` 播报并 @负责人 → Redmine 开 Bug。
