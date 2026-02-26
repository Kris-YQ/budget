# Budget 管理系统需求梳理（V3）

## 1. 目标概述
系统用于管理 70+ 资源（resource）在 20-30 个项目中的预算与分配，确保：

- BP 资金按规则消耗（尽量花完，不硬性禁止超支，但要明显标识）。
- 资源按月分配到 Clarity，支持跨 BP/Clarity 拆分 FTE。
- 识别每个资源的 coverage gap（月份与金额），并给出补洞与招聘建议。

## 2. 核心实体与关系

- Project：有 `project code`（简写）与项目名称。
- BP：每个 Project code 仅对应一个 BP；BP 有编号（如 2501970）和名称。
- Clarity：一个 BP 对应多个 Clarity；一个 Clarity 只能归属一个 BP。
- Resource：有唯一员工编号与唯一 cTool 编号；支持重名；含 manager、cost center 等扩展字段。
- Allocation：Resource 最终按月分配到 Clarity 级别，FTE 可拆分。
- Gap（Demand）：按资源识别未覆盖月份和金额缺口。

## 3. 时间与结算口径

- 预算周期：上一年 12 月到当年 11 月（例如 2025-12 ~ 2026-11）。
- FTE 粒度：最小 0.1，月度上限 1.0。
- 月度成本：`当月实际分配 FTE × rate`。
- rate：按地区 + resource 类型（perm/contract + contract type）确定；年度会涨价。

## 4. Resource 规则

- perm 与 contract 均以“每月总 FTE=1.0”为目标，允许跨多个 BP/Clarity 凑满。
- perm：强制 12 个月都需满配覆盖。
- contract：允许某些月份 0 FTE；0 FTE 需特别标识，并与 Contract End Date 联动展示。
- 需要记录 release/end date。

## 5. BP/Clarity 预算与状态规则

- BP 状态：`Committed / TBC / Received / Closed`。
- 未到账（非 Received）的 BP：完全禁止分配。
- BP 有可用窗口（有效期）；到期后提醒并锁定，可手动解锁。
- Clarity 使用时限跟随 BP。
- BP 金额单位按 K；可接受约 ±5K 浮动，但任何超支都要有明显标识。

## 6. Gap 计算与建议

- Gap 公式确认：
  - `gap_cost(月) = max(0, 1 - 当月总FTE) × 当月rate`
  - 年度 gap = 周期内各月 gap_cost 汇总
- contract 的 gap 仍按 12 个月预算视角核算，同时结合 Contract End Date 展示实际可覆盖区间。
- 推荐补洞策略优先级：
  1. 先用“快到期”BP
  2. 再优先“可刚好用完”的 BP
  3. 再看“余额最多”BP
  4. 支持手动策略切换（D）
- 招聘建议需按地区输出：
  - perm 按 12 个月总费用测算
  - contract 最小建议单位为 3 个月

## 7. 功能域（必须覆盖）

1. Resource（Supply）
2. Project
3. BP
4. Clarity
5. Allocation（资源分配）
6. Gap（Demand）
7. Dashboard（新增，需规划）

## 8. 数据与操作能力

- 支持多条件筛选。
- 支持 Excel 导入/导出（字段待提供）。

## 9. Dashboard 初步规划（无 UI 图）

建议包含：

- 首页第一屏核心字段：`Resource ID / Project code / Resource name / BP ID / Allocated budget`。
- 首页主视图：偏好人力维度（Resource/Gap）。
- 无需单独展示“本月新增项目/BP”卡片。
- 预算执行：按 BP/Project 展示 burn rate、剩余额度、到期状态。
- 资源覆盖热力图：按月查看资源 FTE 覆盖与 0 FTE 标识。
- Gap 看板：按资源列出 gap 月份、gap 金额、建议补洞 BP。
- 招聘建议区：按地区展示可新增 perm/contract（3个月起）容量。

## 10. 权限与流程（已确认）

- 第一版角色：`BM / SME`。
- BM：可编辑 Allocation、可解锁过期 BP。
- SME：只读权限（read-only）。
- 第一版不需要审批流。

## 11. Excel 导入导出（已确认）

- 导入顺序：`Resource → BP/Clarity → Allocation`。
- 支持导入预检查，不仅做校验，还要展示“改动前/改动后”对比（至少两列），并标注改动。
- 导出支持按当前筛选条件导出。

## 12. 报表与提醒（已确认）

- 第一版不强制周报/月报维度。
- 提醒仅需系统内标识（不需要邮件/Teams 推送）。
- 暂不需要“未来3个月预测缺口”报表。

## 13. 第4轮确认：Resource 字段清单

### 13.1 必填字段
- `Resource ID`
- `cTool ID`
- `Resource Name`
- `Contract Type`
- `City`
- `Pod`
- `2026 GPDM Rate($)`
- `Allocate Month`
- `Allocate budget($)`
- `Gap($)`
- `Project code`
- `BP ID`
- `Clarity ID`
- `Role End date`
- `SVS`
- `Supplier Code`
- `Billable Service Code`

### 13.2 选填字段
- `Project Name`
- `BP Name`
- `Clarity Name`
- `2025 Dec FTE`
- `2026 Jan FTE ... 2026 Dec FTE`（按月字段）
- `Total FTE($)`

## 14. 第4轮确认：Contract Type 与地区 Rate 字典（单位：K）

- Contract Type 仅有两类：`Perm / Non-Perm`。

### 14.1 Perm
- HK: 15.212
- UK: 24.429
- PL: 12.301
- GZ: 9.182
- XA: 7.601

### 14.2 Non-Perm
- PL: 14.022
- GZ: 6.281
- XA: 5.773

## 15. 第4轮确认：审计与导入机制

- BP 手动解锁必须记录日志（至少包含操作人、操作时间、原因）。
- Allocation 变更需要保留历史版本（用于审计与回溯）。
- 导入预检查不做阻断；系统展示每条记录“原值 vs 新值”差异，需逐条手动确认后才可完成导入。

## 16. FE UI 低保真方案（V1）

> 目标：在不依赖设计稿的前提下，先定义可开发的页面结构、关键组件与交互流程。

### 16.1 信息架构（导航）

- 顶部导航：`Dashboard | Resource | Allocation | Gap | BP/Clarity | Import/Export`
- 全局筛选条（跨页保留）：`Budget Cycle`、`City`、`Contract Type`、`BP Status`、`Project code`。
- 全局状态颜色建议：
  - 正常：绿色
  - 临界（接近超支或即将到期）：橙色
  - 超支/锁定/未到账：红色

### 16.2 Dashboard（首页，人力维度主视图）

#### A. 顶部 KPI 条
- KPI1：`Total Allocated Budget`
- KPI2：`Total Gap($)`
- KPI3：`Overrun BP Count`
- KPI4：`Received BP Count / Total BP`
- KPI5：`Uncovered Resource Count`

#### B. 第一屏主表（按你的要求）
- 列：`Resource ID | Project code | Resource Name | BP ID | Allocated budget`
- 支持：排序、筛选、导出当前结果
- 行点击：进入 Resource 详情抽屉（右侧）

#### C. 第二屏图表区
- 图1：`Monthly Coverage Heatmap`（资源 × 月份，显示 FTE）
- 图2：`Gap by Resource` 条形图
- 图3：`BP Burn-down`（预算消耗趋势）

### 16.3 Resource（Supply）页面

#### A. 列表区
- 关键列：
  `Resource ID / cTool ID / Resource Name / Contract Type / City / Pod / Role End Date / 2026 GPDM Rate($) / Gap($)`
- 快速筛选：`Perm/Non-Perm`、`City`、`Role End Date` 区间、`Gap > 0`

#### B. 行展开（12个月覆盖）
- 月度矩阵：`2025 Dec FTE` 到 `2026 Dec FTE`
- 每月显示：`总FTE` + 对应 `Gap($)`
- 0 FTE 月份红底强调

#### C. 详情抽屉
- 基本资料、manager/cost center（后续字段补齐）
- 该资源的 BP/Clarity 分配明细时间线

### 16.4 Allocation 页面（核心编辑）

#### A. 编辑网格
- 主键维度：`Resource × Month`
- 可新增多条分配行到不同 `Clarity ID`
- 每条行字段：`Project code / BP ID / Clarity ID / FTE / Allocate budget($)`

#### B. 即时校验
- 月度总 FTE > 1.0：禁止保存
- BP 未到账（非 Received）：禁止选择
- BP 到期且锁定：不可写；若 BM 解锁后可写

#### C. 辅助能力
- 自动计算剩余可分配 FTE（例如当月已分配 0.7，则剩余 0.3）
- “推荐补洞 BP”按钮：按优先级给候选（快到期→可刚好用完→余额最多）

### 16.5 Gap（Demand）页面

#### A. Gap 主表（按人）
- 列：`Resource ID / Resource Name / Contract Type / City / Annual Gap($) / Gap Months / Suggested BP`
- 支持按 `Gap($)` 倒序，快速定位高优先级对象

#### B. 右侧建议面板
- 展示该资源可匹配 BP 候选列表：
  `BP ID / BP Name / Remaining / Expire Date / Match Score / Recommended FTE`
- 支持“一键带入 Allocation 草稿”

#### C. 招聘建议卡
- 按城市输出可新增容量：
  - Perm：按 12 个月费用
  - Non-Perm：按最小 3 个月

### 16.6 BP/Clarity 页面

#### A. BP 列表
- 列：`BP ID / BP Name / Project code / Status / Window / Total Budget / Allocated / Remaining / Overrun Flag / Lock Status`
- 明显标识：超支、未到账、已锁定

#### B. BP 详情
- Clarity 子表：`Clarity ID / Clarity Name / Allocated / Remaining`
- 操作日志：解锁记录（操作人、时间、原因）

### 16.7 Import/Export 页面

#### A. 上传与预检查
- 上传后显示“变更对比表”：
  - `Row Key`
  - `Original Value`
  - `New Value`
  - `Changed Fields`
  - `Confirm`（逐条勾选）
- 规则：不阻断，但必须逐条确认后才能“最终导入”

#### B. 导出
- 支持“按当前筛选结果导出 Excel”
- 支持导出对象：`Resource / BP/Clarity / Allocation / Gap`

### 16.8 交互与权限落地

- BM：拥有编辑、解锁、导入确认权限
- SME：仅查看与导出
- 所有变更（尤其 Allocation 与 BP 解锁）需有历史记录

## 17. 给 BM 的阅读与使用方式（你可以这样看）

如果你不看代码，只需要按下面顺序看文档即可：

1. **先看业务规则是否正确**
   - 看第 `3~6` 章（时间口径、Resource 规则、BP/Clarity 规则、Gap 公式）。
   - 目标：确认“算钱方式”和“分配约束”都符合你实际工作。

2. **再看角色权限是否正确**
   - 看第 `10` 章。
   - 目标：确认 BM 能编辑、SME 只读、是否有审批流。

3. **再看导入导出是否可用**
   - 看第 `11` 和第 `15` 章。
   - 目标：确认导入顺序、逐条对比确认、是否支持按筛选导出。

4. **最后看页面长什么逻辑**
   - 看第 `16` 章（FE UI 低保真方案）。
   - 目标：确认每个页面“看什么、点哪里、怎么改”。

### 17.1 你最关心的 4 个页面，建议先看

- `Dashboard`：先总览团队与预算状态。
- `Allocation`：你日常实际调整人力分配的主页面。
- `Gap`：快速看谁还差钱、系统建议用哪个 BP 补。
- `Import/Export`：批量更新和导出报表。

### 17.2 我们下一步怎么协作（最省力）

你每次只需要回复三类信息，我就能继续往前推进：

- **A. 哪条规则不对**（例如：某地区 rate、某个状态约束）
- **B. 哪个页面不好用**（例如：要多一个筛选或列）
- **C. 哪个字段要新增/改名**

我会把你的反馈直接更新到同一份文档，再给你一个“变更摘要”，你不用自己比对全部内容。

## 18. 不是“记录”，而是可执行方案（MVP 可直接开工）

这部分把前面的规则转成“开发任务 + 页面动作 + 验收标准”。

### 18.1 MVP 范围（第一期必须交付）

- P0-1：Dashboard 首页（人力视角）
- P0-2：Allocation 编辑页（支持按月拆分到 Clarity）
- P0-3：Gap 页面（按人显示缺口 + 推荐 BP）
- P0-4：BP/Clarity 页面（状态、剩余、锁定、日志）
- P0-5：Import/Export（逐条差异确认导入、按筛选导出）

> 说明：Resource 页面可由 Dashboard + Gap 的明细抽屉覆盖核心能力，后续再独立增强。

### 18.2 页面级“你能做什么”（操作清单）

#### A. Dashboard
你可以：
1. 先用筛选器选 `Budget Cycle / City / Contract Type / BP Status`。
2. 在主表快速看到：`Resource ID / Project code / Resource name / BP ID / Allocated budget`。
3. 点某一行打开详情抽屉，看到这个人每月 FTE、Gap 和当前分配去向。
4. 一键导出当前筛选结果（Excel）。

#### B. Allocation
你可以：
1. 选择某个 Resource + Month，给多个 Clarity 分配 FTE（例如 0.3 + 0.7）。
2. 系统实时阻止错误：
   - 当月总 FTE > 1.0
   - BP 非 Received
   - BP 已到期且未解锁
3. 保存后自动重算 Allocate budget 与 Gap。

#### C. Gap
你可以：
1. 直接看到谁 gap 最大（按金额排序）。
2. 点开某人，看系统建议的 BP 候选（按优先级）。
3. 一键把建议带入 Allocation 草稿，再确认保存。

#### D. BP/Clarity
你可以：
1. 看每个 BP 的总额、已分配、剩余、是否超支、是否锁定。
2. 点 BP 看下属 Clarity 分配情况。
3. BM 可执行“解锁”，系统自动写入日志（人/时间/原因）。

#### E. Import/Export
你可以：
1. 上传 Excel 后先看“逐条差异对比”（旧值 vs 新值）。
2. 逐条勾选确认后才导入。
3. 导出当前筛选后的结果（不是全量）。

### 18.3 关键计算（系统自动算）

- 月成本：`allocated_cost = month_fte × month_rate`
- 月缺口：`gap_cost = max(0, 1 - month_total_fte) × month_rate`
- 年缺口：12 个月 `gap_cost` 累加
- BP 剩余：`bp_remaining = bp_total_budget - bp_allocated_budget`
- 超支标识：`bp_remaining < 0` => 红色 Overrun

### 18.4 3 个真实示例（便于你验收）

#### 示例 1：同月分摊到两个 BP
- 某资源 2026-03：
  - Clarity A（BP 2500113）分配 0.6
  - Clarity B（BP 2501970）分配 0.4
- 结果：当月总 FTE=1.0，Gap=0。

#### 示例 2：未到账 BP 禁分配
- 你尝试把 0.3 FTE 分给状态 `Committed` 的 BP。
- 系统应：禁止保存，并提示“BP 未到账，不能分配”。

#### 示例 3：导入差异确认
- Excel 中某行 `City: GZ -> HK`，`Rate: 9.182 -> 15.212`。
- 系统应：在预检查界面高亮这两个字段变化，需你勾选确认后才能导入。

### 18.5 验收标准（UAT）

- UAT-1：任意月份，系统不允许保存 `Resource 月总 FTE > 1.0`。
- UAT-2：非 Received 的 BP 不可用于 Allocation。
- UAT-3：Gap 页面可按金额排序，且可跳转到 Allocation 草稿。
- UAT-4：导入必须逐条确认差异，未确认的数据不得入库。
- UAT-5：BM 执行 BP 解锁后，日志中可查到人/时间/原因。

## 19. 你现在怎么“看到东西”（给 BM 的最短路径）

- 第一步看第 `18.2`：这里是“你在系统里到底能点什么”。
- 第二步看第 `18.4`：这里是“真实业务会怎么跑”。
- 第三步看第 `18.5`：这里是“验收时怎么判断系统合格”。

如果你愿意，下一步我可以把第18章再升级成：
- 每个页面的“表头草图”（列名顺序）
- 每个按钮的“点击后行为”
- 一份你可直接给开发的任务拆分（前端/后端/测试）

## 20. 我想直接看页面：本地查看方式（5分钟）

你现在可以直接打开我做的原型页面：`prototype/index.html`。

### 20.1 最简单方式
- 直接双击文件：`prototype/index.html`

### 20.2 推荐方式（本地起服务）
在项目根目录执行：

```bash
python -m http.server 4173 --directory prototype
```

然后浏览器访问：

- `http://localhost:4173`

### 20.3 你会看到什么
- 可切换页面 Tab：`Dashboard / Allocation / Gap / BP/Clarity / Import/Export`
- Dashboard 第一屏主表就是你指定的 5 个字段
- Allocation 演示了“未到账 BP 禁分配、FTE 上限 1.0”等规则
- Import 页面演示了“old vs new 逐条确认”

### 20.4 文件位置
- 原型文件：`prototype/index.html`
- 需求文档：`docs/requirements_v3.md`


## 21. 新增：手动录入字段并自动关联六页面

为满足“先手动输入字段，再自动关联展示”的需求，原型已新增 `Data Entry` 页面：

- 你可在 Data Entry 一次输入主字段（Resource/BP/Clarity/Month/FTE/预算/Gap/状态等）。
- 点击“新增/更新数据行”后，会自动同步到六个业务页面：
  1. Dashboard
  2. Resource
  3. Allocation
  4. Gap
  5. BP/Clarity
  6. Import/Export
- Import/Export 页面会基于“上一版快照 vs 当前输入”自动生成差异字段，支持逐条核对。

> 入口文件：`prototype/index.html`。

## 22. 是的，需要 BE：已新增后端接口（不只是原型）

你说得对，产品要真正可用必须有后端（BE）。目前我已经补了一个可运行的基础后端：

- 文件：`backend/server.py`
- 端口：`8000`
- 存储：`SQLite`（`backend/budget.db`）
- 能力：保存 Data Entry 数据、读取并返回六页面所需聚合数据

### 22.1 已提供 API
- `GET /health`
- `GET /api/fields`
- `GET /api/rows`
- `POST /api/rows`（批量 upsert）
- `DELETE /api/rows`
- `GET /api/dashboard`
- `GET /api/resource`
- `GET /api/allocation`
- `GET /api/gap`
- `GET /api/bp`

### 22.2 你怎么跑起来

```bash
# 启动后端
python backend/server.py

# 启动前端原型
python -m http.server 4173 --directory prototype
```

然后：
- 前端：`http://localhost:4173`
- 后端健康检查：`http://localhost:8000/health`

### 22.3 前端和后端如何联动

在 Data Entry 页面新增了两个按钮：
- `保存到BE`：把当前录入数据写入后端
- `从BE加载`：从后端拉取数据并刷新六个页面

> 这样就不再只是“页面演示”，而是具备了最基础的数据持久化与联动能力。
