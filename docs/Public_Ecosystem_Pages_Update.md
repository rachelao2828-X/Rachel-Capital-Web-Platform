# Public Ecosystem Pages Update

## 修改内容

本次更新升级了 Rachel Capital OS Public Research Portal 的“战略生态”展示逻辑。

数据源来自 Obsidian Vault：

```text
/Users/rachelao/Documents/Rachel Capital/02_战略生态
```

导出规则：

- 只导出 frontmatter 中 `public: true` 的 Markdown 文件。
- 生态文件需为 `type: ecosystem`。
- 生态结构化数据写入 `public_site/data/ecosystems.json`。
- 公开内容总索引仍写入 `public_site/data/public_content.json`，供日报、报告等页面使用。
- 生态 Markdown 文件复制到 `public_site/ecosystems/`。

## 导出字段

每个公开生态导出以下字段：

- `title`
- `id`
- `tags`
- `linked_companies`
- `company_count`
- `publish_scope`
- `summary`
- `source_path`
- `sections`
- `path`

`sections` 包括：

- `definition`: 生态定义
- `industry_chain`: 产业链结构
- `value_chain`: 核心价值链
- `companies`: 关键公司观察池
- `indicators`: 长期跟踪指标
- `questions`: 关键问题
- `relations`: 与其他生态的关系
- `next_tasks`: 下一步研究任务

数据结构示例：

```json
[
  {
    "id": "ECO-AI-INFRA-001",
    "title": "AI基础设施生态",
    "tags": ["战略生态", "AI基础设施", "算力"],
    "linked_companies": ["NVIDIA", "中际旭创"],
    "company_count": 12,
    "publish_scope": "public_summary",
    "summary": "AI基础设施生态是 AI 时代最重要的底层能力体系之一。",
    "source_path": "02_战略生态/AI基础设施生态.md",
    "sections": {
      "definition": "...",
      "industry_chain": "...",
      "value_chain": "...",
      "companies": "...",
      "indicators": "...",
      "questions": "...",
      "relations": "...",
      "next_tasks": "..."
    }
  }
]
```

## 页面结构

战略生态页面继续使用 GitHub Pages 兼容的 hash route：

```text
#ecosystems
```

生态详情页使用：

```text
#/ecosystems/生态名称
```

示例：

```text
#/ecosystems/AI基础设施生态
```

不使用服务端动态路由，因此 GitHub Pages 部署后不会出现详情页 404。

## 页面展示

“战略生态”页面展示七个生态卡片：

- AI基础设施生态
- 半导体生态
- 华为生态
- 机器人生态
- 高端材料生态
- 船舶与国防生态
- 医疗科技生态

每个卡片显示：

- 生态名称
- 公开展示摘要
- 核心标签
- 重点公司数量
- 查看详情按钮

首页“七大战略生态”模块也读取 `public_site/data/ecosystems.json`，不再使用硬编码占位内容。首页展示生态名称、一句话摘要和“查看生态”按钮。

点击详情后显示：

- 生态定义
- 产业链结构
- 核心价值链
- 关键公司观察池
- 长期跟踪指标
- 关键问题
- 与其他生态的关系
- 下一步研究任务

## 验收结果

已完成以下本地检查：

- `python3 -m py_compile scripts/export_public_site.py` 通过。
- `node --check public_site/assets/site.js` 通过。
- `python scripts/export_public_site.py` 在本机不可用，因为当前 shell 没有 `python` 命令。
- 使用等效命令 `python3 scripts/export_public_site.py` 导出成功。
- 从 Obsidian Vault 导出 `16` 个公开内容，其中 `7` 个为战略生态。
- 已生成 `public_site/data/ecosystems.json`。
- `public_site/data/ecosystems.json` 中包含 7 个生态。
- 7 个生态均包含 `id`、`title`、`tags`、`linked_companies`、`publish_scope`、`source_path`、`summary` 和详情 `sections`。
- `public_site/ecosystems/` 下已生成 7 个生态 Markdown 文件。
- 本地静态服务器验证首页返回 `HTTP 200`。
- 本地访问 `public_site/data/ecosystems.json` 可读取 7 个生态。
- 本地访问 `public_site/ecosystems/AI基础设施生态.md` 返回 `HTTP 200`。

## 后续建议

- 将 GitHub Pages 的“战略生态”卡片视觉进一步优化为更适合长摘要的研究页布局。
- 在导出流程中增加公开字段白名单测试，避免未来误导出内部字段。
- 将 Coze 日报中的生态标签与这些 Source of Truth 文件建立自动关联。

## 2026-06-26 发布验收记录

本次验收继续推进战略生态公开页面发布。

检查结果：

- 当前分支为 `develop`。
- `develop` 已包含章节编号修复提交：`76eda42 Fix ecosystem detail section numbering`。
- 关键文件均存在：
  - `public_site/data/ecosystems.json`
  - `docs/Public_Ecosystem_Section_Numbering_Fix.md`
  - `docs/Public_Ecosystem_Pages_Update.md`
- `python scripts/export_public_site.py` 在本机不可用，因为当前 shell 没有 `python` 命令。
- 使用 `python3 scripts/export_public_site.py` 重新导出成功。
- `public_site/data/ecosystems.json` 包含 7 个公开战略生态。
- 每个生态均包含 `id`、`title`、`tags`、`linked_companies`、`company_count`、`publish_scope`、`summary`、`source_path` 和 `sections`。
- 本地静态站使用 `http://127.0.0.1:8081` 验收，原因是 `8080` 已被占用。
- 首页中文导航显示正常。
- 首页“七大战略生态”显示 7 个生态卡片。
- “战略生态”页面显示 7 个生态卡片，并包含“查看详情”入口。
- 7 个生态详情页均可通过 hash route 打开，不出现 404。
- 详情页统一显示连续章节编号 `1` 到 `8`。
- 不再出现 `9. 下一步研究任务`。
- 详情页不展示 `公开展示摘要`，该内容仅作为首页和卡片摘要使用。

本地验收结论：通过。

## 2026-06-26 AI基础设施生态 1.0 更新记录

AI基础设施生态已从 Seed 0.1 升级为 1.0 样板生态，Obsidian Source of Truth 为：

```text
/Users/rachelao/Documents/Rachel Capital/02_战略生态/AI基础设施生态.md
```

本次公开站同步内容：

- 首页“七大战略生态”中的 AI基础设施生态摘要已更新。
- “战略生态”页面中的 AI基础设施生态卡片摘要已更新。
- AI基础设施生态详情页已展示 1.0 内容。
- 详情页新增展示“子链条拆解”和“Coze 日报自动关联规则”两个公开结构化章节。
- 详情页仍隐藏“公开展示摘要”，该内容仅用于首页和卡片摘要。

为适配 1.0 样板生态，公开站前端将生态详情页改为按实际存在的 section 动态连续编号：

- AI基础设施生态显示 10 个连续章节。
- 其他六个生态仍显示 8 个连续章节。
- 不再依赖 Obsidian 原始 Markdown 编号。

本地验收结果：

- `python3 scripts/export_public_site.py` 导出成功。
- `public_site/data/ecosystems.json` 包含 7 个战略生态。
- AI基础设施生态包含 `sub_chains` 和 `coze_rules` 两个新增公开 section。
- 子目录中的研究文件未被误导出到 public content。
- 本地静态站使用 `http://127.0.0.1:8081` 验收，原因是 `8080` 已被占用。
- 首页、战略生态页面、AI基础设施生态详情页均显示正常。
- AI基础设施生态详情页无 404，编号连续，不出现 `9. 下一步研究任务` 跳号。
