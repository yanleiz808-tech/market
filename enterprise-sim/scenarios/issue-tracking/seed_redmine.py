#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
问题跟踪场景种子脚本（Redmine，Jira 平替）

在 Redmine 里建一个研发项目，并灌入示例 Bug / Feature 工单，
用于模拟研发测试部门的缺陷/需求管理。

依赖：requests（pip install requests）
前置：Redmine 已启动，且已在「管理→设置→API」开启 REST，并拿到 API Key。
配置（环境变量）：
  REDMINE_URL=http://localhost:8084 \
  REDMINE_API_KEY=你的APIKey \
  python3 seed_redmine.py

脚本幂等：项目 identifier 已存在会复用；示例工单按主题查重，存在则跳过。
"""
import os
import sys

try:
    import requests
except ImportError:
    sys.exit("请先安装依赖：pip install requests")

BASE = os.environ.get("REDMINE_URL", "http://localhost:8084").rstrip("/")
API_KEY = os.environ.get("REDMINE_API_KEY", "")
if not API_KEY:
    sys.exit("请通过环境变量 REDMINE_API_KEY 提供 API Key（我的账号 → API 访问键）。")

PROJECT_ID = "rd-5g-gnodeb"
PROJECT_NAME = "5G 基站研发"

S = requests.Session()
S.headers.update({"X-Redmine-API-Key": API_KEY, "Content-Type": "application/json"})


def get(path, **params):
    r = S.get(f"{BASE}{path}", params=params)
    r.raise_for_status()
    return r.json()


def ensure_project():
    r = S.get(f"{BASE}/projects/{PROJECT_ID}.json")
    if r.status_code == 200:
        print(f"项目已存在：{PROJECT_NAME} ({PROJECT_ID})")
        return
    payload = {"project": {
        "name": PROJECT_NAME, "identifier": PROJECT_ID,
        "description": "5G 基站(gNodeB)研发的需求与缺陷跟踪。",
        "is_public": True,
    }}
    r = S.post(f"{BASE}/projects.json", json=payload)
    if r.status_code in (201, 200):
        print(f"项目已创建：{PROJECT_NAME} ({PROJECT_ID})")
    else:
        sys.exit(f"项目创建失败：{r.status_code} {r.text[:200]}")


def tracker_map():
    """返回 {名称: id}，用于按 Bug/Feature 名称取 tracker id。"""
    return {t["name"]: t["id"] for t in get("/trackers.json")["trackers"]}


def issue_exists(subject):
    # 在本项目内按主题查重（Redmine 无精确 subject 过滤，取回本项目问题自行比对）
    data = get("/issues.json", project_id=PROJECT_ID, status_id="*", limit=100)
    return any(i["subject"] == subject for i in data.get("issues", []))


def create_issue(tracker_id, subject, description, priority_id=None):
    if issue_exists(subject):
        print(f"  工单已存在，跳过：{subject}")
        return
    issue = {"project_id": PROJECT_ID, "tracker_id": tracker_id,
             "subject": subject, "description": description}
    if priority_id:
        issue["priority_id"] = priority_id
    r = S.post(f"{BASE}/issues.json", json={"issue": issue})
    if r.status_code in (201, 200):
        print(f"  已创建：[{subject}]")
    else:
        print(f"  ! 创建失败 {subject} -> {r.status_code} {r.text[:160]}")


def main():
    ensure_project()
    trackers = tracker_map()
    bug = trackers.get("Bug") or trackers.get("缺陷")
    feature = trackers.get("Feature") or trackers.get("功能")
    if not bug or not feature:
        print(f"提示：未找到 Bug/Feature tracker，现有：{list(trackers)}；"
              f"请在 管理→跟踪标签 中确认。")

    print("灌入 Feature：")
    if feature:
        create_issue(feature, "支持 N78 频段载波聚合",
                     "研发需求：新增 N78 频段 2CC 载波聚合能力，提升下行峰值吞吐。")
        create_issue(feature, "gNodeB 远程重启 API",
                     "运维需求：提供安全的远程重启接口，带鉴权与操作审计。")

    print("灌入 Bug：")
    if bug:
        create_issue(bug, "同频小区切换偶发掉话",
                     "复现：UE 在小区边缘触发 A3 事件切换时偶发 RRC 重建，掉话率约 2%。"
                     "对应 Kiwi 用例『同频小区切换』FAILED，构建 build-2026.08。")
        create_issue(bug, "上行功率控制收敛慢",
                     "路径损耗突变后 UE 发射功率收敛超过 3 个 TPC 周期，超出规格。")
        create_issue(bug, "高负载下 DRB 资源泄漏",
                     "长稳测试 12h 后观测到 DRB 未完全释放，内存缓慢增长。")

    # 简单统计
    data = get("/issues.json", project_id=PROJECT_ID, status_id="*", limit=100)
    total = data.get("total_count", len(data.get("issues", [])))
    print(f"\n完成。项目现有工单 {total} 条。到 {BASE}/projects/{PROJECT_ID}/issues 查看。")


if __name__ == "__main__":
    main()
