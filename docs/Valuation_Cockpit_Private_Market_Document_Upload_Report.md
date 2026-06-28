# Valuation Cockpit Private Market Document Upload Report

## 1. 功能目的

本功能用于 Rachel Capital OS 本地 Valuation Cockpit 的“未上市 / 一级市场估值”板块。用户可以上传项目资料、商业计划书、路演材料或可研报告，系统在本地解析文件内容，提取 13 类一级市场估值信息，并生成 Obsidian 项目资料解析报告和估值框架草稿。

本功能仅用于内部研究、估值框架和尽调准备，不直接生成最终估值结论，不输出买入、卖出或推荐。

## 2. 支持的文件类型

第一版支持：

- PDF
- PPTX
- DOCX

旧版格式处理：

- PPT：页面不崩溃，并提示“当前建议使用 PPTX 格式，旧版 PPT 可能无法完整解析。”
- DOC：页面不崩溃，并提示“当前建议使用 DOCX 格式，旧版 DOC 可能无法完整解析。”

当前不再只支持 PDF。PDF、PPTX、DOCX 均通过统一入口 `parse_uploaded_document(file_path)` 自动按扩展名分发。

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

## 4. 文件解析逻辑

解析模块位于：

```text
app/services/valuation_engine/document_parser.py
```

统一输出结构：

```text
{
  "file_name": "",
  "file_path": "",
  "file_type": "",
  "parser": "",
  "raw_text": "",
  "pages": [],
  "slides": [],
  "paragraphs": [],
  "tables": [],
  "warnings": [],
  "extraction_quality": ""
}
```

PDF 使用 PyMuPDF 提取分页文本，并使用 pdfplumber 尝试提取表格。扫描版或图片型 PDF 不报错，会提示当前版本可能无法完整识别，后续预留 OCR。

PPTX 使用 python-pptx 提取每页幻灯片标题、正文、表格文字、备注文字和 slide_number。

DOCX 使用 python-docx 提取段落、标题样式文本和表格文字。

## 5. 自动提取 13 类信息

结构化提取模块位于：

```text
app/services/valuation_engine/private_market_extractor.py
```

第一版使用规则和关键词提取，不强依赖外部 LLM 或真实 API key。自动提取信息升级为 13 类：

1. 项目基本信息
2. 创始团队信息
3. 商业模式
4. 技术路线
5. 产品与客户
6. 市场空间
7. 财务数据
8. 融资信息
9. 产能数据
10. 成本结构
11. 退出路径
12. 风险因素
13. 估值可用性

输出包括：

- `project_summary`
- `founder_team`
- `commercial_model`
- `technology_and_barriers`
- `product_and_customers`
- `market_and_competition`
- `financial_data`
- `financing_info`
- `operating_data`
- `capacity_and_cost`
- `exit_path`
- `risk_factors`
- `valuation_readiness`
- `field_assessments`
- `raw_excerpt`

## 6. 创始团队信息

新增 `founder_team` 字段，单独展示并写入 Obsidian 报告。提取内容包括创始人、联合创始人、核心高管、技术负责人、商业负责人、财务负责人、董事会/顾问、团队履历、产业经验、融资经验、团队完整度、团队短板和关键人依赖。

创始团队信息会影响：

- 团队风险
- 关键人风险
- 数据可信度
- 估值置信度
- 是否适合进入初步估值
- 需要向项目方追问的问题

## 7. 数据可信度标记

页面展示字段级可信度表：

| 字段 | 提取结果 | 来源 | 可信度 | 是否需要用户确认 |
|---|---|---|---|---|

来源分为：

- 资料明确披露
- 系统推断
- 用户需要确认
- 缺失

可信度分为：

- 高
- 中
- 低
- 缺失

## 8. Obsidian 输出路径

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

项目资料解析报告包含“创始团队信息”独立章节。估值框架草稿会引用团队风险和关键人风险。

## 9. 隐私与安全边界

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

## 10. 当前限制

- 扫描版 PDF 暂不做 OCR，只给出提示。
- 旧版 PPT / DOC 暂不做完整解析，建议转换为 PPTX / DOCX。
- 结构化提取为规则和关键词，不保证完整准确。
- 创始团队识别依赖资料披露质量，仍需人工核验履历和关键人依赖。
- 当前不直接生成最终估值结论，只生成资料解析、估值框架和缺失数据清单。

## 11. 下一步计划

- 增加 OCR 处理扫描版 PDF。
- 增加用户校正表单，把确认后的字段写入结构化 case 文件。
- 在用户明确同意后，预留 LLM 辅助提取接口。
- 增强团队履历、资本市场经验和产业资源识别。
- 增加更多真实样本的解析回归测试。

## 手动测试说明

1. 上传 PDF 商业计划书：应能读取文本，生成 13 类信息，创始团队信息单独展示。
2. 上传 PPTX 路演材料：应能读取幻灯片标题和正文，能提取团队页、融资页、财务页核心内容。
3. 上传 DOCX 项目资料：应能读取段落和表格，能提取项目摘要和财务/融资信息。
4. 上传旧版 PPT：不崩溃，提示建议转换为 PPTX。
5. 上传旧版 DOC：不崩溃，提示建议转换为 DOCX。
6. 上传扫描版 PDF：不崩溃，提示当前版本可能无法完整识别。
7. 生成 Obsidian 项目资料解析报告：包含“创始团队信息”，frontmatter 包含 `public: false`，路径正确。
8. 生成未上市一级市场估值框架：能引用创始团队风险，frontmatter 包含 `public: false`，路径正确。
9. 确认上传文件没有进入 `public_site`。
10. 确认 `data/uploads/`、`data/extracted/`、`data/private_market_cases/` 已在 `.gitignore`。
