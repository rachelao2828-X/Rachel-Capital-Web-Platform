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
