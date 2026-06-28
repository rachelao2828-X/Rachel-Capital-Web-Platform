# Valuation Cockpit Private Market Financial Model Report

## 1. 功能目的

本功能用于 Rachel Capital OS localhost Valuation Cockpit 的“未上市 / 一级市场估值”板块。用户可以上传 Excel / CSV 财务模型、预测表、项目测算表或审计资料摘要，系统在本地读取表格结构，识别财务表类型，提取关键财务字段，并生成 Obsidian 财务模型解析报告。

输出仅作为内部研究草稿，不构成任何投资建议、投资邀约、买卖依据、目标价或收益承诺。

## 2. 支持文件类型

第一版支持：

- XLSX
- CSV

旧版 XLS：

- 页面不崩溃。
- 提示用户建议转换为 XLSX。

## 3. 本地保存路径

上传文件保存到：

```text
/Users/rachelao/Documents/Rachel Capital Web Platform/data/uploads/private_market_financials/
```

解析中间结果保存到：

```text
/Users/rachelao/Documents/Rachel Capital Web Platform/data/extracted/private_market_financials/
```

上传文件和解析结果不得进入 `public_site`，也不得提交到 Git。

## 4. 财务表类型识别

解析器会基于 sheet 名称和表格关键词识别：

1. 收入预测表
2. 成本结构表
3. 利润表
4. 现金流表
5. 资产负债表
6. CAPEX / 投资计划表
7. 产能规划表
8. 融资测算表
9. IRR / 回收期测算表
10. 敏感性分析表

## 5. 关键财务字段提取

第一版尽量提取：

- 收入相关：历史收入、预测收入、收入增长率、产品收入拆分、客户收入拆分、单价、销量
- 毛利与利润：毛利、毛利率、净利润、净利率、EBITDA、EBITDA Margin、EBIT
- 成本费用：原材料成本、人工成本、能耗成本、折旧、销售费用、管理费用、研发费用、财务费用、OPEX
- 现金流：经营现金流、自由现金流、项目现金流、累计现金流
- 投资与产能：CAPEX、项目总投资、建设周期、设计产能、当前产能、产能利用率、产能爬坡
- 融资与回报：融资金额、投前估值、投后估值、出让股权比例、IRR、回收期、NPV
- 敏感性假设：保守情景、中性情景、乐观情景、单价敏感性、销量敏感性、毛利率敏感性、利用率敏感性、折现率敏感性

无法可靠提取的字段会标记为“缺失”或“需要用户确认”。

## 6. 数据可信度标记

页面展示字段级可信度表：

| 字段 | 提取结果 | 来源Sheet | 可信度 | 是否需要确认 |
|---|---|---|---|---|

来源包括：

- Excel明确披露
- 系统推断
- 缺失

可信度包括：

- 高
- 中
- 低
- 缺失

## 7. 与 BP / 项目资料解析结果的关系

Excel / 财务模型用于补充项目资料中缺失的财务、产能、成本、现金流、IRR 和敏感性数据。

本阶段先不做复杂自动合并，但会在页面和 Obsidian 输出中体现：

- 来自项目资料的文本信息
- 来自 Excel 的财务数据
- 两者存在冲突时提示用户核验

## 8. Obsidian 输出路径

财务模型解析报告输出到：

```text
/Users/rachelao/Documents/Rachel Capital/15_估值引擎/一级市场财务模型解析/
```

文件 frontmatter 默认：

```text
status: draft
public: false
```

未上市一级市场估值框架草稿会增加“Excel / 财务模型补充信息”章节。

## 9. 隐私与安全边界

- 本功能仅用于 localhost。
- 不发布 GitHub Pages。
- 不把上传文件或解析结果放入 `public_site`。
- 不自动调用外部 API 上传财务模型。
- 生成的 Obsidian 文件默认 `public: false`。
- 所有输出仅用于内部研究。

`.gitignore` 必须包含：

```text
data/uploads/
data/extracted/
data/private_market_cases/
data/uploads/private_market_financials/
data/extracted/private_market_financials/
```

## 10. 当前限制

- 第一版重点支持 XLSX 和 CSV。
- 旧版 XLS 暂提示转换为 XLSX。
- 解析逻辑为关键词和表格结构识别，不保证完全准确。
- 当前不执行 DCF / IRR 自动计算，只判断哪些模型可被当前数据支持。
- 不解析复杂 Excel 公式链、隐藏 sheet、宏或外部链接。

## 11. 下一步计划

- 财报 / 审计报告读取。
- 三张表标准化。
- DCF / IRR 自动计算。
- 敏感性分析自动建模。
- 项目资料文本与 Excel 财务模型的冲突检测。
- 用户校正字段后写入结构化 case 文件。
