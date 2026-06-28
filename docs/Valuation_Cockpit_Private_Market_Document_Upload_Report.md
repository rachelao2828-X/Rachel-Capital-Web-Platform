# Valuation Cockpit Private Market Document Upload Report

## 1. 功能目的

本功能用于 Rachel Capital OS 本地 Valuation Cockpit 的“未上市 / 一级市场估值”板块。用户可以上传 PDF 版项目资料、商业计划书或可研报告，系统在本地读取文本，提取项目摘要、融资信息、经营数据、财务数据、技术壁垒、市场竞争、风险因素和估值可用性，并生成 Obsidian 草稿。

本功能仅用于内部研究、估值框架和尽调准备，不输出买入、卖出或推荐结论。

## 2. 支持的文件类型

第一版页面允许上传：

- PDF
- PPTX
- DOCX
- XLSX

当前可解析的文件类型为 PDF。PPTX、DOCX、XLSX 上传后会保存到本地私有目录，但解析器会提示当前版本暂不支持该格式，页面不得崩溃。

## 3. 本地保存路径

上传文件保存到：

```text
/Users/rachelao/Documents/Rachel Capital Web Platform/data/uploads/private_market/
```

解析中间结果保存到：

```text
/Users/rachelao/Documents/Rachel Capital Web Platform/data/extracted/private_market/
```

文件名会加时间戳，避免覆盖。上传文件和解析中间结果不得放入 `public_site`。

## 4. PDF 解析逻辑

PDF 解析模块位于：

```text
app/services/valuation_engine/document_parser.py
```

解析输出结构：

```text
{
  "file_name": "",
  "file_path": "",
  "pages": [{"page_number": 1, "text": ""}],
  "raw_text": "",
  "tables": [],
  "warnings": []
}
```

解析器优先使用 PyMuPDF 提取分页文本，并使用 pdfplumber 尝试提取表格。如果环境缺少对应依赖，会返回 warning，而不是让页面崩溃。

当 PDF 文本为空或很少时，页面提示：

```text
该 PDF 可能为扫描件，当前版本可能无法完整识别。后续可接入 OCR。
```

## 5. 结构化提取 Schema

结构化提取模块位于：

```text
app/services/valuation_engine/private_market_extractor.py
```

第一版使用规则和关键词提取，不强依赖外部 LLM 或真实 API key。输出包括：

- `project_summary`
- `founder_team_info`
- `financing_info`
- `operating_data`
- `financial_data`
- `cost_structure`
- `technology_and_barriers`
- `market_and_competition`
- `risk_factors`
- `exit_path`
- `valuation_readiness`
- `field_assessments`
- `raw_excerpt`

其中 `founder_team_info` 会单独展示创始团队、管理团队、团队背景和关键人风险，并影响团队风险、关键人风险和估值可用性。`valuation_readiness` 会生成推荐估值模型、可用数据、缺失数据、追问清单和估值可用性等级。

## 6. 数据可信度标记

页面展示字段级可信度表：

| 字段 | 提取结果 | 来源 | 可信度 | 是否需要用户确认 |
|---|---|---|---|---|

来源分为：

- PDF 明确披露
- 系统推断
- 用户需要确认
- 缺失

可信度分为：

- 高
- 中
- 低
- 缺失

## 7. Obsidian 输出路径

项目资料解析报告输出到：

```text
/Users/rachelao/Documents/Rachel Capital/15_估值引擎/一级市场项目资料解析/
```

未上市一级市场估值框架输出到：

```text
/Users/rachelao/Documents/Rachel Capital/15_估值引擎/估值历史/未上市一级市场/
```

两个文件 frontmatter 均默认：

```text
status: draft
public: false
```

## 8. 隐私与安全边界

- 本功能仅用于 localhost。
- 不发布 GitHub Pages。
- 不把上传文件或解析内容放入 `public_site`。
- 不自动调用外部 API 上传资料。
- 如果后续接入 LLM API，必须在页面明确提示资料可能发送给外部模型服务。
- 生成的 Obsidian 文件默认 `public: false`。
- 所有输出仅用于内部研究，不构成任何投资建议、投资邀约或买卖依据。

`.gitignore` 必须包含：

```text
data/uploads/
data/extracted/
data/private_market_cases/
```

## 9. 当前限制

- 第一版仅完整支持文本型 PDF。
- 扫描版 PDF 暂不做 OCR，只给出提示。
- PPTX、DOCX、XLSX 暂未做正文解析。
- 结构化提取为规则和关键词，不保证完整准确。
- 创始团队信息已独立展示，但第一版仍以关键词提取为主，后续需要升级为更完整的团队履历和关键人风险评分。
- 不直接生成最终投资结论或单点估值。

## 10. 下一步计划

- 增加 PPTX、DOCX 和 XLSX 正文解析。
- 增加 OCR 处理扫描版 PDF。
- 将创始团队信息升级为独立提取模块，并影响团队风险、关键人风险和估值可用性。
- 增加用户校正表单，把确认后的字段写入结构化 case 文件。
- 在用户明确同意后，预留 LLM 辅助提取接口。
- 增加更多手动测试样例和小型 PDF fixture。

## 手动测试说明

1. 上传普通文本型 PDF BP：应能提取文本、生成项目摘要、生成缺失数据清单。
2. 上传扫描版 PDF：应提示可能无法完整识别，不应报错。
3. 上传文件后生成 Obsidian 项目资料解析报告：路径应正确，frontmatter 应包含 `public: false`。
4. 生成未上市一级市场估值框架：路径应正确，frontmatter 应包含 `public: false`。
5. 确认上传文件没有进入 `public_site`。
6. 确认 `data/uploads/` 已在 `.gitignore`。
