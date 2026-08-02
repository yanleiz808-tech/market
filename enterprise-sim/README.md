# 企业模拟环境（供应链 + 研发测试）—— AI 工作场景沙盒

一套可自托管、API 优先的开源工具组合，用来模拟一家虚拟公司的**供应链部门**与
**研发测试部门**的日常工作，供 AI Agent / MCP 进行读写操作与端到端场景演练。

## 1. 架构总览

```
                         ┌──────────────────────────┐
                         │        n8n (glue)        │  ← AI Agent 的编排入口
                         │  跨部门 Webhook / 自动化   │
                         └───┬───────────┬───────┬───┘
             供应链部门        │           │       │        研发测试部门
        ┌───────────────┐     │           │       │   ┌──────────────────┐
        │  Odoo 17 CE   │◄────┘           │       └──►│   Kiwi TCMS      │
        │ 采购/库存/MRP  │  JSON-RPC       │  REST     │ 测试用例/计划/执行 │
        └───────────────┘                 │           └──────────────────┘
                                          ▼
                               ┌──────────────────┐   ┌──────────────┐
                               │   OpenProject    │   │    Gitea     │
                               │  项目/工单/甘特   │   │ 代码托管/CI  │
                               └──────────────────┘   └──────────────┘
```

## 2. 服务清单与访问入口

| Profile | 服务 | 部门/职能 | 地址 | API |
|---|---|---|---|---|
| `erp`  | Odoo 17 CE  | 供应链：采购/库存/制造 | http://localhost:8069 | JSON-RPC `/jsonrpc` |
| `test` | Kiwi TCMS   | 研发测试：测试管理 | https://localhost:8444 | JSON-RPC `/json-rpc/` |
| `pm`   | OpenProject | 项目管理 | http://localhost:8082 | REST `/api/v3` |
| `rnd`  | Gitea       | 研发：代码托管 | http://localhost:3000 | REST `/api/v1` |
| `glue` | n8n         | 自动化编排 | http://localhost:5678 | Webhook |

> 硬件建议：全量启动约需 **6–8GB 内存**。资源有限时按 profile 启动子集。

## 3. 快速开始

```bash
cd enterprise-sim
cp .env.example .env          # 按需修改密码

# 按需启动（profile 可组合）
docker compose --profile erp --profile test up -d
# 或全部启动
docker compose --profile all up -d

docker compose ps            # 查看状态
docker compose logs -f odoo  # 看某个服务日志
```

停止 / 清理：

```bash
docker compose --profile all down          # 停止（保留数据卷）
docker compose --profile all down -v       # 停止并删除所有数据
```

## 4. 各服务首次初始化

### Odoo（供应链）
1. 打开 http://localhost:8069 ，创建数据库（记住 master password）。
2. 安装模块：**采购(Purchase)**、**库存(Inventory)**、**制造(Manufacturing/MRP)**、
   **销售(Sales)** —— 这几个模块共同构成完整供应链链路。
3. API 示例（Python，`xmlrpc`）：见 `seed/README.md`。

### Kiwi TCMS（测试管理）
首次需要建库并创建超级用户：
```bash
docker compose exec kiwi /Kiwi/manage.py migrate
docker compose exec kiwi /Kiwi/manage.py createsuperuser
```
然后访问 https://localhost:8444 （自签名证书，忽略浏览器安全警告）。

### OpenProject（项目管理）
- 首次登录 `admin` / `admin`，系统会强制改密码。
- 在 *我的账户 → 访问令牌* 生成 API token 供 AI 调用。

### Gitea（代码托管）
- 首次访问 http://localhost:3000 完成安装向导，数据库选 **SQLite3**（已在环境变量预设）。
- 在 *设置 → 应用 → 生成令牌* 创建 API token。

### n8n（编排）
- 直接访问 http://localhost:5678 创建管理员账号。
- 用 HTTP Request / Webhook 节点连接上面各服务的 API，即可搭建跨部门自动化。

## 5. 面向 AI 的接入方式

模拟 AI 工作场景的关键是让 Agent **通过 API 读写**，而不是点 UI：

- **直接 REST/RPC**：每个服务都有开放 API + Token 认证，Agent 可直接调用。
- **MCP 封装（推荐）**：为常用操作写一层薄 MCP Server（如 `create_purchase_order`、
  `run_test_plan`、`create_work_package`），让 Agent 以工具形式调用，语义更清晰。
- **n8n 作为编排层**：把「测试失败 → Odoo 建质量异常单 → OpenProject 建修复工单 →
  通知」这类多系统流程做成 workflow，AI 只需触发一个 webhook。

## 6. 建议的模拟场景

| 场景 | 涉及系统 | AI 演练点 |
|---|---|---|
| 采购补货 | Odoo | 读库存 → 判断安全库存 → 生成采购订单 |
| 缺料预警 | Odoo + n8n | MRP 缺料 → 自动通知 + 建工单 |
| 需求到测试 | OpenProject + Kiwi | 需求工单 → 生成测试计划与用例 → 回填结果 |
| 缺陷闭环 | Gitea + Kiwi + OpenProject | 测试失败 → 建 issue → 建修复任务 → 复测 |
| 跨部门报表 | 全部 | 汇总库存/项目/测试通过率生成周报 |

> `seed/` 目录存放种子数据脚本与说明，用于快速灌入一家虚拟公司的基础数据。

## 7. 可直接运行的场景

`scenarios/` 下提供两个端到端、可脚本一键跑通的业务场景：

| 场景 | 部门 | 系统 | 链路 |
|---|---|---|---|
| [库存管理 + 拣货出库](scenarios/inventory-fulfillment/README.md) | 供应链 | Odoo | 销售单 → 确认 → 出库单 → 预留 → 拣货 → 出库扣库存 |
| [通信测试部门](scenarios/telecom-testing/README.md) | 研发测试 | Kiwi TCMS | 测试计划 → 用例定义 → 评审 → 执行 → 统计报表 |

每个场景目录内含一个幂等种子脚本（`seed_*.py`）和一份业务流程说明（UI 步骤 + AI/API 演练点）。
