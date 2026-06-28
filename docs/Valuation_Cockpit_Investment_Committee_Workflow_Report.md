# Valuation Cockpit V1.0 Investment Committee Workflow Report

## 1. 功能目的

V1.0 在未上市 / 一级市场估值模块中新增“投资委员会工作流 / 决策闸门”，用于把 V0.9 项目观察池记录推进到内部流程管理环节。

本功能只生成流程动作、检查表、Memo 草稿、决策日志和状态推进记录，不生成自动投资决策。

## 2. 输入来源

- 当前 Streamlit session 中的 V0.9 项目跟踪记录
- `data/private_market_cases/` 中保存的项目跟踪记录 JSON
- 手动填写的项目基础信息

第一版暂不读取 `public_site`，Obsidian 项目卡片 Markdown 读取作为后续预留。

## 3. 决策阶段定义

- 初筛
- 观察池复查
- 深度尽调立项
- 投委会预审
- 投委会讨论
- 投资决策候选
- 暂缓
- 放弃
- 归档

系统会根据当前项目状态给出默认阶段，用户可以人工调整。

## 4. 决策准备度规则

- 高：项目卡片、Memo、估值摘要、风险清单、尽调问题和跟踪任务较完整，主要缺口较少。
- 中：具备 Memo、估值摘要、主要风险和尽调问题，但仍有数据缺口。
- 低：已有项目卡片或基础项目记录，但财务、估值或尽调结果仍不完整。
- 不足：缺少项目摘要、财务数据、估值结果和尽调结论。

## 5. 决策闸门检查表

检查表包含 10 类：

1. 项目资料完整性
2. 团队闸门
3. 技术闸门
4. 产品与客户闸门
5. 市场与竞争闸门
6. 财务闸门
7. 估值闸门
8. 风险闸门
9. 退出路径闸门
10. 决策流程闸门

每个检查项包含状态、证据、风险等级和备注。

## 6. 一票否决风险规则

系统会识别并标记高风险项，包括团队履历严重缺失、财务数据完全缺失、客户合同无法验证、核心技术无法验证、重大合规风险、估值明显偏离、退出路径完全不清楚、系统推断无法验证，以及重大债务、诉讼、环保或监管风险。

系统不会自动放弃项目，只会提示进入人工风险复核。

## 7. 投委会 Memo 结构

投委会 Memo 草稿包括：

- 项目快照
- 投资逻辑草案
- 核心价值驱动因素
- 估值摘要
- 决策闸门检查表
- 一票否决风险
- 主要风险
- 尽调进展
- 数据缺口
- 投委会需要讨论的问题
- 系统建议流程动作
- 人工复核意见
- 后续任务

## 8. 人工复核机制

页面提供人工复核意见填写区，支持复核人、日期、核心判断、最大吸引力、最大风险、必须补充的数据、外部专家、财务尽调、法律尽调、技术尽调和本次流程动作。

所有关键输出均需人工复核后才能进入下一步。

## 9. 流程动作定义

- 继续观察
- 补充资料后复查
- 启动深度尽调
- 提交投委会预审
- 进入投资决策候选
- 暂缓
- 归档
- 人工风险复核

这些动作是研究流程动作，不是投资建议。

## 10. 项目状态推进规则

- 继续观察：项目状态为新建观察或初步解析完成，观察池状态为 active，30 天后复查。
- 补充资料后复查：项目状态为等待资料，观察池状态为 pending_data，14 天后复查。
- 启动深度尽调：项目状态为深度尽调中，观察池状态为 deep_research_candidate，7 天后复查。
- 提交投委会预审：项目状态为深度尽调中，观察池状态为 investment_decision_candidate，7 天后复查。
- 进入投资决策候选：项目状态为已进入投资决策，观察池状态为 investment_decision_candidate，7 天后复查。
- 暂缓：项目状态为暂缓跟踪，观察池状态为 paused，60 天后复查。
- 归档：项目状态为已归档，观察池状态为 archived，不设置复查日期。
- 人工风险复核：项目状态为待深度尽调，观察池状态为 deep_research_candidate，7 天后复查。

## 11. JSON 保存路径

本地 JSON 保存到：

```text
/Users/rachelao/Documents/Rachel Capital Web Platform/data/private_market_cases/
```

文件名：

```text
项目名称_YYYY-MM-DD_投委会决策记录.json
```

该目录已纳入 `.gitignore`，不提交 Git。

## 12. Obsidian 投委会 Memo 输出路径

```text
/Users/rachelao/Documents/Rachel Capital/16_投资决策引擎/投委会Memo/
```

文件名：

```text
项目名称_YYYY-MM-DD_投委会Memo.md
```

frontmatter 必须包含 `public: false`。

## 13. Obsidian 决策日志输出路径

```text
/Users/rachelao/Documents/Rachel Capital/16_投资决策引擎/决策日志/
```

文件名：

```text
项目名称_YYYY-MM-DD_决策日志.md
```

frontmatter 必须包含 `public: false`。

## 14. 项目卡片状态更新方式

`update_project_card_status()` 会优先更新项目卡片 frontmatter 中的：

- updated
- project_status
- watchlist_status
- next_review_date
- process_action

随后在“后续复查记录”中追加 V1.0 状态推进记录。如果项目卡片不存在，会自动创建基础项目卡片。

## 15. 观察池更新方式

复用并扩展 `update_private_market_project_watchlist()`，支持 V1.0 decision package。

观察池会更新或新增对应项目行，包括项目状态、观察池状态、流程动作、估值置信度、下次复查日期和项目卡片链接。

## 16. 与 V1.1 决策后跟踪的关系

V1.0 在 `decision_package` 中预留：

```json
"for_v1_1_post_decision_tracking": {
  "target_name": "",
  "process_action": "",
  "next_project_status": "",
  "next_watchlist_status": "",
  "next_review_date": "",
  "follow_up_tasks": [],
  "decision_log_path": "",
  "committee_memo_path": "",
  "project_card_path": "",
  "watchlist_path": ""
}
```

V1.1 可继续用于决策后任务跟踪、复查提醒、项目状态看板、跟踪复盘和月度项目池复盘。

## 17. 隐私与安全边界

- 仅用于 localhost 内部流程管理
- 不发布 GitHub Pages
- 不修改 `public_site`
- 不保存到公开目录
- 所有 Obsidian 输出 `public: false`
- 所有流程动作均需人工复核
- 不提交上传文件、解析结果和私有案例 JSON

## 18. 当前限制

第一版主要从 V0.9 项目跟踪记录、项目卡片摘要、数据缺口、风险清单和跟踪任务中生成闸门判断。复杂交易条款、法律合规、技术验证和客户合同真实性仍需要人工尽调。

## 19. 下一步计划

- 增强 Obsidian 项目卡片读取
- 增强 frontmatter 结构化更新
- 接入 V1.1 决策后任务追踪
- 增加项目状态看板
- 增加月度项目池复盘视图
