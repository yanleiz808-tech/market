#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通信产业测试部门场景种子脚本：测试计划 → 用例定义 → 评审 → 执行 → 统计

在 Kiwi TCMS 中构建一个「5G 基站(gNodeB)」的测试项目：
  建产品/版本/构建 → 建测试计划 → 定义测试用例(含步骤)
  → 评审(PROPOSED → CONFIRMED) → 建测试运行并加入用例
  → 回填执行结果(PASS/FAIL/...) → 汇总通过率统计

依赖：requests（pip install requests）。使用原生 JSON-RPC，自签名证书已跳过校验。
配置（环境变量）：
  KIWI_URL=https://localhost:8444/json-rpc/ \
  KIWI_USER=admin KIWI_PASSWORD=你的密码 python3 seed_kiwi.py

说明：Kiwi 的「评审」用用例状态 PROPOSED→CONFIRMED 表达；此脚本创建用例后
将其置为 CONFIRMED 以模拟评审通过。各类枚举 id（状态/优先级）通过 *.filter
按名称查找，尽量避免硬编码；个别方法名随版本略有差异，报错时以 README 的 UI
步骤为准。
"""
import os
import sys

try:
    import requests
except ImportError:
    sys.exit("请先安装依赖：pip install requests")
import urllib3
urllib3.disable_warnings()

URL = os.environ.get("KIWI_URL", "https://localhost:8444/json-rpc/")
USER = os.environ.get("KIWI_USER", "admin")
PASSWORD = os.environ.get("KIWI_PASSWORD", "")
if not PASSWORD:
    sys.exit("请通过环境变量 KIWI_PASSWORD 提供 admin 密码（见 README「Kiwi 初始化」）。")

S = requests.Session()
S.verify = False
_id = 0


def call(method, *params):
    global _id
    _id += 1
    r = S.post(URL, json={"jsonrpc": "2.0", "method": method, "params": list(params), "id": _id})
    r.raise_for_status()
    data = r.json()
    if data.get("error"):
        raise RuntimeError(f"{method} 失败：{data['error']}")
    return data.get("result")


def first_id(method, name_field, name, extra=None):
    """按名称查枚举/记录，返回 id；查不到返回 None。"""
    q = {name_field: name}
    if extra:
        q.update(extra)
    try:
        rows = call(method, q)
    except RuntimeError:
        return None
    return rows[0]["id"] if rows else None


def main():
    call("Auth.login", USER, PASSWORD)
    print("登录成功。")

    # 1) 产品 / 版本 / 构建
    classification = 1  # 默认分类 "Other"，通常 id=1
    prod = call("Product.filter", {"name": "5G 基站 gNodeB"})
    if prod:
        pid = prod[0]["id"]
    else:
        pid = call("Product.create", {"name": "5G 基站 gNodeB", "classification": classification})["id"]
    print(f"产品 id={pid}")

    ver = call("Version.filter", {"product": pid, "value": "R1.0"})
    vid = ver[0]["id"] if ver else call("Version.create", {"product": pid, "value": "R1.0"})["id"]

    bld = call("Build.filter", {"version": vid, "name": "build-2026.08"})
    bid = bld[0]["id"] if bld else call("Build.create",
                                        {"version": vid, "name": "build-2026.08", "is_active": True})["id"]
    print(f"版本 id={vid}  构建 id={bid}")

    # 2) 测试计划
    plan_type = first_id("PlanType.filter", "name", "Function") or 1
    plans = call("TestPlan.filter", {"name": "5G NR 协议一致性测试", "product": pid})
    if plans:
        plan_id = plans[0]["id"]
    else:
        plan_id = call("TestPlan.create", {
            "name": "5G NR 协议一致性测试",
            "text": "覆盖 RRC/切换/功率控制/吞吐量等核心协议流程的一致性验证。",
            "product": pid, "product_version": vid, "type": plan_type, "is_active": True,
        })["id"]
    print(f"测试计划 id={plan_id}")

    # 3) 定义测试用例（含步骤：Kiwi 将步骤合并在 text 字段，Markdown）
    category = first_id("Category.filter", "name", "--default--", {"product": pid}) \
        or call("Category.create", {"name": "协议一致性", "product": pid})["id"]
    priority = first_id("Priority.filter", "value", "P1") or 1
    confirmed = first_id("TestCaseStatus.filter", "name", "CONFIRMED") or 2

    cases = [
        ("RRC 连接建立成功率",
         "**前置**: UE 开机并搜网\n**步骤**: 1. UE 发起 RRC Setup Request 2. 观察 gNodeB 响应\n"
         "**预期**: 收到 RRC Setup，连接建立，成功率 ≥ 99%"),
        ("同频小区切换 (Intra-freq Handover)",
         "**前置**: UE 处于连接态并靠近小区边缘\n**步骤**: 1. 触发 A3 事件 2. 观察切换流程\n"
         "**预期**: 切换成功、无掉话、中断时延 < 50ms"),
        ("上行功率控制 (Uplink Power Control)",
         "**前置**: UE 已接入\n**步骤**: 1. 改变路径损耗 2. 观察 UE 发射功率调整\n"
         "**预期**: 功率按闭环 TPC 命令收敛，PHR 合理"),
        ("下行吞吐量 (DL Throughput)",
         "**前置**: 单 UE 满缓冲\n**步骤**: 1. 灌满业务 2. 记录 MAC 层吞吐\n"
         "**预期**: 达到该带宽/MCS 理论峰值 ≥ 85%"),
        ("DRB 建立与去激活",
         "**前置**: RRC 已连接\n**步骤**: 1. 建立 DRB 2. 触发去激活\n"
         "**预期**: DRB 正确建立/释放，无资源泄漏"),
    ]
    case_ids = []
    for summary, text in cases:
        exist = call("TestCase.filter", {"summary": summary})
        if exist:
            cid = exist[0]["id"]
        else:
            cid = call("TestCase.create", {
                "summary": summary, "text": text,
                "category": category, "priority": priority,
                "case_status": confirmed,  # 直接置为「评审通过」
                "is_automated": False,
            })["id"]
        case_ids.append(cid)
        # 4) 评审：确保状态为 CONFIRMED；并挂到测试计划
        call("TestCase.update", cid, {"case_status": confirmed})
        try:
            call("TestPlan.add_case", plan_id, cid)
        except RuntimeError:
            pass  # 已在计划中
        print(f"用例 id={cid}  {summary}  → 已评审(CONFIRMED)并加入计划")

    # 5) 测试运行（执行）：从计划创建 Run 并加入用例
    me = call("User.filter", {"username": USER})[0]["id"]
    run = call("TestRun.create", {
        "summary": "5G NR 一致性 - 冒烟轮次 build-2026.08",
        "plan": plan_id, "build": bid, "manager": me,
    })["id"]
    exec_ids = []
    for cid in case_ids:
        res = call("TestRun.add_case", run, cid)  # 返回该用例在此 run 的 TestExecution
        # add_case 可能返回列表或单对象，兼容处理
        if isinstance(res, list):
            exec_ids.extend([e["id"] for e in res])
        elif isinstance(res, dict):
            exec_ids.append(res["id"])
    print(f"测试运行 id={run}  执行条目 {len(exec_ids)} 条")

    # 6) 回填执行结果（模拟：多数 PASS，一条 FAIL 便于统计有对比）
    st_pass = first_id("TestExecutionStatus.filter", "name", "PASSED")
    st_fail = first_id("TestExecutionStatus.filter", "name", "FAILED")
    for i, eid in enumerate(exec_ids):
        status = st_fail if (i == 1 and st_fail) else st_pass
        if status:
            call("TestExecution.update", eid, {"status": status})
    print("已回填执行结果（含 1 条 FAILED 以便统计对比）。")

    # 7) 统计：按状态汇总通过率
    execs = call("TestExecution.filter", {"run_id": run})
    total = len(execs)
    passed = sum(1 for e in execs if e.get("status") == st_pass)
    print(f"\n统计：共 {total} 条，PASSED {passed} 条，通过率 "
          f"{(passed / total * 100 if total else 0):.1f}%")
    print("到 https://localhost:8444 → Test Runs / Reports 查看图形化报表。")


if __name__ == "__main__":
    main()
