# Rachel Capital OS / Rachel Capital Web Platform

## 项目架构原则

- Obsidian = 研究内容源头 Source of Truth
- GitHub = 版本管理与同步
- GitHub Pages = 公开研究展示层
- Web App = 私人投资操作系统

## 核心路径

Obsidian Vault：

```text
/Users/rachelao/Documents/Rachel Capital
```

Web Platform 项目：

```text
/Users/rachelao/Documents/Rachel Capital Web Platform
```

本地 Web App：

```text
Streamlit / localhost
```

公开展示：

```text
GitHub Pages，但当前阶段不要发布新功能。
```

## GitHub Pages 发布状态说明

- AI基础设施生态已经存在 GitHub Pages 公开版本，线上版本不是名称占位，已经包含公开摘要和详情内容。
- 半导体生态已经存在 GitHub Pages 公开版本，线上版本不是名称占位，已经包含公开摘要和详情内容，后续仍可能继续增强。
- 当前线上 GitHub Pages 与本地 `develop` 分支可能存在版本差异。
- 当前状态定义：
  - 线上 Pages：已发布旧版本 / 轻量公开版本。
  - 本地 `develop`：增强版本 / 待统一审查后再发布。
- 例如：AI基础设施生态在本地 `develop` 的 `public_site/data/ecosystems.json` 中 `company_count` 为 26，线上 Pages 当前展示为 12。
- 当前战略生态建设原则：先在 Obsidian + localhost + `develop` 中本地完善，后续统一进行公开版发布审查。
- 后续建设华为生态、机器人生态、高端材料生态、船舶与国防生态、医疗科技生态时，默认只建设 Obsidian + localhost + `develop`。
- `public_site` 不自动同步内部研究内容。
- GitHub Pages 发布需要用户单独明确指令。
- 等七大战略生态完成后，再统一进行公开版发布审查。

## Strategic Ecosystems Module

- 已完成 AI基础设施生态。
- 已完成 半导体生态。
- 已完成 华为生态。
- 已完成 机器人生态。
- 已完成 高端材料生态。
- 已完成 船舶与国防生态。
- 已完成 医疗科技生态。
- 七大战略生态内部框架已完成。
- 已完成 七大战略生态交叉关系图谱。
- 已完成 七大战略生态公司池结构。
- 后续建议建设：季度跟踪表、公司数据库联动、公开版发布审查。
- 当前模块建设默认只面向 Obsidian + localhost + `develop`，不自动发布 GitHub Pages。

## 当前重要边界

- 不要合并 main
- 不要发布 GitHub Pages
- 不要把内部估值功能放入 public_site
- 不要把上传的商业计划书、PDF、PPT、Word 文件放入 public_site
- 不要提交 data/uploads/
- 不要提交 data/extracted/
- 不要输出买入、卖出、推荐
- 所有估值输出仅用于内部研究
- 所有一级市场资料解析结果默认 public: false
- 所有估值备忘录默认 public: false

## Valuation Cockpit 当前产品方向

Valuation Cockpit 是 Rachel Capital OS 的本地估值驾驶舱，不是公开网站功能。

它需要拆分为两个独立板块：

1. 已上市公司估值
2. 未上市 / 一级市场估值

## 已上市公司估值板块

适用：

- A股
- 港股
- 美股
- 港股通
- ETF / REITs，如后续需要

核心功能：

- 输入股票名称、代码、市场、行业、生态
- 识别公司特征
- 推荐估值模型
- 展示多模型适用性对比
- 生成 Obsidian 估值备忘录草稿

输出路径：

```text
/Users/rachelao/Documents/Rachel Capital/15_估值引擎/估值历史/已上市公司/
```

## 未上市 / 一级市场估值板块

适用：

- 未上市成长公司
- 一级市场融资标的
- 项目公司 / SPV
- 资产型项目

核心功能：

- 手动输入项目信息
- 上传项目资料 / 商业计划书
- 解析 PDF / PPTX / DOCX
- 提取 13 类信息
- 推荐估值模型
- 生成项目资料解析报告
- 生成估值框架草稿

输出路径一：

```text
/Users/rachelao/Documents/Rachel Capital/15_估值引擎/一级市场项目资料解析/
```

输出路径二：

```text
/Users/rachelao/Documents/Rachel Capital/15_估值引擎/估值历史/未上市一级市场/
```

## 一级市场项目资料自动提取 13 类信息

必须提取：

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

创始团队信息必须单独展示，并影响团队风险、关键人风险和估值可用性。

## 文件上传要求

第一版必须支持：

- PDF
- PPTX
- DOCX

旧版 PPT / DOC 如无法完整解析，必须提示用户转换为 PPTX / DOCX，不得页面崩溃。

扫描版 PDF 如无法识别，必须提示可能是扫描件，后续可接 OCR，不得页面崩溃。

## 本地私有保存路径

上传文件保存到：

```text
/Users/rachelao/Documents/Rachel Capital Web Platform/data/uploads/private_market/
```

解析中间结果保存到：

```text
/Users/rachelao/Documents/Rachel Capital Web Platform/data/extracted/private_market/
```

必须确保 .gitignore 包含：

```text
data/uploads/
data/extracted/
data/private_market_cases/
```

## 推荐代码结构

如可行，使用：

```text
valuation_engine/
├── init.py
├── listed.py
├── private_market.py
├── document_parser.py
├── private_market_extractor.py
├── memo_writer.py
└── model_registry.py
```

其中：

- listed.py 负责已上市公司估值逻辑
- private_market.py 负责未上市 / 一级市场分类和模型推荐
- document_parser.py 负责 PDF / PPTX / DOCX 解析
- private_market_extractor.py 负责 13 类信息结构化提取
- memo_writer.py 负责写入 Obsidian Markdown
- model_registry.py 负责估值模型定义

## 当前工作方式

每次执行新任务前，请先阅读本文件：

```text
docs/CODEX_CONTEXT.md
```

然后再执行用户当前指令。

不要依赖聊天历史记忆。

## Rachel Valuation Agent 未来方向

- 当前 Valuation Cockpit 是 Rachel Capital OS 的内部估值工具，覆盖一级市场和二级市场研究场景。
- 未来未上市 / 一级市场部分可升级为 Rachel Valuation Agent。
- Rachel Valuation Agent 的市场化定位是 AI 估值与尽调助理 / AI Valuation & Due Diligence Copilot。
- 不定位为 AI 投资顾问、AI 荐股工具、自动买卖决策工具、收益预测工具或自动交易工具。
- 第一款市场化 MVP 是一级市场 BP 解析 + 尽调初筛 + 估值框架生成器。
- 所有关键输出必须保留 human review gate，由用户确认后才能进入下一步。
- 不输出买入、卖出、推荐、收益承诺或自动交易指令。
