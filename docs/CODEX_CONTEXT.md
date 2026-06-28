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
