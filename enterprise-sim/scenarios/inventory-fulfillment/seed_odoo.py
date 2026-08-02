#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
供应链场景种子脚本：库存管理 + 销售订单 → 拣货 → 出库

在 Odoo 中构建一条可演练的完整链路：
  建产品 → 调整库存 → 建客户 → 下销售单 → 确认(生成出库单/Delivery)
  → 预留(reserve) → 拣货填数 → 出库校验(validate) → 库存扣减

依赖：Python 标准库 xmlrpc（无需 pip）。
配置：通过环境变量覆盖，默认对接本地 compose 里的 Odoo。

  ODOO_URL=http://localhost:8069 ODOO_DB=acme \
  ODOO_USER=admin ODOO_PASSWORD=admin python3 seed_odoo.py

脚本为「幂等」：先查后建，可反复执行。button_validate 的收尾在不同
Odoo 小版本上行为略有差异（见 README 的「注意」），若出库校验未自动完成，
按 README 的 UI 步骤点一下 Validate 即可。
"""
import os
import sys
import xmlrpc.client

URL = os.environ.get("ODOO_URL", "http://localhost:8069")
DB = os.environ.get("ODOO_DB", "acme")
USER = os.environ.get("ODOO_USER", "admin")
PASSWORD = os.environ.get("ODOO_PASSWORD", "admin")

common = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common")
uid = common.authenticate(DB, USER, PASSWORD, {})
if not uid:
    sys.exit(f"认证失败：请检查 ODOO_DB={DB} / 账号密码，以及数据库是否已创建。")
models = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object")


def x(model, method, *args, **kw):
    return models.execute_kw(DB, uid, PASSWORD, model, method, list(args), kw)


def get_or_create(model, domain, vals):
    ids = x(model, "search", domain, limit=1)
    if ids:
        return ids[0]
    return x(model, "create", vals)


def main():
    # 1) 主仓库存放位置（Odoo 安装库存模块后默认自带 WH/Stock）
    wh = x("stock.warehouse", "search_read", [], fields=["lot_stock_id", "name"], limit=1)
    if not wh:
        sys.exit("未找到仓库：请先在 Odoo 里安装 Inventory(库存) 模块。")
    stock_loc = wh[0]["lot_stock_id"][0]
    print(f"仓库：{wh[0]['name']}  库存位置 id={stock_loc}")

    # 2) 可库存产品（type=product 表示可跟踪库存数量）
    products = [
        ("SFP-10G 光模块", 50.0, 30.0, 200),
        ("千兆交换机 SW-24", 800.0, 600.0, 40),
        ("网线 Cat6 (箱)", 120.0, 80.0, 150),
    ]
    product_ids = []
    for name, price, cost, qty in products:
        pid = get_or_create(
            "product.product",
            [["name", "=", name]],
            {"name": name, "type": "product", "list_price": price,
             "standard_price": cost, "sale_ok": True, "purchase_ok": True},
        )
        product_ids.append((pid, name, qty))
        # 3) 库存调整：写入盘点数量并应用
        quant = x("stock.quant", "create",
                  {"product_id": pid, "location_id": stock_loc, "inventory_quantity": float(qty)})
        try:
            x("stock.quant", "action_apply_inventory", [quant])
        except Exception as e:  # 某些版本命名不同，忽略即可，可在 UI 手动应用
            print(f"  ! 库存应用提示（{name}）：{e}")
        print(f"产品：{name}  id={pid}  初始库存={qty}")

    # 4) 客户
    customer = get_or_create(
        "res.partner",
        [["name", "=", "华东电信集成商"]],
        {"name": "华东电信集成商", "customer_rank": 1,
         "street": "上海市浦东新区", "phone": "021-88886666"},
    )
    print(f"客户 id={customer}")

    # 5) 销售订单（拿前两个产品各下若干）
    order_lines = [
        (0, 0, {"product_id": product_ids[0][0], "product_uom_qty": 20}),
        (0, 0, {"product_id": product_ids[1][0], "product_uom_qty": 5}),
    ]
    so = x("sale.order", "create", {"partner_id": customer, "order_line": order_lines})
    print(f"销售订单 id={so}（草稿）")

    # 6) 确认订单 → 自动生成出库单(Delivery/stock.picking)
    x("sale.order", "action_confirm", [so])
    so_read = x("sale.order", "read", [so], fields=["name", "picking_ids"])
    print(f"已确认：{so_read[0]['name']}  出库单 picking_ids={so_read[0]['picking_ids']}")
    if not so_read[0]["picking_ids"]:
        print("未生成出库单（检查库存路线/仓库配置）。")
        return
    pick = so_read[0]["picking_ids"][0]

    # 7) 预留库存（reserve）
    x("stock.picking", "action_assign", [pick])

    # 8) 拣货：把每条明细的完成数量填满（全量出库，避免产生欠单 backorder）
    moves = x("stock.move", "search_read", [["picking_id", "=", pick]],
              fields=["id", "product_uom_qty"])
    for mv in moves:
        mls = x("stock.move.line", "search", [["move_id", "=", mv["id"]]])
        if mls:
            # Odoo 17 中 stock.move.line 的完成数量字段为 quantity，并需 picked=True
            for ml in mls:
                x("stock.move.line", "write", [ml],
                  {"quantity": mv["product_uom_qty"], "picked": True})
        else:
            x("stock.move.line", "create",
              {"move_id": mv["id"], "picking_id": pick,
               "quantity": mv["product_uom_qty"], "picked": True})

    # 9) 出库校验（validate）→ 完成出库、扣减库存
    res = x("stock.picking", "button_validate", [pick])
    if res is True:
        print(f"出库单 id={pick} 已校验完成，库存已扣减。")
    else:
        # 返回的是向导（如欠单确认），在 UI 里点 Validate/Apply 即可收尾
        print(f"出库单 id={pick} 需在 UI 手动点 Validate 收尾（返回：{res}）。")

    print("\n完成。到 http://localhost:8069 的 库存/销售 模块查看该链路。")


if __name__ == "__main__":
    main()
