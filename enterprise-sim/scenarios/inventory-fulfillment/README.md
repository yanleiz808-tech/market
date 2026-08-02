# 场景一：库存管理 + 销售订单拣货出库（Odoo）

模拟供应链/仓储部门最核心的一条正向流程：**下单 → 备货 → 拣货 → 出库 → 扣库存**。

## 业务流程

```
销售订单(SO)  ──确认──►  出库单(Delivery)  ──预留──►  拣货(填完成数量)  ──校验──►  出库完成
   draft            confirmed        reserved(assigned)      picked            done
                                                                              └─► 库存自动扣减
```

对应 Odoo 模型：`sale.order` → `stock.picking`（出库类型）→ `stock.move` / `stock.move.line`
→ `stock.quant`（库存账）。

## 前置：安装模块

进入 http://localhost:8069 ，在 *应用(Apps)* 里安装：
- **库存 Inventory**（提供仓库、出库单、拣货、库存调整）
- **销售 Sales**（提供销售订单，确认后自动生成出库单）

## 方式 A：脚本一键灌数并跑通链路

```bash
cd enterprise-sim/scenarios/inventory-fulfillment
ODOO_URL=http://localhost:8069 ODOO_DB=acme \
ODOO_USER=admin ODOO_PASSWORD=admin \
python3 seed_odoo.py
```

脚本会：建 3 个可库存产品 → 调整初始库存 → 建客户 → 下销售单 → 确认生成出库单
→ 预留 → 填拣货数量 → 校验出库。执行完到 *库存 → 出库* 里能看到一张 Done 的出库单。

> **注意**：`button_validate`（出库校验）在不同 Odoo 小版本上，收尾可能弹「欠单确认」
> 等向导。脚本按「全量出库」处理以尽量避免欠单；若最后一步返回的是向导而非 `True`，
> 到 UI 里对该出库单点一下 **Validate** 即可完成（业务数据已就绪）。

## 方式 B：纯 UI 手动走一遍（最稳，也便于理解流程）

1. *销售 → 订单 → 新建*：选客户、加两行产品与数量 → **确认**。
2. 订单右上角出现 **Delivery** 智能按钮，点进去（即出库单）。
3. 出库单点 **Check Availability**（预留库存）。
4. 在明细里把 **Done** 数量填成需求数量（模拟拣货）。
5. 点 **Validate** → 出库完成，产品 *库存数量* 相应减少。

## AI 演练点（用 API 而非点 UI）

| AI 任务 | 涉及模型/接口 | 说明 |
|---|---|---|
| 安全库存补货判断 | `stock.quant` 读现有量 | 低于阈值时自动建采购/调拨 |
| 自动确认可发货订单 | `sale.order.action_confirm` | 库存充足则确认并生成出库单 |
| 智能拣货填数 | `stock.move.line.write(quantity, picked)` | 按可用库存分配、拆分欠单 |
| 出库异常处理 | `button_validate` 返回向导 | 识别欠单/缺料并决策 |
| 库存与发货日报 | `stock.quant` / `stock.picking` 聚合 | 生成周转率、及时出库率 |

XML-RPC 调用范式见 `seed_odoo.py` 里的 `x()` 辅助函数；把这些操作包一层 MCP
工具（如 `check_stock`、`confirm_sales_order`、`validate_delivery`），即可让
Agent 以工具形式驱动整条链路。
