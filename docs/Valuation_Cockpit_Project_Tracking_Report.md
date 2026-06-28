# Valuation Cockpit V0.9 Project Tracking Report

## 1. 功能目的

V0.9 项目观察池 / 跟踪任务 / 项目卡片用于 Rachel Capital OS localhost Valuation Cockpit 的“未上市 / 一级市场估值”板块。它把 V0.8 投资备忘录整合结果沉淀为可持续维护的项目观察池记录、Obsidian 项目卡片和后续跟踪任务。

本模块仅用于内部研究观察，不构成投资建议、投资邀约、买卖依据、目标价或收益承诺。

## 2. 输入来源

V0.9 支持：

- 当前页面 `session_state` 中的 V0.8 投资备忘录整合结果。
- 本地 `data/private_market_cases/` 中的 `项目名称_YYYY-MM-DD_投资备忘录整合.json`。
- 手动填写项目观察池信息。

模块只读取本地 JSON，不读取 `public_site`。

## 3. 项目状态定义

支持以下项目状态：

- 新建观察
- 等待资料
- 初步解析完成
- 估值框架完成
- 待深度尽调
- 深度尽调中
- 暂缓跟踪
- 已放弃
- 已进入投资决策
- 已归档

默认由 V0.8 研究动作映射生成，用户可在页面手动调整。

## 4. 观察池状态定义

支持以下观察池状态：

- `active`：观察中
- `pending_data`：等待资料
- `deep_research_candidate`：深度研究候选
- `paused`：暂缓
- `archived`：已归档
- `rejected`：已放弃
- `investment_decision_candidate`：投资决策候选

## 5. 下次复查日期规则

- 观察中：默认 30 天后复查。
- 等待资料：默认 14 天后复查。
- 深度研究候选：默认 7 天后复查。
- 暂缓：默认 60 天后复查。
- 已放弃 / 已归档：默认不设复查日期。

用户可以手动修改复查日期。

## 6. 项目卡片结构

项目卡片包含项目名称、公司名称、行业、Rachel 战略生态、标的类型、项目阶段、地区、一句话摘要、团队摘要、商业模式摘要、技术摘要、产品客户摘要、市场摘要、财务摘要、融资摘要、估值摘要、风险摘要、Memo 完整度、估值置信度、研究动作、项目状态、观察池状态、下次复查日期、来源文件、关联文件和标签。

## 7. 跟踪任务生成规则

系统会根据以下内容生成跟踪任务：

- 数据缺口。
- 尽调问题。
- 低估值置信度。
- 缺失创始团队信息。
- 缺失客户合同信息。
- 退出路径不清楚。
- 项目进入深度研究。

任务分类包括资料补充、团队尽调、技术尽调、客户尽调、财务尽调、法务合规、估值复核、产业研究、退出路径和内部复盘。

## 8. JSON 保存路径

```text
/Users/rachelao/Documents/Rachel Capital Web Platform/data/private_market_cases/项目名称_YYYY-MM-DD_项目跟踪记录.json
```

该目录已在 `.gitignore` 中，不应提交到 Git。

## 9. Obsidian 项目卡片输出路径

```text
/Users/rachelao/Documents/Rachel Capital/03_公司数据库/一级市场项目/项目名称.md
```

frontmatter 必须包含 `public: false`。

## 10. Obsidian 项目跟踪任务输出路径

```text
/Users/rachelao/Documents/Rachel Capital/16_投资决策引擎/项目跟踪任务/项目名称_YYYY-MM-DD_项目跟踪任务.md
```

frontmatter 必须包含 `public: false`。

## 11. Obsidian 项目观察池总览输出路径

```text
/Users/rachelao/Documents/Rachel Capital/03_公司数据库/一级市场项目/一级市场项目观察池.md
```

生成或更新时，同名项目行会被替换，其他项目行会保留。

## 12. 与 V1.0 投资委员会工作流的关系

V0.9 在 `tracking_record` 中预留：

```json
"for_v1_0_portfolio_decision": {
  "target_name": "",
  "project_status": "",
  "research_action": "",
  "valuation_summary": {},
  "memo_links": [],
  "tracking_tasks": [],
  "next_review_date": "",
  "decision_readiness": "",
  "suggested_next_gate": ""
}
```

V1.0 可基于该字段建设投资委员会工作流、决策候选池、决策闸门和投后跟踪框架。

## 13. 隐私与安全边界

- 仅用于 localhost。
- 不发布 GitHub Pages。
- 不修改 `public_site`。
- 不把上传文件、解析结果、估值结果、投资备忘录或项目观察池放入 `public_site`。
- 不提交 `data/private_market_cases/`、`data/uploads/`、`data/extracted/`。
- 所有 Obsidian 输出默认 `public: false`。
- 项目状态和研究动作均需人工复核。

## 14. 当前限制

- 观察池总览更新以 Markdown 表格行为基础，复杂手工格式可能无法完整保留。
- 跟踪任务为规则化生成，仍需人工调整优先级和截止日期。
- 项目卡片尚未自动回链所有历史 Obsidian 文件。
- 未接入提醒、日历、任务完成状态持久化。

## 15. 下一步计划

- V1.0：投资委员会工作流和决策闸门。
- 增加任务完成状态更新。
- 增加项目复查提醒。
- 增加项目卡片与 Memo、尽调问题、估值报告的自动双链。
