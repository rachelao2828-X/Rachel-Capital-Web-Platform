# Valuation Cockpit V0.7 Multi-Model Comparison Report

## 1. 功能目的

V0.7 多模型估值对比与综合区间用于 Rachel Capital OS localhost Valuation Cockpit 的“未上市 / 一级市场估值”板块。它基于 V0.6 基础估值计算结果，对多个估值模型进行权重分配、结果对比、分歧度解释、综合置信度判断和 Obsidian 报告输出。

本模块仅生成内部研究草稿，不构成投资建议、投资邀约、买卖依据、目标价或收益承诺。

## 2. 为什么需要多模型估值对比

一级市场项目通常缺少统一市场报价，单一模型容易被某一项假设放大。多模型对比可以帮助用户识别：

- 倍数法与现金流法之间的差异。
- 资产重估结果与经营现金流结果之间的差异。
- 数据缺失、预测偏乐观或模型不适配造成的估值分歧。
- 哪些模型适合作为主参考，哪些模型只适合作为辅助校验。

## 3. 输入来源

V0.7 支持两种输入：

- 当前页面 session 中的 V0.6 基础估值计算结果。
- 本地 `data/private_market_cases/` 中已保存的 `项目名称_YYYY-MM-DD_基础估值计算.json`。

模块只读取本地 JSON，不读取 `public_site`。

## 4. 模型权重规则

系统根据标的类型选择默认权重：

- 未上市成长公司：收入倍数法优先，EBITDA、利润、DCF、订单和资产重估作为组合参考。
- 一级市场融资标的：收入、利润、EBITDA 和订单倍数优先，DCF 和资产重估作为辅助。
- 项目公司 / SPV：DCF、IRR / 回收期、EBITDA、资产重估和收入倍数共同校验。
- 资产型项目：资产重估、DCF、EBITDA、收入倍数和 IRR / 回收期共同校验。

不可计算模型会自动剔除，其默认权重会在剩余纳入模型之间归一化。

## 5. 用户调整权重逻辑

页面展示模型权重表，用户可以：

- 修改“用户调整权重”。
- 勾选或取消“是否纳入综合区间”。
- 保留系统默认权重原因和模型置信度。

如果用户调整后的权重总和不等于 100%，系统自动在纳入模型之间归一化。

## 6. 加权综合估值区间计算方法

系统使用 V0.6 模型结果中的 `low`、`base`、`high`。如果模型只有单一估值，则视为 `low = base = high`。

计算方式：

- 加权 low = Σ(模型 low × 归一化权重)
- 加权 base = Σ(模型 base × 归一化权重)
- 加权 high = Σ(模型 high × 归一化权重)

输出包括保守估值、中性估值、乐观估值、权重来源、纳入模型数量和剔除模型数量。

## 7. 模型分歧度规则

系统使用纳入模型的 base 估值计算：

- `min_value`
- `max_value`
- `spread_ratio = max_value / min_value`

分歧等级：

- `< 1.5`：低
- `1.5 - 2.5`：中
- `2.5 - 4`：高
- `>= 4`：极高
- 无法计算：无法判断

## 8. 综合置信度规则

综合置信度分为：

- 高
- 中
- 低
- 仅供框架参考

判断因素包括可纳入模型数量、V0.5 估值准备度、数据缺失数量、模型分歧度、是否包含 DCF / 现金流模型、是否包含收入 / 利润 / EBITDA 基础数据，以及关键风险是否仍未确认。

## 9. JSON 保存路径

多模型估值结果保存到：

```text
/Users/rachelao/Documents/Rachel Capital Web Platform/data/private_market_cases/项目名称_YYYY-MM-DD_多模型估值对比.json
```

该目录已在 `.gitignore` 中，不应提交到 Git。

## 10. Obsidian 输出路径

Obsidian 报告输出到：

```text
/Users/rachelao/Documents/Rachel Capital/15_估值引擎/多模型估值对比/项目名称_YYYY-MM-DD_多模型估值对比.md
```

frontmatter 必须包含 `public: false`。

## 11. 与 V0.8 投资备忘录的关系

V0.7 结果中预留：

```json
"for_v0_8_decision_memo": {
  "valuation_range": {},
  "confidence_level": "",
  "key_assumptions": [],
  "major_risks": [],
  "data_gaps": [],
  "questions_for_company": [],
  "recommended_research_action": ""
}
```

V0.8 可以在此基础上生成内部投资备忘录草稿。`recommended_research_action` 只能使用“进入观察池”“需要补充数据”“进入深度研究”“暂不进入估值”“等待更多财务或项目数据”等研究动作，不得输出交易建议。

## 12. 隐私与安全边界

- 仅用于 localhost。
- 不发布 GitHub Pages。
- 不修改 `public_site`。
- 不把上传文件、解析结果或估值结果放入 `public_site`。
- 不提交 `data/private_market_cases/`。
- 不输出买入、卖出、推荐、目标价或收益承诺。
- 所有 Obsidian 输出默认 `public: false`。

## 13. 当前限制

- 默认权重是规则化建议，不替代人工判断。
- 当前图表以 Streamlit 原生柱状图为主。
- 模型分歧来源为启发式识别，仍需结合原始资料复核。
- 可比公司、可比交易、行业估值分位和更复杂的 DCF 尚未接入。

## 14. 下一步计划

- V0.8：基于 V0.7 结果生成内部投资备忘录草稿。
- 增加可比公司和可比交易样本库。
- 增加权重敏感性分析。
- 增加模型结果版本管理和项目案例库复盘。
