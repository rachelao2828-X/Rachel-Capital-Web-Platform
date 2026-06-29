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
- 已完成 七大战略生态季度跟踪表结构。
- AI基础设施生态和半导体生态已有具体公司池。
- 已补全华为生态、机器人生态、高端材料生态、船舶与国防生态、医疗科技生态的核心公司观察池。
- 公司池仅为 Rachel Capital OS 内部研究对象池，不构成交易依据、定价判断或回报承诺。
- 后续需要人工复核公司相关性、收入占比、研究优先级和数据来源。
- 已完成战略生态公司池与 `03_公司数据库` 的 localhost 联动。
- 公司数据库读取路径为 `/Users/rachelao/Documents/Rachel Capital/03_公司数据库/`。
- 支持读取 A股、港股、港股通、美股、一级市场项目、全球创新企业、非上市公司、产业项目。
- 匹配方式包括显式生态字段、关键词匹配和公司池反向匹配。
- 匹配结果仅用于研究对象归类，不构成交易依据、定价判断或回报承诺。
- 战略生态公司池与公司数据库联动不自动发布 GitHub Pages。
- 后续需要人工确认公司生态相关性、细分环节、研究优先级和数据来源。
- 后续建议建设：公司数据库联动、日报事件输入、公开版发布审查。
- 当前模块建设默认只面向 Obsidian + localhost + `develop`，不自动发布 GitHub Pages。

## Foundation Files / 01_基石文件

- `01_基石文件` 是 Rachel Capital OS 的世界观与方法论底座。
- 当前第一步治理已完成：`00_基石文件总览`、`基石文件与七大战略生态关系`、`基石文件阅读顺序`、`基石文件更新日志`。
- 基石文件分为世界观层、方法论层、治理与索引层。
- 世界观层包括：`全球产业权力地图`、`全球产业权力迁移图`、`全球AI革命全景图`、`中国产业权力迁移图`。
- 已对四个世界观层基石文件进行结构化深化。
- `全球产业权力地图` 用于判断当下全球产业权力掌握者。
- `全球产业权力迁移图` 用于判断产业权力动态迁移方向。
- `全球AI革命全景图` 用于判断 AI 革命对产业、资本、公司和人的生产方式的影响。
- `中国产业权力迁移图` 用于判断中国从旧产业权力向硬科技、先进制造、自主可控和全球供应链能力迁移的过程。
- 四个世界观层文件共同支撑七大战略生态、公司数据库、季度跟踪表、估值引擎和投资决策引擎。
- `Rachel估值方法论` 已建设为 `01_基石文件` 的方法论层文件。
- `Rachel估值方法论` 用于统一 Rachel Capital OS 的估值原则、估值对象分类、估值方法选择、情景分析和风险折价。
- `Rachel估值方法论` 支撑 `15_估值引擎`、Valuation Cockpit、公司数据库、一级市场项目尽调、投资备忘录和投委会流程。
- 估值方法论覆盖二级市场上市公司、一级市场项目、产业资产、平台型资产和周期型资产。
- 估值方法论覆盖七大战略生态：AI基础设施、半导体、华为、机器人、高端材料、船舶与国防、医疗科技。
- 所有估值输出均为内部研究草稿，不构成交易依据、定价判断或回报承诺。
- `Rachel风险控制原则` 已建设为 `01_基石文件` 的方法论层文件。
- `Rachel风险控制原则` 用于统一 Rachel Capital OS 的风险定义、风险分类、风险等级、风险补偿、安全边际、仓位约束、一级市场风险控制、二级市场风险控制和事后复盘原则。
- `Rachel风险控制原则` 支撑 `16_投资决策引擎`、`15_估值引擎`、Valuation Cockpit、公司数据库、一级市场项目尽调、二级市场组合管理和季度复盘。
- 风险控制原则覆盖七大战略生态：AI基础设施、半导体、华为、机器人、高端材料、船舶与国防、医疗科技。
- 所有风险控制输出均为内部研究草稿，不构成交易依据、定价判断或回报承诺。
- 基石文件用于支撑七大战略生态、公司数据库、估值引擎、投资决策引擎和工作流。
- 所有基石文件均为内部研究内容，frontmatter 应保持 `public: false`。
- 所有世界观层文件仅用于内部研究，不构成交易依据、定价判断或回报承诺。
- 后续待建设：Rachel产业研究方法论、Rachel组合构建原则、2026年度核心假设。
- 后续建议继续建设：2026年度核心假设、Rachel组合构建原则。
- 后续建议建设：2026年度核心假设、Rachel组合构建原则、不投资清单、高置信度机会判断标准。
- 后续可在 Web Platform 增加“基石文件”页面，用于展示世界观层、方法论层、治理与索引层。
- 后续 Web Platform 可增加“基石文件 / 估值方法论”页面；Valuation Cockpit 后续升级应遵循 `Rachel估值方法论`。
- 后续 Web Platform 可增加“基石文件 / 风险控制原则”页面；Valuation Cockpit 和投资决策引擎后续升级应遵循 `Rachel风险控制原则`。

## Key Persons / 04_关键人物

- `04_关键人物` 是 Rachel Capital OS 的人物研究库，用于研究影响产业方向、公司战略、技术路线、资本流向、政策组织和一级市场项目成败的关键人物。
- 当前第一步治理已完成：目录结构、`00_关键人物总览`、`人物研究模板`、`人物研究方法论`、`创始人判断框架`、`基金经理风格判断框架`、`人物风险识别框架`、`关键人物更新日志`。
- 关键人物目录分为产业领袖、投资大师与基金经理、科技公司创始人与CEO、科学家与技术路线推动者、一级市场关键人、政策与产业组织者、人物方法论和 Archive。
- 关键人物研究需要连接七大战略生态、公司数据库、估值引擎、投资决策引擎和基金经理模式。
- 所有关键人物相关 Obsidian 文件均为内部研究内容，frontmatter 应保持 `public: false`。
- 本阶段不批量创建具体人物卡片；后续建议先建设投资大师与基金经理、AI / 科技公司创始人、中国硬科技人物和一级市场项目创始人模板。

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
