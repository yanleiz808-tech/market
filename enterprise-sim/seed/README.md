# 种子数据（虚拟公司 "Acme 制造"）

给沙盒灌入一批基础数据，让 AI 场景更真实。以下为最小示例，可按需扩展成脚本。

## Odoo：通过 XML-RPC 创建供应商与产品

```python
import xmlrpc.client

url, db = "http://localhost:8069", "acme"      # db 为你创建的数据库名
username, password = "admin", "admin"

common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")

def create(model, vals):
    return models.execute_kw(db, uid, password, model, "create", [vals])

# 供应商
vendor = create("res.partner", {"name": "深圳元件供应商", "supplier_rank": 1})

# 可采购+可库存的产品
product = create("product.template", {
    "name": "主控板 PCBA-100",
    "type": "product",          # 可库存
    "purchase_ok": True,
    "list_price": 120.0,
    "standard_price": 80.0,
})

print("vendor:", vendor, "product:", product)
```

## OpenProject：通过 REST v3 创建工单

```bash
curl -u apikey:<YOUR_TOKEN> -X POST \
  http://localhost:8082/api/v3/projects/<project_id>/work_packages \
  -H "Content-Type: application/json" \
  -d '{"subject":"新品导入测试","_links":{"type":{"href":"/api/v3/types/1"}}}'
```

## Kiwi TCMS：通过 JSON-RPC 建测试计划

```python
from tcms_api import TCMS   # pip install tcms-api
rpc = TCMS("https://localhost:8444/json-rpc/", "admin", "<password>").exec
plan = rpc.TestPlan.create({
    "name": "PCBA-100 出厂测试",
    "product": 1, "product_version": 1, "type": 1, "is_active": True,
})
print(plan)
```

## Gitea：通过 REST 建仓库

```bash
curl -X POST http://localhost:3000/api/v1/user/repos \
  -H "Authorization: token <YOUR_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"name":"pcba-firmware","private":false,"auto_init":true}'
```

> 建议把上述调用整理成一个 `seed.py` 幂等脚本（先查后建），便于反复重置沙盒。
