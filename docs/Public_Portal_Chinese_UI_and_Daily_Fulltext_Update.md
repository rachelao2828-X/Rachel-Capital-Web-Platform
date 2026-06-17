# Public Portal Chinese UI and Daily Fulltext Update

## 修改目标

本次更新优化 Rachel Capital OS Public Research Portal 的中文展示与科技动向日报全文阅读体验。

## 完成内容

### 1. 全站中文化

保留以下英文品牌/标题：

- Rachel Capital OS
- Public Research Portal

其余主要用户可见导航与页面标题已中文化：

- Home -> 首页
- Daily Intelligence -> 科技动向日报
- Ecosystems -> 战略生态
- Companies -> 公司观察
- Reports -> 研究报告
- Disclaimer -> 免责声明

按钮与状态文案已改为中文，包括：

- 查看全部
- 查看全部生态
- 阅读全文
- 返回科技动向日报列表
- 正在加载公开数据
- 公开数据更新时间

### 2. 首页日报摘要可点击

首页“今日科技动向日报”卡片已改为整卡可点击。

展示内容：

- 日报标题
- 日期
- 一句话摘要
- 阅读全文入口

点击卡片、标题、摘要或“阅读全文”后，会进入对应日报全文视图。

### 3. 静态详情路由

日报详情使用 hash route，兼容 GitHub Pages 静态站点：

```text
#/daily/YYYY-MM-DD
```

示例：

```text
#/daily/2026-06-17
```

不依赖服务端动态路由，因此部署到 GitHub Pages 后不会因为详情路径产生 404。

### 4. Markdown 全文渲染

详情视图通过 `public_site/data/public_content.json` 中的 `path` 字段读取 Markdown：

```text
fetch(item.path)
```

示例路径：

```text
daily/2026/2026-06/2026-06-17_科技动向日报.md
```

渲染能力：

- 隐藏 frontmatter
- 一级标题
- 二级标题
- 三级标题
- 列表
- 加粗
- 段落

### 5. 日报全文页面体验

日报详情页顶部显示：

- 科技动向日报
- 日期：YYYY-MM-DD
- 来源：Coze
- 返回科技动向日报列表

正文显示完整 Markdown 内容。

## 使用方式

打开 Public Research Portal 首页：

```text
public_site/index.html
```

或 GitHub Pages：

```text
https://rachelao2828-x.github.io/Rachel-Capital-Web-Platform/
```

首页点击“今日科技动向日报”卡片即可进入全文。

日报列表页路径：

```text
#daily
```

日报详情页路径：

```text
#/daily/YYYY-MM-DD
```

## 本地验收结果

已完成以下检查：

- `node --check public_site/assets/site.js` 通过。
- 本地静态服务器访问首页返回 `HTTP 200`。
- 本地访问日报 Markdown 路径返回 `HTTP 200`。
- 首页导航显示中文：
  - 首页
  - 科技动向日报
  - 战略生态
  - 公司观察
  - 研究报告
  - 免责声明
- 页面中保留 Rachel Capital OS 与 Public Research Portal。
- 日报链接使用 `#/daily/YYYY-MM-DD`，兼容 GitHub Pages。
- 日报全文读取使用 `fetch(item.path)`。

## 注意事项

如果 GitHub Pages 页面没有立即更新，请等待 GitHub Actions 完成部署并刷新浏览器缓存。

如果某篇日报无法打开全文，请检查 `public_site/data/public_content.json` 中该条记录的 `path` 是否存在，并确认对应 Markdown 文件已提交到仓库。
