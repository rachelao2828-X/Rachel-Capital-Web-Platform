# Public Ecosystem Section Numbering Fix

## 修复背景

Public Research Portal 的战略生态详情页此前直接渲染 Obsidian 源文件中的二级标题。由于“公开展示摘要”已作为卡片摘要使用，详情页不展示该章节，但“下一步研究任务”仍保留源文件中的“9. 下一步研究任务”，导致详情页出现章节编号跳号。

## 修改内容

1. 更新 `scripts/export_public_site.py`：
   - 导出战略生态 section 时去除原始 Markdown 二级标题行。
   - `summary` 继续来自“公开展示摘要”，用于首页和战略生态卡片。
   - 详情页使用的 `sections` 只保留正文内容。

2. 更新 `public_site/assets/site.js`：
   - 新增固定章节顺序 `ecosystemSectionOrder`。
   - 详情页统一由前端生成章节标题：
     - 1. 生态定义
     - 2. 产业链结构
     - 3. 核心价值链
     - 4. 关键公司观察池
     - 5. 长期跟踪指标
     - 6. 关键问题
     - 7. 与其他生态的关系
     - 8. 下一步研究任务
   - 不在详情页展示“公开展示摘要”章节。
   - 保留对旧数据的兼容处理，渲染前会去除 section 内残留的原始二级标题。

## 验收结果

- `python3 scripts/export_public_site.py` 运行成功。
- `public_site/data/ecosystems.json` 已重新生成，包含 7 个公开战略生态。
- `sections.next_tasks` 中不再包含 `## 9. 下一步研究任务`。
- 前端语法检查通过：`node --check public_site/assets/site.js`。
- 导出脚本语法检查通过：`python3 -m py_compile scripts/export_public_site.py`。

## 页面行为

- 首页和战略生态卡片继续使用 `summary` 展示公开摘要。
- 战略生态详情页不展示“公开展示摘要”章节。
- 所有生态详情页按固定顺序展示 1-8 节，编号连续。
- 使用 hash route，保持 GitHub Pages 静态部署兼容。
