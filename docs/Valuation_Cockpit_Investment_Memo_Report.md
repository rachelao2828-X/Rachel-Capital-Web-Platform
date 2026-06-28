# Valuation Cockpit V0.8 Investment Memo Report

## 1. 功能目的

V0.8 投资备忘录 / 尽调问题 / 研究动作建议整合页用于 Rachel Capital OS localhost Valuation Cockpit 的“未上市 / 一级市场估值”板块。它把 V0.3 到 V0.7 的项目资料解析、财务模型解析、关键假设确认、基础估值计算和多模型估值对比整合为内部投研 Memo 草稿。

本模块输出仅用于内部研究，不构成投资建议、投资邀约、买卖依据、目标价或收益承诺。

## 2. 输入来源

V0.8 支持两类输入：

- 当前页面 `session_state`：项目资料解析、财务模型解析、关键假设确认、基础估值计算、多模型估值对比。
- 本地 JSON：`data/private_market_cases/`、`data/extracted/private_market/`、`data/extracted/private_market_financials/` 中的本地文件。

模块只读取本地 JSON，不读取 `public_site`。

## 3. Memo 完整度判断

- 高：同时具备项目资料解析、财务模型解析、关键假设确认、基础估值计算和多模型估值对比。
- 中：具备项目资料解析、关键假设确认和至少一种估值计算结果。
- 低：只具备项目资料解析、财务模型解析或关键假设确认。
- 不足：缺少项目摘要、财务数据、融资信息和估值结果，无法形成有效 Memo。

## 4. 投资备忘录结构

投资备忘录草稿包含：

- 项目快照
- 创始团队评估
- 商业模式评估
- 技术与壁垒评估
- 产品与客户评估
- 市场与竞争评估
- 财务与经营评估
- 融资与估值评估
- 主要风险
- 尽调问题清单
- 数据缺口
- 研究动作建议
- 后续研究任务
- 免责声明

## 5. 尽调问题生成规则

系统按以下分类生成问题：

- 团队尽调
- 技术尽调
- 产品与客户尽调
- 市场与竞争尽调
- 财务尽调
- 融资与股权结构尽调
- 法务与合规尽调
- 退出路径尽调

每类至少生成 3 个具体、可执行问题。若创始团队、财务数据、客户订单、估值信息或技术信息缺失，对应问题会被标记为更高优先级。

## 6. 研究动作建议规则

研究动作建议只能使用：

- 进入观察池
- 需要补充数据
- 进入深度研究
- 暂不进入估值
- 等待更多财务或项目数据

禁止输出买入、卖出、推荐、增持、减持、目标价、收益预测或应该投资等表达。

## 7. JSON 保存路径

V0.8 结果保存到：

```text
/Users/rachelao/Documents/Rachel Capital Web Platform/data/private_market_cases/项目名称_YYYY-MM-DD_投资备忘录整合.json
```

该目录已在 `.gitignore` 中，不应提交到 Git。

## 8. Obsidian 投资备忘录输出路径

```text
/Users/rachelao/Documents/Rachel Capital/16_投资决策引擎/投资备忘录/项目名称_YYYY-MM-DD_投资备忘录草稿.md
```

frontmatter 必须包含 `public: false`。

## 9. Obsidian 尽调问题清单输出路径

```text
/Users/rachelao/Documents/Rachel Capital/16_投资决策引擎/尽调问题清单/项目名称_YYYY-MM-DD_尽调问题清单.md
```

frontmatter 必须包含 `public: false`。

## 10. 与 V0.9 项目跟踪的关系

V0.8 在 `memo_data` 中预留：

```json
"for_v0_9_project_tracking": {
  "target_name": "",
  "research_action": "",
  "follow_up_tasks": [],
  "data_gaps": [],
  "questions_for_company": [],
  "next_review_date": "",
  "watchlist_status": ""
}
```

V0.9 可基于该字段建设项目观察池、跟踪任务、下次复查日期、项目状态更新和 Obsidian 项目卡片。

## 11. 隐私与安全边界

- 仅用于 localhost。
- 不发布 GitHub Pages。
- 不修改 `public_site`。
- 不把上传文件、解析结果、估值结果或投资备忘录放入 `public_site`。
- 不提交 `data/private_market_cases/`、`data/uploads/`、`data/extracted/`。
- 所有 Obsidian 输出默认 `public: false`。
- 所有结论均需人工复核。

## 12. 当前限制

- Memo 仍是规则化草稿，不替代人工投研判断。
- 尽调问题为通用模板叠加数据缺口优先级，尚未接入外部资料核验。
- 研究动作建议只基于本地已读取数据，不代表最终投资决策。
- 未接入项目观察池和任务提醒。

## 13. 下一步计划

- V0.9：项目观察池、项目状态跟踪和下次复查日期。
- 增加 Obsidian 项目卡片自动生成。
- 增加尽调问题完成状态和资料回收记录。
- 增加 Memo 版本对比和复盘机制。
