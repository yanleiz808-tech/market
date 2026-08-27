#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企业文档协同场景种子脚本（Nextcloud，WebDAV）

在 Nextcloud 里建出「供应链部 / 研发测试部」两个文档中心的目录树，
并上传两份样例文档，用于模拟 SharePoint 式的企业文档协同。

依赖：requests（pip install requests）
配置（环境变量）：
  NEXTCLOUD_URL=http://localhost:8083 \
  NEXTCLOUD_USER=admin NEXTCLOUD_PASSWORD=admin123456 \
  python3 seed_nextcloud.py

脚本幂等：目录已存在(405)或文件已存在都会跳过。
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

# 目录树（相对用户根）
FOLDERS = [
    "供应链部",
    "供应链部/供应商资质",
    "供应链部/采购合同",
    "供应链部/到货单据",
    "供应链部/库存盘点报告",
    "研发测试部",
    "研发测试部/需求文档",
    "研发测试部/测试计划评审",
    "研发测试部/测试报告",
    "研发测试部/缺陷分析",
]

# 样例文档 (目标路径, 内容)
FILES = {
    "供应链部/到货单据/README.txt":
        "本目录存放到货/出库单据。可由 n8n 从 Odoo 出库完成后自动归档。\n",
    "研发测试部/测试报告/5G基站-冒烟测试报告.md":
        "# 5G 基站 gNodeB 冒烟测试报告\n\n"
        "- 构建: build-2026.08\n- 用例数: 5\n- 通过率: 80%\n"
        "- 失败项: 同频小区切换 (待复测)\n\n对应 Kiwi 测试运行，供评审归档。\n",
}


def mkcol(path):
    url = f"{DAV}/{requests.utils.quote(path)}"
    r = S.request("MKCOL", url)
    if r.status_code in (201, 405):  # 201 建成功 / 405 已存在
        print(f"目录 {'已存在' if r.status_code == 405 else '已创建'}：{path}")
    else:
        print(f"! 目录创建失败 {path} -> {r.status_code} {r.text[:120]}")


def put(path, content):
    url = f"{DAV}/{requests.utils.quote(path)}"
    r = S.put(url, data=content.encode("utf-8"))
    if r.status_code in (201, 204):
        print(f"文件已上传：{path}")
    else:
        print(f"! 文件上传失败 {path} -> {r.status_code} {r.text[:120]}")


def main():
    # 连通性检查
    r = S.request("PROPFIND", DAV, headers={"Depth": "0"})
    if r.status_code == 401:
        sys.exit("认证失败：检查 NEXTCLOUD_USER / NEXTCLOUD_PASSWORD。")
    if r.status_code >= 400 and r.status_code != 405:
        sys.exit(f"无法连接 Nextcloud（{r.status_code}）：确认已 docker compose --profile docs up -d "
                 f"且初始化完成，URL={BASE}")

    for f in FOLDERS:
        mkcol(f)
    for path, content in FILES.items():
        put(path, content)

    print(f"\n完成。登录 {BASE} 的 Files 查看部门目录；"
          f"在 Apps 里装 Nextcloud Office + 内置 CODE 即可协同编辑。")


if __name__ == "__main__":
    main()
