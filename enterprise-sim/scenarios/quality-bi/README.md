# 场景七：质量 BI 报表（Metabase，Power BI 平替）

用 Metabase 提供 Power BI 的核心能力：**连接业务库、拖拽出图、做质量仪表盘**。
用于模拟"登录 BI 获取 quality 数据 → 再做 PPT 质量报告"这一步。

## 能力对照（对标 Power BI）

| Power BI 概念 | Metabase 对应 |
|---|---|
| 数据源连接 | Database 连接（Postgres/MySQL 等） |
| 数据集/查询 | Question（可视化查询，含 SQL 模式） |
| 报表/仪表板 | Dashboard |
| 定时刷新/订阅 | Subscription（定时邮件推送，可接场景六邮件） |
| DAX/度量 | SQL / 自定义字段 |

## 启动

```bash
cd enterprise-sim
cp .env.example .env
docker compose --profile bi up -d
```

访问 http://localhost:3002 ，首次创建管理员账号。初始化约 1–2 分钟。

## 连接业务数据库（拿 quality 数据）

Metabase 通过内网直接连其它服务的数据库。*管理设置 → 数据库 → 添加数据库*：

| 数据源 | 类型 | Host | 端口 | 库名 | 用户 | 说明 |
|---|---|---|---|---|---|---|
| 缺陷数据(Redmine) | PostgreSQL | `redmine-db` | 5432 | redmine | redmine | Bug/Feature 统计 |
| 测试数据(Kiwi) | MySQL/MariaDB | `kiwi-db` | 3306 | kiwi | kiwi | 用例/执行/通过率 |
| 供应链(Odoo) | PostgreSQL | `odoo-db` | 5432 | acme | odoo | 库存/订单 |

> Host 用容器服务名（如 `redmine-db`）而非 localhost —— Metabase 和这些库在同一
> compose 网络里。密码用 `.env` 里对应的值。启动对应 profile 后这些库才存在。

## 建质量仪表盘（示例）

1. **测试通过率趋势**：连 Kiwi 库，按构建统计 PASSED/总数。
2. **缺陷分布**：连 Redmine 库，按 tracker(Bug/Feature)、状态、优先级分组。
3. **缺陷闭环时长**：Redmine 工单 created→closed 的平均天数。
4. 把上面几个 Question 拖进一个 **Dashboard**「研发质量看板」。

## 到 PPT 质量报告这一步

Metabase 出图后，做 PPT 报告有两条路：
- **手动**：Dashboard 里每个图可导出 PNG/CSV，贴进 PowerPoint。
- **AI 自动**：让 Agent 通过 Metabase API 拉数据，再用本仓库可用的 **pptx 技能**
  自动生成质量报告 PPT（这正是"AI 工作场景"的一环）。

## AI 演练点

| AI 任务 | 接口 | 说明 |
|---|---|---|
| 拉取图表数据 | `POST /api/card/{id}/query/json` | 取某个 Question 的结果做报告 |
| 读仪表盘 | `GET /api/dashboard/{id}` | 汇总多个指标 |
| 定时订阅 | Dashboard Subscription | 定时把质量看板邮件推送给同事（接场景六） |

认证：登录拿 `X-Metabase-Session`，或用管理端创建的 API Key。
