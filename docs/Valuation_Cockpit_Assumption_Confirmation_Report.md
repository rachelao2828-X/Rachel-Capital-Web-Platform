# Valuation Cockpit Assumption Confirmation Report

## 1. 功能目的

V0.5 关键假设确认页用于 Rachel Capital OS localhost Valuation Cockpit 的“未上市 / 一级市场估值”板块。它将项目资料和 Excel / CSV 财务模型中提取出的关键估值假设汇总为标准化表格，供用户确认、修改、剔除和补充。

本阶段不做自动最终估值计算，只为 V0.6 自动估值计算准备可靠输入。

## 2. 为什么需要关键假设确认页

BP、商业计划书和财务模型通常来自项目方预测，可能存在乐观假设、口径不一致、缺失数据或公式错误。进入自动估值计算前，必须由用户确认核心收入、成本、现金流、CAPEX、估值、团队和退出路径假设。

## 3. 10 类关键假设

1. 项目基本假设
2. 融资与估值假设
3. 收入假设
4. 成本与利润假设
5. 现金流假设
6. CAPEX 与产能假设
7. 回报与估值计算假设
8. 情景与敏感性假设
9. 创始团队假设
10. 风险与缺失数据假设

## 4. 数据结构

每条假设包含：

- field
- extracted_value
- confirmed_value
- unit
- period
- source
- source_file
- source_location
- confidence
- needs_confirmation
- use_in_valuation
- notes

顶层结构包含：

- target_name
- source_files
- assumption_groups
- warnings
- readiness_summary
- ready_for_valuation_calculation
- valuation_inputs

## 5. 用户确认逻辑

用户可以在页面中逐项编辑：

- 用户确认值
- 单位
- 期间 / 情景
- 是否需要继续确认
- 是否用于估值
- 备注

系统提取值、来源和可信度用于审计追踪，默认不建议直接改写。

## 6. 估值准备度评分

准备度分为：

- 高：关键收入、成本、现金流、CAPEX、融资估值、退出路径较完整。
- 中：收入和部分成本完整，但现金流、CAPEX、融资估值或退出路径缺失。
- 低：只有部分商业或融资信息，关键财务假设不足。
- 不足：无法进入估值计算。

输出字段：

- valuation_readiness_level
- reason
- ready_for_v0_6_calculation
- missing_before_calculation

## 7. JSON 保存路径

确认结果保存到本地私有目录：

```text
/Users/rachelao/Documents/Rachel Capital Web Platform/data/private_market_cases/
```

文件名：

```text
项目名称_YYYY-MM-DD_关键假设确认.json
```

该目录不得提交到 Git，不得放入 public_site。

## 8. Obsidian 输出路径

关键假设确认报告输出到：

```text
/Users/rachelao/Documents/Rachel Capital/15_估值引擎/关键假设确认/
```

frontmatter 默认：

```text
type: private_market_assumption_confirmation
status: draft
public: false
```

## 9. 与 V0.6 自动估值计算的关系

V0.6 自动估值计算只读取：

- confirmed_value
- use_in_valuation = true
- confidence 不为 缺失

V0.5 保存的 JSON 已预留：

```json
{
  "ready_for_valuation_calculation": false,
  "valuation_inputs": {
    "revenue": {},
    "cost_profit": {},
    "cash_flow": {},
    "capex_capacity": {},
    "return_valuation": {},
    "scenario_sensitivity": {}
  }
}
```

## 10. 隐私与安全边界

- 本功能仅用于 localhost。
- 不发布 GitHub Pages。
- 不修改 public_site。
- 不保存上传文件、解析结果或确认结果到 public_site。
- 所有 Obsidian 输出默认 public: false。
- 不输出买入、卖出、推荐、目标价或收益承诺。

## 11. 当前限制

- 当前假设表由规则抽取生成，复杂表格和非标准 BP 表述可能需要用户人工校正。
- 暂不做自动估值计算。
- 暂不做合同、订单、流水、审计数据的外部交叉验证。
- 暂不做 Excel 与 BP 冲突的自动强校验。

## 12. 下一步计划

- V0.6 自动估值计算读取 confirmed valuation_inputs。
- 增加 BP 与 Excel 冲突检测。
- 增加用户补充假设的结构化新增行。
- 增加行业模板化假设校验。
- 增加 DCF、IRR、收入倍数、融资锚定等多模型计算。
