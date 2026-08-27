#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企业文档协同场景种子脚本（Nextcloud，WebDAV）

在 Nextcloud 里建出「供应链部 / 研发测试部」两个文档中心，按
  部门 → 项目 → 文档库
的层级建目录，并灌入一批带真实内容的模拟文档，用于模拟 SharePoint 式协同。

依赖：requests（pip install requests）
配置（环境变量）：
  NEXTCLOUD_URL=http://localhost:8083 \
  NEXTCLOUD_USER=admin NEXTCLOUD_PASSWORD=admin123456 \
  python3 seed_nextcloud.py

脚本幂等：目录逐级创建(已存在返回 405 视为正常)，文件 PUT 覆盖。
"""
import os
import sys

try:
    import requests
except ImportError:
    sys.exit("请先安装依赖：pip install requests")

BASE = os.environ.get("NEXTCLOUD_URL", "http://localhost:8083").rstrip("/")
USER = os.environ.get("NEXTCLOUD_USER", "admin")
PASSWORD = os.environ.get("NEXTCLOUD_PASSWORD", "admin123456")
DAV = f"{BASE}/remote.php/dav/files/{USER}"

S = requests.Session()
S.auth = (USER, PASSWORD)

# ---- 目录树：部门 → 项目 → 文档库 ----------------------------------------
FOLDERS = [
    # 供应链部
    "供应链部",
    "供应链部/部门制度",
    "供应链部/供应商管理",
    "供应链部/供应商管理/供应商资质",
    "供应链部/供应商管理/采购合同",
    "供应链部/项目_2026年度采购降本",
    "供应链部/项目_2026年度采购降本/到货单据",
    "供应链部/项目_2026年度采购降本/库存盘点报告",
    # 研发测试部
    "研发测试部",
    "研发测试部/部门制度",
    "研发测试部/项目_5G基站gNodeB",
    "研发测试部/项目_5G基站gNodeB/需求文档",
    "研发测试部/项目_5G基站gNodeB/测试计划评审",
    "研发测试部/项目_5G基站gNodeB/测试报告",
    "研发测试部/项目_5G基站gNodeB/缺陷分析",
    "研发测试部/项目_核心网UPF",
    "研发测试部/项目_核心网UPF/需求文档",
    "研发测试部/项目_核心网UPF/测试报告",
]

# ---- 模拟文档：路径 -> 内容 ----------------------------------------------
FILES = {
    "供应链部/部门制度/供应链管理制度.md":
        "# 供应链管理制度\n\n## 1. 目的\n规范采购、库存与出入库流程。\n\n"
        "## 2. 采购流程\n请购 → 询比价 → 下单(Odoo) → 到货检验 → 入库。\n\n"
        "## 3. 安全库存\n低于安全库存自动触发补货请购。\n",
    "供应链部/供应商管理/供应商资质/合格供应商清单.md":
        "# 合格供应商清单(AVL)\n\n| 供应商 | 品类 | 资质 | 评级 |\n"
        "|---|---|---|---|\n| 深圳元件供应商 | 光模块/PCBA | ISO9001 | A |\n"
        "| 华东线缆厂 | 网线/连接器 | ISO9001 | B |\n",
    "供应链部/供应商管理/采购合同/README.md":
        "本目录存放采购合同扫描件与电子签署版本。命名规范：`合同号_供应商_日期`。\n",
    "供应链部/项目_2026年度采购降本/降本目标与计划.md":
        "# 2026 年度采购降本计划\n\n- 目标：整体采购成本下降 8%\n"
        "- 举措：集中采购、双源引入、VMI 寄售\n- 里程碑：Q1 立项 / Q2 谈判 / Q3 落地 / Q4 复盘\n",
    "供应链部/项目_2026年度采购降本/到货单据/README.md":
        "存放到货/出库单据。可由 n8n 从 Odoo 出库完成事件自动归档 PDF。\n",
    "供应链部/项目_2026年度采购降本/库存盘点报告/2026Q1盘点报告.md":
        "# 2026 Q1 库存盘点报告\n\n- 盘点范围：主仓 WH/Stock\n- 账实相符率：99.2%\n"
        "- 差异处理：3 项待复盘，已建调整单\n",

    "研发测试部/部门制度/研发测试流程规范.md":
        "# 研发测试流程规范\n\n需求 → 用例设计(Kiwi) → 评审 → 执行 → 缺陷(Redmine) → 复测 → 报告归档。\n\n"
        "## 准入准出\n准入：需求冻结、用例评审通过。\n准出：P1/P2 缺陷清零，通过率 ≥ 95%。\n",
    "研发测试部/项目_5G基站gNodeB/需求文档/需求规格说明.md":
        "# 5G 基站 gNodeB 需求规格说明(SRS)\n\n"
        "## 功能需求\n- FR-01 RRC 连接建立\n- FR-02 同频/异频切换\n- FR-03 上行功率控制\n"
        "- FR-04 N78 载波聚合\n\n## 性能需求\n- 下行吞吐 ≥ 理论峰值 85%\n- 切换中断 < 50ms\n",
    "研发测试部/项目_5G基站gNodeB/测试计划评审/测试计划_冒烟轮次.md":
        "# 测试计划 - 冒烟轮次(build-2026.08)\n\n"
        "## 范围\nRRC / 切换 / 功率控制 / 吞吐量 / DRB 共 5 条核心用例。\n\n"
        "## 评审记录\n评审人：测试组长；结论：通过，用例状态置 CONFIRMED。\n",
    "研发测试部/项目_5G基站gNodeB/测试报告/冒烟测试报告.md":
        "# 5G 基站冒烟测试报告\n\n- 构建：build-2026.08\n- 用例数：5\n- 通过：4  失败：1\n"
        "- 通过率：80%\n- 失败项：同频小区切换偶发掉话(已在 Redmine 建 Bug)\n\n"
        "对应 Kiwi 测试运行，供评审归档。\n",
    "研发测试部/项目_5G基站gNodeB/缺陷分析/缺陷Top分析.md":
        "# 缺陷 Top 分析\n\n| 模块 | 缺陷数 | 占比 |\n|---|---|---|\n"
        "| 移动性(切换) | 3 | 43% |\n| 功率控制 | 2 | 29% |\n| 资源管理 | 2 | 28% |\n\n"
        "结论：移动性为高风险模块，下一轮加强回归。\n",
    "研发测试部/项目_核心网UPF/需求文档/README.md":
        "核心网 UPF(用户面功能)项目文档区，存放需求、接口与测试资料。\n",
}


def mkcol_p(path):
    """逐级创建目录，父目录不存在也能建出整条路径。"""
    parts, cur = path.split("/"), ""
    for p in parts:
        cur = f"{cur}/{p}" if cur else p
        url = f"{DAV}/{requests.utils.quote(cur)}"
        r = S.request("MKCOL", url)
        if r.status_code not in (201, 405):  # 201 建成功 / 405 已存在
            print(f"! 目录创建失败 {cur} -> {r.status_code} {r.text[:100]}")
            return
    print(f"目录就绪：{path}")


def put(path, content):
    url = f"{DAV}/{requests.utils.quote(path)}"
    r = S.put(url, data=content.encode("utf-8"))
    if r.status_code in (201, 204):
        print(f"文件已写入：{path}")
    else:
        print(f"! 文件写入失败 {path} -> {r.status_code} {r.text[:100]}")


def main():
    r = S.request("PROPFIND", DAV, headers={"Depth": "0"})
    if r.status_code == 401:
        sys.exit("认证失败：检查 NEXTCLOUD_USER / NEXTCLOUD_PASSWORD。")
    if r.status_code >= 400 and r.status_code != 405:
        sys.exit(f"无法连接 Nextcloud（{r.status_code}）：确认已 "
                 f"docker compose --profile docs up -d 且初始化完成，URL={BASE}")

    print("== 建目录（部门 → 项目 → 文档库）==")
    for f in FOLDERS:
        mkcol_p(f)
    print("\n== 写入模拟文档 ==")
    for path, content in FILES.items():
        put(path, content)

    print(f"\n完成。登录 {BASE} 的 Files 查看；"
          f"在 Apps 装 Nextcloud Office + 内置 CODE 后即可在线协同编辑。")


if __name__ == "__main__":
    main()
