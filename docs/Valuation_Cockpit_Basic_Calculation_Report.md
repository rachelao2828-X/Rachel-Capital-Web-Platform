# Valuation Cockpit Basic Calculation Report

## 1. 功能目的

V0.6 基础估值自动计算用于 Rachel Capital OS localhost Valuation Cockpit 的“未上市 / 一级市场估值”板块。它基于 V0.5 已确认关键假设，生成基础模型计算结果、初步估值区间、缺失数据和敏感性提示。

本阶段只生成内部研究草稿，不构成投资建议、投资邀约、买卖依据、目标价或收益承诺。

## 2. 为什么 V0.6 必须基于 V0.5 已确认假设

一级市场估值高度依赖假设质量。项目方 BP 和财务模型中的收入、成本、现金流、CAPEX、倍数和退出路径可能存在乐观假设或口径不一致。V0.6 只读取：

- confirmed_value
- use_in_valuation = true
- confidence 不为“缺失”

未经确认的 extracted_value 不作为正式估值输入。

## 3. 支持的基础估值模型

V0.6 支持：

1. 收入倍数法
2. 利润倍数法
3. EBITDA 倍数法
4. 订单倍数法
5. DCF 简化法
6. IRR / 投资回收期校验
7. 资产重估 / 重置成本法

## 4. 输入字段要求

主要输入来自 V0.5 JSON 的 valuation_inputs：

- revenue
- cost_profit
- cash_flow
- capex_capacity
- return_valuation
- scenario_sensitivity

模型缺少必要字段时，会在页面展示不可计算模型和缺失字段。

## 5. 折扣与风险调整

支持的基础折扣因子：

- 流动性折扣
- 技术成熟度折扣
- 团队风险折扣
- 退出路径折扣
- 信息透明度折扣

如果用户填写折扣：

```text
调整后估值 = 原始估值 × ∏(1 - 单项折扣率)
```

如果折扣缺失，不强行假设，页面会提示当前为未折扣估值。

## 6. 综合估值区间生成规则

初版规则：

1. 剔除置信度为“仅供框架参考”的极端值。
2. 使用剩余模型低值作为 low。
3. 使用剩余模型 base 平均值作为 base。
4. 使用剩余模型高值作为 high。
5. 只有一个模型可计算时，标记为单模型参考区间。

页面措辞使用“初步估值区间”“研究参考”“需人工确认”“估值框架结果”。

## 7. JSON 保存路径

估值计算结果保存到：

```text
/Users/rachelao/Documents/Rachel Capital Web Platform/data/private_market_cases/
```

文件名：

```text
项目名称_YYYY-MM-DD_基础估值计算.json
```

该目录不得提交 Git，不得放入 public_site。

## 8. Obsidian 输出路径

基础估值计算报告输出到：

```text
/Users/rachelao/Documents/Rachel Capital/15_估值引擎/基础估值计算/
```

frontmatter 默认：

```text
type: private_market_basic_valuation_calculation
status: draft
public: false
```

## 9. 与 V0.7 多模型估值对比的关系

valuation_result 中预留：

```json
{
  "for_v0_7_multi_model_comparison": {
    "model_results": [],
    "valuation_range": {},
    "confidence_level": "",
    "weighting_candidates": []
  }
}
```

V0.7 将在此基础上做更正式的多模型对比、权重调整和综合估值区间。

## 10. 隐私与安全边界

- 仅用于 localhost。
- 不发布 GitHub Pages。
- 不修改 public_site。
- 上传文件、解析结果和估值结果不进入 public_site。
- Obsidian 输出默认 public: false。
- 不输出买入、卖出、推荐、目标价或收益承诺。

## 11. 当前限制

- DCF 为简化计算，不支持复杂年度现金流数组的完整建模。
- IRR 第一版以回收期校验为主。
- 收入倍数、利润倍数、折现率等需要用户在 V0.5 中确认。
- 不自动联网寻找可比公司或可比交易。
- 不形成最终投资结论。

## 12. 下一步计划

- V0.7 多模型对比与权重调整。
- 增加年度现金流序列解析。
- 增加真实 IRR 计算。
- 增加可比公司 / 可比融资交易样本库。
- 增加敏感性矩阵和情景估值图表。
