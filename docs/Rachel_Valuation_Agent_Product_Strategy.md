# Rachel Valuation Agent Product Strategy

## 1. 产品定位

当前版本：

Rachel Valuation Cockpit 是本地估值驾驶舱，用于内部研究、项目资料解析、估值模型推荐、估值框架生成。

未来版本：

Rachel Valuation Agent 是 AI 估值与尽调助理，用于自动阅读资料、提取信息、识别标的类型、推荐估值模型、生成尽调问题、形成估值 Memo。

市场化定位：

AI Valuation & Due Diligence Copilot，面向投资人、FA、产业方、政府基金、战投部门和创业公司 CFO 的估值与尽调工作台。

明确禁止定位为：

- AI 投资顾问
- AI 荐股工具
- 自动买卖决策工具
- 收益预测工具
- 自动交易工具

## 2. Cockpit 与 Agent 的区别

| 维度 | Valuation Cockpit | Valuation Agent |
|---|---|---|
| 工作方式 | 用户主导点击 | Agent 主动规划任务 |
| 数据输入 | 用户上传/填写 | Agent 自动读取、提取、追问 |
| 模型选择 | 规则推荐 | 根据标的、数据质量、行业自动选择 |
| 数据补充 | 给出缺失清单 | 自动检索部分数据并生成追问 |
| 输出 | 估值框架 | 估值草案、反证、尽调问题、Memo |
| 记忆 | 写入 Obsidian | 持续学习项目库和估值案例 |
| 风险控制 | 用户确认 | 人在回路审批 |

## 3. Agent-ready 架构

未来 Agent 模块设计：

```text
valuation_agent/
├── document_reading_agent.py
├── target_classification_agent.py
├── model_selection_agent.py
├── data_gap_agent.py
├── comparable_company_agent.py
├── valuation_calculation_agent.py
├── memo_agent.py
├── risk_review_agent.py
└── human_review_gate.py
```

### Document Reading Agent

读取：

- PDF
- PPTX
- DOCX
- XLSX

输出：

- 13 类信息
- 数据可信度
- 缺失数据
- 原始摘录

### Target Classification Agent

识别：

- 已上市公司
- 未上市成长公司
- 一级市场融资标的
- 项目公司 / SPV
- 资产型项目

### Model Selection Agent

选择：

- PE
- PB
- PS
- EV/EBITDA
- DCF
- SOTP
- 可比公司法
- 可比交易法
- 收入倍数
- ARR 倍数
- IRR
- 项目现金流法
- 资产重估法

### Data Gap Agent

生成：

- 缺失数据清单
- 尽调问题
- 需要人工确认的数据
- 数据可信度评级

### Comparable Company Agent

未来负责：

- 匹配上市可比公司
- 匹配一级市场可比交易
- 匹配产业链上下游
- 映射 A股 / 港股 / 美股可比标的

当前阶段只预留设计，不强制实现。

### Valuation Calculation Agent

未来负责：

- 多模型估值
- 保守 / 中性 / 乐观情景
- 敏感性分析
- 折扣因子
- 估值区间

### Memo Agent

生成：

- 项目资料解析报告
- 估值框架
- 尽调问题清单
- 投资备忘录草稿
- 投委会 Memo 草稿

### Risk Review Agent

检查：

- 数据真实性风险
- 技术风险
- 市场风险
- 团队风险
- 融资风险
- 政策风险
- 估值过高风险

### Human Review Gate

所有关键输出必须经过用户确认。

禁止 Agent 自动生成：

- 买入
- 卖出
- 推荐
- 收益承诺
- 自动交易指令

## 4. 市场化路线

### Phase 1：内部版

目标：

- Rachel 自己使用
- 跑通 20-50 个真实项目
- 打磨估值模板
- 沉淀行业案例库

### Phase 2：顾问服务版

目标：

- 用内部工具为外部客户提供服务
- 输出项目解析报告、估值框架、尽调问题清单
- 按项目或月度顾问收费

### Phase 3：私有化部署版

目标客户：

- 产业基金
- 政府基金
- FA 机构
- 上市公司战投部
- 投资机构

特点：

- 本地部署
- 私有项目库
- 权限管理
- 数据不出客户环境

### Phase 4：SaaS 版

目标：

- 标准化在线产品
- 支持上传 BP
- 自动解析
- 自动生成估值框架和尽调问题
- 团队协作
- 项目库

SaaS 版合规、安全和数据隐私要求最高，应放在最后。

## 5. 合规边界

允许：

- 资料解析
- 估值模型推荐
- 估值框架
- 尽调问题
- 可比公司整理
- 投资备忘录草稿
- 风险提示
- 内部研究辅助

禁止：

- 个股荐股
- 买入/卖出建议
- 收益承诺
- 自动投资决策
- 自动交易
- 面向公众提供未经合规设计的证券投资建议

## 6. 第一款市场化 MVP

上传一级市场 BP / 商业计划书 / 项目资料，10 分钟生成：

1. 项目摘要
2. 创始团队信息
3. 商业模式
4. 技术壁垒
5. 产品与客户
6. 市场空间
7. 财务数据
8. 融资估值
9. 推荐估值模型
10. 可比公司方向
11. 缺失数据
12. 尽调问题
13. 风险提示
14. 估值可用性评级

MVP 定位：

一级市场 BP 解析 + 尽调初筛 + 估值框架生成器
