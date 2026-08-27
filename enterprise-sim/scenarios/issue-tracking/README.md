# 场景四：问题跟踪 / 需求缺陷管理（Redmine，Jira 平替）

用 Redmine 提供 Jira 的核心能力：**创建与管理 Bug、Feature、Task 工单**，
支持状态流转、指派、版本(里程碑)、优先级、看板。用于研发测试部门的研发协作。

## 能力对照（对标 Jira）

| Jira 概念 | Redmine 对应 |
|---|---|
| Issue Type(Bug/Story/Task) | Tracker：开箱自带 **Bug / Feature / Support** |
| 工作流 Workflow | 状态(New→In Progress→Resolved→Closed)+ 角色工作流 |
| Sprint / 版本 | Version(目标版本，可当迭代/里程碑) |
| 看板 Board | Agile 插件的看板视图（可选安装） |
| 指派人 Assignee | Assignee / Watcher |
| Epic / 父子 | 父子任务(subtasks) |
| JQL 检索 | 自定义查询(过滤+分组+保存) |

## 启动

```bash
cd enterprise-sim
cp .env.example .env
docker compose --profile issues up -d
```

访问 http://localhost:8084 ，首次登录 **admin / admin**，系统会强制改密码。

## 首次配置（3 步）

1. **建项目**：*项目 → 新建项目*，例如「5G 基站研发」，勾选模块「问题跟踪」。
2. **开 REST API**（供 AI 调用）：*管理 → 设置 → API →* 勾选「启用 REST Web 服务」。
3. **拿 API Key**：右上角 *我的账号 →* 右侧「API 访问键」，复制备用。

> 工单类型 Bug/Feature/Support 默认就有；如需「用户故事/Epic」可在
> *管理 → 跟踪标签(Trackers)* 里自行增加。

## 方式 A：脚本建项目 + 灌 Bug/Feature 工单

```bash
cd enterprise-sim/scenarios/issue-tracking
pip install requests
REDMINE_URL=http://localhost:8084 \
REDMINE_API_KEY=你的APIKey \
python3 seed_redmine.py
```

脚本会（若项目不存在则创建）灌入几条示例工单：2 个 Feature + 3 个 Bug，
并设置优先级，方便演练看板与统计。

## 方式 B：UI 手动建工单

*项目 → 问题 → 新建问题*：选跟踪标签(Bug/Feature)、填主题与描述、选优先级、
指派、目标版本 → 保存。之后可在「问题」列表按类型/状态过滤，或装 Agile 插件看看板。

## AI 演练点（用 API 而非点 UI）

Redmine REST API 简单稳定，均返回/接受 JSON：

| AI 任务 | 接口 | 说明 |
|---|---|---|
| 创建 Bug/Feature | `POST /issues.json` | 从需求/测试失败自动开单 |
| 更新状态/指派 | `PUT /issues/{id}.json` | 流转、分配、加备注 |
| 查询/统计 | `GET /issues.json?...` | 按类型/状态/优先级统计，出质量报表 |
| 关联版本 | `GET /projects/{id}/versions.json` | 规划迭代、按里程碑归集 |
| 类型清单 | `GET /trackers.json` | 获取 Bug/Feature 的 tracker id |

认证：HTTP 头 `X-Redmine-API-Key: <key>`，或 URL 参数 `?key=<key>`。

## 与其他场景的联动（配合 n8n）

- 场景二 Kiwi 测试用例 **FAILED** → n8n 自动在 Redmine `POST /issues.json` 开一个 **Bug**，
  带上用例名、构建号、失败详情。
- 修复合入 Gitea 后 → 关闭对应 Bug → 通知 Kiwi 复测。
- AI 汇总 Redmine 的 Bug 趋势 + Kiwi 通过率 → 生成研发质量周报存入 Nextcloud。

把这些包成 MCP 工具（如 `create_bug`、`update_issue`、`quality_stats`），
Agent 就能端到端跑「测试失败 → 开单 → 修复 → 复测 → 报表」的缺陷闭环。
