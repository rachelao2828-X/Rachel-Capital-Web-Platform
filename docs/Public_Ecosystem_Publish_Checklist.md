# Public Ecosystem Publish Checklist

## 本次发布范围

- 发布 Rachel Capital Public Research Portal 的“战略生态”公开页面。
- 数据源为 Obsidian Vault：`/Users/rachelao/Documents/Rachel Capital/02_战略生态/`。
- 导出目标包括：
  - `public_site/data/ecosystems.json`
  - `public_site/data/public_content.json`
- 本次重点验收七大战略生态列表、生态详情页、章节编号、GitHub Pages 静态路由兼容性。

## 本地验收结果

- 当前分支：`develop`。
- 工作区初始状态：干净。
- `develop` 已包含修复提交：`76eda42 Fix ecosystem detail section numbering`。
- `python scripts/export_public_site.py` 在本机不可用，原因是当前 shell 没有 `python` 命令。
- 使用 `python3 scripts/export_public_site.py` 重新导出成功：
  - 公开内容：16 条。
  - 战略生态：7 条。
- 本地静态站使用端口：`8081`。
- 端口说明：`8080` 已被占用，因此按验收要求切换到 `8081`。
- 本地地址：`http://127.0.0.1:8081`。
- 本地页面验收：通过。

## 七大战略生态展示检查

首页“七大战略生态”区域已显示 7 个生态卡片：

- AI基础设施生态
- 半导体生态
- 华为生态
- 机器人生态
- 高端材料生态
- 船舶与国防生态
- 医疗科技生态

“战略生态”页面已显示 7 个生态卡片。每个卡片具备：

- 生态名称
- 公开展示摘要
- 标签
- 重点公司数量
- 查看详情按钮

## 详情页章节编号检查

已逐一验证 7 个生态详情页。详情页章节标题由前端统一生成，不依赖 Obsidian 原始 Markdown 编号。

固定章节顺序如下：

1. 生态定义
2. 产业链结构
3. 核心价值链
4. 关键公司观察池
5. 长期跟踪指标
6. 关键问题
7. 与其他生态的关系
8. 下一步研究任务

验收结果：

- AI基础设施生态详情页编号连续。
- 所有生态详情页均不再出现 `9. 下一步研究任务`。
- 详情页不展示 `公开展示摘要` 章节。
- `summary` 仍用于首页与生态卡片展示。

## Public 数据导出检查

`public_site/data/ecosystems.json` 已生成，包含 7 个生态。

每个生态均包含以下字段：

- `id`
- `title`
- `tags`
- `linked_companies`
- `company_count`
- `publish_scope`
- `summary`
- `source_path`
- `sections`

已确认 `publish_scope` 为 `public_summary`。导出逻辑只读取 frontmatter 中 `public: true` 的生态内容。

## GitHub Pages 兼容性检查

- 页面使用静态资源与前端 `fetch` 读取 JSON。
- 生态详情页使用 hash route：`#/ecosystems/生态名称`。
- 不依赖服务端动态路由。
- 本地验证详情页不出现 404。

## 未公开内容泄露风险

本次导出规则限定为 `public: true`。

本地数据扫描未发现以下敏感内容导出：

- 内部持仓
- 私人决策日志
- 完整估值模型
- API Key 或 Secret

页面中的风险边界说明和免责声明属于公开展示说明，不代表泄露内部内容。

## 后续待优化事项

- 将公开导出流程加入自动化测试，固定检查 `public: true` 与字段白名单。
- 为 GitHub Pages 部署增加发布后自动验收脚本。
- 优化生态详情页中长表格在手机端的阅读体验。
- 将 Coze 日报中的生态标签与七大战略生态 Source of Truth 做自动关联。
