#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
团队沟通场景种子脚本（Mattermost，Teams 平替）

创建团队「Acme 通信」及一组按部门/项目划分的频道，用于模拟同事沟通。

依赖：requests（pip install requests）
前置：Mattermost 已启动，且已开启「个人访问令牌」并生成一个 Token。
配置（环境变量）：
  MM_URL=http://localhost:8065 \
  MM_TOKEN=你的PersonalAccessToken \
  python3 seed_mattermost.py

脚本幂等：团队/频道已存在则复用。
"""
import os
import sys

try:
    import requests
except ImportError:
    sys.exit("请先安装依赖：pip install requests")

BASE = os.environ.get("MM_URL", "http://localhost:8065").rstrip("/")
TOKEN = os.environ.get("MM_TOKEN", "")
if not TOKEN:
    sys.exit("请通过环境变量 MM_TOKEN 提供个人访问令牌（个人设置→安全→个人访问令牌）。")

API = f"{BASE}/api/v4"
S = requests.Session()
S.headers.update({"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})

TEAM_NAME = "acme-comm"
TEAM_DISPLAY = "Acme 通信"
CHANNELS = [
    ("supply-purchase", "供应链-采购"),
    ("supply-warehouse", "供应链-仓储物流"),
    ("rd-5g", "研发-5G基站"),
    ("test-defects", "测试-缺陷跟踪"),
    ("quality-report", "质量-周报"),
]


def me():
    r = S.get(f"{API}/users/me")
    r.raise_for_status()
    return r.json()["id"]


def ensure_team():
    r = S.get(f"{API}/teams/name/{TEAM_NAME}")
    if r.status_code == 200:
        print(f"团队已存在：{TEAM_DISPLAY}")
        return r.json()["id"]
    r = S.post(f"{API}/teams", json={"name": TEAM_NAME, "display_name": TEAM_DISPLAY, "type": "O"})
    if r.status_code in (200, 201):
        print(f"团队已创建：{TEAM_DISPLAY}")
        return r.json()["id"]
    sys.exit(f"团队创建失败：{r.status_code} {r.text[:200]}")


def ensure_membership(team_id, user_id):
    S.post(f"{API}/teams/{team_id}/members", json={"team_id": team_id, "user_id": user_id})


def ensure_channel(team_id, name, display):
    r = S.get(f"{API}/teams/{team_id}/channels/name/{name}")
    if r.status_code == 200:
        print(f"  频道已存在：#{display}")
        return
    r = S.post(f"{API}/channels", json={
        "team_id": team_id, "name": name, "display_name": display, "type": "O"})
    if r.status_code in (200, 201):
        print(f"  频道已创建：#{display}")
    else:
        print(f"  ! 频道创建失败 #{display} -> {r.status_code} {r.text[:160]}")


def main():
    uid = me()
    team_id = ensure_team()
    ensure_membership(team_id, uid)
    print("建频道：")
    for name, display in CHANNELS:
        ensure_channel(team_id, name, display)
    print(f"\n完成。登录 {BASE} 查看团队「{TEAM_DISPLAY}」及各频道。")


if __name__ == "__main__":
    main()
