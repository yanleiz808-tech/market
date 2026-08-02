# 场景二：通信产业测试部门（Kiwi TCMS）

模拟一个通信设备（示例：**5G 基站 gNodeB**）测试部门的完整闭环：
**测试计划 → 用例定义 → 评审 → 执行 → 统计报表**。

## 业务流程与 Kiwi 模型对应

```
产品/版本/构建          测试计划            测试用例(定义)        评审            测试运行(执行)         统计
Product/Version/Build → TestPlan  ──加入──► TestCase ──状态──► CONFIRMED ──► TestRun/TestExecution ─► Reports
                                          (含步骤 text)   PROPOSED→CONFIRMED   回填 PASS/FAIL/BLOCKED   通过率/趋势
```

- **计划(TestPlan)**：一次测试活动的容器，绑定产品与版本。
- **用例(TestCase)**：可复用的用例定义；步骤写在 `text`（Markdown）。
- **评审**：Kiwi 用用例状态表达——`PROPOSED`(草拟) → `CONFIRMED`(评审通过) → 可执行。
- **执行(TestRun/TestExecution)**：针对某个构建执行计划中的用例，逐条回填结果。
- **报表(Reports/Telemetry)**：内置通过率、执行趋势、按优先级/组件分布等图表。

## Kiwi 初始化（首次必做）

```bash
cd enterprise-sim
docker compose exec kiwi /Kiwi/manage.py migrate
docker compose exec kiwi /Kiwi/manage.py createsuperuser   # 记住这里的密码
```

然后访问 https://localhost:8444 （自签名证书，浏览器忽略警告即可登录）。

## 方式 A：脚本一键构建整条链路

```bash
cd enterprise-sim/scenarios/telecom-testing
pip install requests
KIWI_URL=https://localhost:8444/json-rpc/ \
KIWI_USER=admin KIWI_PASSWORD=你设置的密码 \
python3 seed_kiwi.py
```

脚本会：建产品/版本/构建 → 建计划「5G NR 协议一致性测试」→ 定义 5 条通信专业用例
（RRC 连接、切换、功率控制、吞吐量、DRB）→ 评审置 CONFIRMED → 建测试运行并回填结果
（含 1 条 FAILED 便于统计对比）→ 打印通过率。

> 各版本方法名/枚举 id 可能略有差异，脚本已尽量用 `*.filter` 按名称查找。若某一步
> 报错，按下方 UI 步骤在界面里完成对应动作即可。

## 方式 B：UI 手动走一遍

1. **建产品**：*Admin → Products* 新建「5G 基站 gNodeB」，加版本 R1.0、构建 build-2026.08。
2. **建计划**：*Test Plans → New*，选产品与版本，填计划名与说明。
3. **定义用例**：计划页 *Add Case*，填 Summary、步骤(text)、优先级、组件；初始状态 PROPOSED。
4. **评审**：用例页把 *Status* 改为 **CONFIRMED**（代表评审通过）。
5. **执行**：计划页 *New Test Run*，选构建、加入用例；逐条点 **PASS/FAIL/BLOCKED**。
6. **报表**：*Test Runs* 页看单轮统计；*Telemetry/Reporting* 看跨轮次通过率与趋势。

## AI 演练点（用 API 而非点 UI）

| AI 任务 | 涉及方法 | 说明 |
|---|---|---|
| 需求转用例 | `TestCase.create` | 从需求/协议文档自动生成用例草稿 |
| 用例评审辅助 | `TestCase.filter/update` | 检查步骤完整性，批量置 CONFIRMED |
| 组织测试轮次 | `TestRun.create` + `add_case` | 按优先级/变更范围挑选用例组 Run |
| 结果回填 | `TestExecution.update(status)` | 对接自动化框架回写 PASS/FAIL |
| 质量报表 | `TestExecution.filter` 聚合 | 生成通过率、失败 Top、回归风险 |

把这些包成 MCP 工具（如 `create_test_plan`、`define_test_case`、`start_test_run`、
`record_result`、`quality_report`），Agent 即可端到端跑「计划→定义→评审→执行→报表」。
