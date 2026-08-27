# 场景三：企业文档协同（Nextcloud，SharePoint 平替）

用 Nextcloud 提供 SharePoint 的核心能力：**文档共享、版本管理、在线协同编辑、
按部门分权限**。用于模拟供应链与研发测试两个部门的文档中心。

## 能力对照（对标 SharePoint）

| SharePoint 概念 | Nextcloud 对应 |
|---|---|
| 文档库 Document Library | 文件夹 + Files 应用 |
| 站点/团队站点 | 群组文件夹 Group Folders |
| 共同编辑 Co-authoring | Nextcloud Office（Collabora） |
| 版本历史 | 内置版本控制 |
| 权限继承/共享 | 分享链接 + 群组 ACL |
| 列表 Lists | Tables 应用（可选） |

## 启动

```bash
cd enterprise-sim
cp .env.example .env
docker compose --profile docs up -d
```

访问 http://localhost:8083 ，用 `.env` 里的 `NEXTCLOUD_ADMIN_USER/PASSWORD`
（默认 admin / admin123456）登录。首次启动初始化需要 1–2 分钟。

## 开启「在线协同编辑」（关键一步）

为避免跨容器网络配置，采用**内置 CODE 服务器**方案，零额外容器：

1. 右上角头像 → **应用(Apps)**。
2. 安装 **Nextcloud Office**（Collabora 集成前端）。
3. 安装 **Collabora Online - Built-in CODE Server**（内置文档引擎）。
4. 到 *管理设置 → Nextcloud Office*，选择「使用内置的 CODE 服务器」并保存。

完成后，在 Files 里新建/打开 `.docx`、`.xlsx`、`.pptx` 即可多人实时协同编辑
（多个浏览器登录不同账号打开同一文件可看到协同光标）。

> 内置 CODE 适合演示/模拟；若要更好性能，可改用独立 Collabora 容器（见文末）。

## 建议的部门目录结构

用脚本或手动建出两个部门的文档中心：

```
/供应链部/
  ├── 供应商资质/
  ├── 采购合同/
  ├── 到货单据/          ← 和场景一 Odoo 出入库单据呼应
  └── 库存盘点报告/
/研发测试部/
  ├── 需求文档/
  ├── 测试计划评审/      ← 和场景二 Kiwi 测试计划呼应
  ├── 测试报告/
  └── 缺陷分析/
```

## 方式 A：脚本建目录 + 灌样例文档

```bash
cd enterprise-sim/scenarios/document-collaboration
pip install requests
NEXTCLOUD_URL=http://localhost:8083 \
NEXTCLOUD_USER=admin NEXTCLOUD_PASSWORD=admin123456 \
python3 seed_nextcloud.py
```

脚本通过 WebDAV 建出上面的部门目录树，并上传两份样例文档。

## AI 演练点（用 API 而非点 UI）

Nextcloud 对 AI 友好，主要两套接口：

| AI 任务 | 接口 | 说明 |
|---|---|---|
| 归档/上传文档 | WebDAV `PUT /remote.php/dav/files/<user>/...` | 把生成的报告/单据存入对应库 |
| 建目录/整理 | WebDAV `MKCOL` / `MOVE` | 自动归类、按项目建文件夹 |
| 读取/检索文档 | WebDAV `GET` / `PROPFIND` | 让 Agent 读文档内容做分析 |
| 生成分享链接 | OCS `POST /ocs/v2.php/apps/files_sharing/api/v1/shares` | 对外/跨部门共享 |
| 版本回溯 | `/remote.php/dav/versions/` | 审计文档变更 |

认证：管理接口用账号密码 Basic Auth；生产/模拟推荐给 AI 账号建**应用专用密码**
（*个人设置 → 安全 → 应用密码*），避免用主密码。

## 跨部门联动示例（配合 n8n）

- 场景一 Odoo 出库完成 → n8n 把出库单 PDF 存进 `/供应链部/到货单据/`。
- 场景二 Kiwi 测试轮次结束 → n8n 生成通过率报表存进 `/研发测试部/测试报告/`。
- AI 定期扫描两个库，汇总生成跨部门周报再存回 Nextcloud。

## 可选升级：独立 Collabora 容器（更高性能）

如需更强的协同编辑性能，可在 `docker-compose.yml` 增加 `collabora/code` 服务
并在 Nextcloud Office 设置里填其 URL。注意需处理 Nextcloud 与 Collabora 之间的
WOPI 回调域名（两端都要能通过同一主机名互访），本地纯 localhost 环境配置较繁琐，
模拟场景用内置 CODE 已足够。
