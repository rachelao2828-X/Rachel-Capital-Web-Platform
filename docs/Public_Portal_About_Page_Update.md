# Public Portal About Page Update

## 修改内容

本次更新将 Rachel Capital OS Public Research Portal 原来的独立“免责声明”入口合并为“关于平台”页面。

导航栏最终为：

- 首页
- 科技动向日报
- 战略生态
- 公司观察
- 研究报告
- 关于平台

已移除单独的“免责声明”导航入口。免责声明内容保留在“关于平台”页面内。

## 页面结构

新增“关于平台”页面，静态 hash route：

```text
#about
```

页面包括：

- 平台简介
- 研究方向
- 联系方式
- 免责声明

联系方式：

- 邮箱：rachelaowei@qq.com
- WeChat：rachelao

为兼容旧链接，`#disclaimer` 会在前端路由中显示“关于平台”视图，不使用服务端动态路由。

## 首页页脚

首页底部页脚已更新为：

```text
Rachel Capital OS · 科技与产业研究观察
联系邮箱：rachelaowei@qq.com · WeChat：rachelao
内容仅供研究交流，不构成投资建议。
```

页脚仍保留公开数据更新时间。

## GitHub Pages 兼容性

本次更新继续使用单页静态站点和 hash route：

```text
#home
#daily
#ecosystems
#companies
#reports
#about
```

不依赖服务端动态路由，因此部署到 GitHub Pages 后不会因为“关于平台”页面产生 404。

## 本地验收结果

已完成以下本地验证：

- `node --check public_site/assets/site.js` 通过。
- 本地静态首页返回 `HTTP 200`。
- 本地日报 Markdown 静态路径返回 `HTTP 200`。
- 首页导航出现“关于平台”。
- 导航栏不再出现单独“免责声明”入口。
- “关于平台”页面包含平台简介、研究方向、联系方式、免责声明。
- 首页底部显示联系邮箱、WeChat 和免责声明摘要。

## 注意事项

当前 GitHub Pages workflow 监听 `main` 分支部署。本次按要求推送到 `develop` 后，如需线上页面立即更新，需要将 `develop` 合并到 `main` 或调整 Pages workflow 的部署分支。
