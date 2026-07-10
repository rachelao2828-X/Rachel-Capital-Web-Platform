const ECOSYSTEMS = [
  "AI基础设施生态",
  "半导体生态",
  "华为生态",
  "机器人生态",
  "高端材料生态",
  "船舶与国防生态",
  "医疗科技生态",
];

const ecosystemSectionOrder = [
  ["definition", "生态定义"],
  ["industry_chain", "产业链结构"],
  ["value_chain", "核心价值链"],
  ["sub_chains", "子链条拆解"],
  ["companies", "关键公司研究池"],
  ["indicators", "长期跟踪指标"],
  ["questions", "关键问题"],
  ["relations", "与其他生态的关系"],
  ["coze_rules", "Coze 日报自动关联规则"],
];

const themeSectionOrder = [
  ["overview", "专题概述"],
  ["why_track", "为什么值得长期关注"],
  ["specific_technologies", "具体关键攻关技术列表"],
  ["focus_areas", "重点观察方向"],
  ["stage_observations", "当前阶段观察"],
  ["ecosystem_relations", "与七大战略生态的关系"],
  ["public_boundary", "公开边界"],
];

const state = {
  content: [],
  ecosystems: [],
  themes: [],
  cooperation: [],
  marketRadarUnlocked: false,
  grouped: {
    daily: [],
    marketRadar: [],
    companies: [],
    ecosystems: [],
    reports: [],
  },
};

const MARKET_RADAR_PASSWORD = "128128";
const MARKET_RADAR_TYPES = new Set(["market_radar", "market_review", "review_report"]);

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function asArray(value) {
  if (!value) return [];
  return Array.isArray(value) ? value : [value];
}

function formatMetaValue(value) {
  return asArray(value).filter(Boolean).join("、");
}

function displaySource(value) {
  if (!value) return "未标明";
  if (String(value).toLowerCase() === "coze") return "Coze";
  return value;
}

function displayType(value) {
  const labels = {
    daily_intelligence: "科技动向日报",
    market_radar: "市场雷达",
    market_review: "市场复盘",
    review_report: "复盘报告",
    company: "合作机会",
    cooperation_opportunity: "合作机会",
    ecosystem: "战略生态",
    report: "研究报告",
    knowledge_graph: "知识图谱",
  };
  return labels[value] || value || "";
}

function dailyUrl(item) {
  return item?.date ? `#/daily-intelligence/${encodeURIComponent(item.date)}` : "#daily-intelligence";
}

function marketRadarSlug(item) {
  return item?.slug || item?.date || item?.title || "";
}

function marketRadarUrl(item) {
  const slug = marketRadarSlug(item);
  return slug ? `#/market-radar/${encodeURIComponent(slug)}` : "#market-radar";
}

function ecosystemUrl(item) {
  return item?.title ? `#/strategic-ecosystems/${encodeURIComponent(item.title)}` : "#strategic-ecosystems";
}

function themeUrl(item) {
  return item?.title ? `#/research-reports/${encodeURIComponent(item.title)}` : "#research-reports";
}

function reportUrl(item) {
  return item?.title ? `#/research-reports/${encodeURIComponent(item.title)}` : "#research-reports";
}

function cooperationUrl(item) {
  return item?.slug
    ? `#/cooperation-opportunities/${encodeURIComponent(item.slug)}`
    : "#cooperation-opportunities";
}

function updateDocumentMeta(route, item) {
  const metaDescription = document.querySelector('meta[name="description"]');
  const titles = {
    home: "Rachel Capital | 科技动向与产业研究",
    daily: "科技动向日报 | Rachel Capital",
    "market-radar": item?.title
      ? `${item.title} | 市场雷达 | Rachel Capital`
      : "市场雷达 | Rachel Capital",
    ecosystems: "战略生态 | Rachel Capital",
    "cooperation-opportunities": item?.title
      ? `${item.title} | 合作机会 | Rachel Capital`
      : "合作机会 | Rachel Capital",
    reports: "研究报告 | Rachel Capital",
    about: "关于平台 | Rachel Capital",
  };
  const descriptions = {
    home: "Rachel Capital 公开展示科技动向日报、市场雷达、战略生态、合作机会与研究报告。",
    daily: "Rachel Capital 公开展示经过筛选后的科技动向日报内容。",
    "market-radar": "Rachel Capital 市场雷达用于展示 Coze 自动发布的市场复盘报告，需输入访问密码后阅读。",
    ecosystems: "Rachel Capital 公开展示七大战略生态的产业研究摘要与长期观察。",
    "cooperation-opportunities": "Rachel 基于长期产业研究展示可公开的产业合作方向，包括一级市场项目方向、上市公司产业需求、算力与AI基础设施合作、政府园区产业机会和技术供应链协同。",
    reports: "Rachel Capital 公开展示经过筛选的研究报告、长期专题与知识图谱。",
    about: "Rachel Capital OS Public Research Portal 的公开边界与联系方式。",
  };
  document.title = titles[route] || titles.home;
  if (metaDescription) {
    metaDescription.setAttribute("content", descriptions[route] || descriptions.home);
  }
}

function formatTags(values) {
  const tags = asArray(values);
  if (!tags.length) return "";
  return `<div class="meta">${tags.map((tag) => `<span class="tag">${escapeHtml(tag)}</span>`).join("")}</div>`;
}

function itemCard(item, options = {}) {
  const title = escapeHtml(item.title || "未命名内容");
  const date = escapeHtml(item.date || "");
  const ecosystem = escapeHtml(formatMetaValue(item.ecosystem));
  const summary = escapeHtml(item.summary || item.excerpt || "");
  const tags = formatTags(item.tags);
  const detail = options.detail && item.body
    ? `<details><summary>查看详情</summary><p>${escapeHtml(item.body).replaceAll("\n", "<br />")}</p></details>`
    : "";

  return `
    <article class="card">
      <h3>${title}</h3>
      <div class="meta">
        ${date ? `<span>${date}</span>` : ""}
        ${ecosystem ? `<span>${ecosystem}</span>` : ""}
        ${item.type ? `<span>${escapeHtml(displayType(item.type))}</span>` : ""}
      </div>
      ${summary ? `<p>${summary}</p>` : ""}
      ${tags}
      ${detail}
    </article>
  `;
}

function dailyCard(item) {
  const title = escapeHtml(item.title || "未命名日报");
  const date = escapeHtml(item.date || "");
  const summary = escapeHtml(item.summary || item.excerpt || "");
  const tags = formatTags(item.tags);
  const url = dailyUrl(item);
  const ecosystem = escapeHtml(formatMetaValue(item.ecosystem));

  return `
    <article class="card">
      <h3><a href="${url}">${title}</a></h3>
      <div class="meta">
        ${date ? `<span>${date}</span>` : ""}
        ${ecosystem ? `<span>${ecosystem}</span>` : ""}
      </div>
      ${summary ? `<p><a href="${url}">${summary}</a></p>` : ""}
      ${tags}
      <a class="text-button" href="${url}">
        阅读全文
      </a>
    </article>
  `;
}

function marketRadarCard(item) {
  const title = escapeHtml(item.title || "未命名复盘报告");
  const date = escapeHtml(item.date || "");
  const summary = escapeHtml(item.summary || item.excerpt || "");
  const tags = formatTags(item.tags);
  const url = marketRadarUrl(item);
  const markets = escapeHtml(formatMetaValue(item.market || item.markets));
  const reportKind = escapeHtml(item.review_type || item.report_kind || "市场复盘");

  return `
    <article class="card">
      <h3><a href="${url}">${title}</a></h3>
      <div class="meta">
        ${date ? `<span>${date}</span>` : ""}
        ${markets ? `<span>${markets}</span>` : ""}
        ${reportKind ? `<span>${reportKind}</span>` : ""}
      </div>
      ${summary ? `<p><a href="${url}">${summary}</a></p>` : ""}
      ${tags}
      <a class="text-button" href="${url}">
        阅读复盘
      </a>
    </article>
  `;
}

function homeDailyCard(item) {
  const title = escapeHtml(item.title || "未命名日报");
  const date = escapeHtml(item.date || "");
  const summary = escapeHtml(item.summary || item.excerpt || "");
  const url = dailyUrl(item);

  return `
    <a class="card card-link" href="${url}">
      <article>
        <h3>${title}</h3>
        ${date ? `<div class="meta"><span>${date}</span></div>` : ""}
        ${summary ? `<p>${summary}</p>` : ""}
        <span class="text-button">阅读全文</span>
      </article>
    </a>
  `;
}

function emptyState(label) {
  return `<div class="card"><p>${label}</p></div>`;
}

function ecosystemCard(item, fallbackName) {
  const title = escapeHtml(item?.title || fallbackName);
  const summary = escapeHtml(item?.summary || item?.public_summary || item?.excerpt || "待发布公开生态观察。");
  const tags = formatTags(item?.tags || []);
  const companyCount = Number(item?.company_count ?? asArray(item?.linked_companies).length ?? 0);

  return `
    <article class="card ecosystem-card">
      <h3>${title}</h3>
      <p>${summary}</p>
      ${tags}
      <div class="meta">
        <span>重点公司数量：${companyCount}</span>
      </div>
      ${
        item
          ? `<a class="text-button" href="${ecosystemUrl(item)}">查看详情</a>`
          : `<span class="text-button secondary muted-button">待发布详情</span>`
      }
    </article>
  `;
}

function themeCard(item) {
  const title = escapeHtml(item?.title || "未命名专题");
  const summary = escapeHtml(item?.summary || item?.excerpt || "待发布公开专题摘要。");
  const tags = formatTags(item?.tags || ["关键核心技术", "自主可控", "国产替代", "十五五"]);
  const ecosystemCount = asArray(item?.linked_ecosystems).length;
  const url = themeUrl(item);

  return `
    <article class="card theme-card">
      <h3><a href="${url}">${title}</a></h3>
      <p><a href="${url}">${summary}</a></p>
      ${tags}
      <div class="meta">
        ${ecosystemCount ? `<span>关联生态数量：${ecosystemCount}</span>` : ""}
      </div>
      <a class="text-button" href="${url}">阅读报告</a>
    </article>
  `;
}

function reportCard(item) {
  const title = escapeHtml(item?.title || "未命名报告");
  const summary = escapeHtml(item?.summary || item?.excerpt || "待发布公开报告摘要。");
  const tags = formatTags(item?.tags || []);
  const url = reportUrl(item);

  return `
    <article class="card theme-card">
      <h3><a href="${url}">${title}</a></h3>
      <p><a href="${url}">${summary}</a></p>
      ${tags}
      <div class="meta">
        ${item?.date ? `<span>${escapeHtml(item.date)}</span>` : ""}
        ${item?.updated ? `<span>更新：${escapeHtml(item.updated)}</span>` : ""}
      </div>
      <a class="text-button" href="${url}">阅读报告</a>
    </article>
  `;
}

function homeEcosystemCard(item) {
  const title = escapeHtml(item?.title || "未命名生态");
  const summary = escapeHtml(item?.summary || item?.public_summary || item?.excerpt || "待发布公开生态观察。");
  return `
    <article class="mini-card">
      <h4>${title}</h4>
      <p>${summary}</p>
      <a href="${ecosystemUrl(item)}">查看生态</a>
    </article>
  `;
}

function homeCooperationCard(item) {
  const title = escapeHtml(item?.title || "未命名合作机会");
  const summary = escapeHtml(item?.summary || "");
  const url = cooperationUrl(item);
  return `
    <a class="card card-link" href="${url}">
      <article>
        <h3>${title}</h3>
        <div class="meta">
          ${item?.opportunity_type ? `<span>${escapeHtml(item.opportunity_type)}</span>` : ""}
        </div>
        ${summary ? `<p>${summary}</p>` : ""}
        <span class="text-button">查看合作机会</span>
      </article>
    </a>
  `;
}

function cooperationTable(items) {
  if (!items.length) return emptyState("暂无公开合作机会文章。");
  const rows = items.map((item) => {
    const url = cooperationUrl(item);
    return `
      <tr>
        <td><a href="${url}">${escapeHtml(item.title || "未命名合作机会")}</a></td>
        <td>${escapeHtml(item.opportunity_type || "")}</td>
        <td>${escapeHtml(item.date || "")}</td>
      </tr>
    `;
  });
  return `
    <div class="table-wrap">
      <table class="opportunity-table">
        <thead>
          <tr>
            <th>标题</th>
            <th>机会类型</th>
            <th>发布时间</th>
          </tr>
        </thead>
        <tbody>${rows.join("")}</tbody>
      </table>
    </div>
  `;
}

function groupContent(items) {
  state.grouped.daily = items.filter((item) => item.type === "daily_intelligence");
  state.grouped.marketRadar = items.filter((item) => MARKET_RADAR_TYPES.has(item.type));
  state.grouped.companies = items.filter((item) => item.type === "company");
  state.grouped.ecosystems = items.filter((item) => item.type === "ecosystem");
  state.grouped.reports = items.filter((item) => item.type === "report" || item.type === "knowledge_graph");
}

function renderHome() {
  const latestDaily = state.grouped.daily.slice(0, 1);
  const latestReports = [...state.themes, ...state.grouped.reports].slice(0, 3);
  const latestCooperation = state.cooperation.slice(0, 3);

  document.querySelector("#home-daily").innerHTML = latestDaily.length
    ? latestDaily.map((item) => homeDailyCard(item)).join("")
    : emptyState("暂无公开日报。请在 Obsidian 中将可公开日报标记为 public: true 后导出。");

  document.querySelector("#home-ecosystems").innerHTML = ECOSYSTEMS
    .map((name) => state.ecosystems.find((item) => item.title === name))
    .filter(Boolean)
    .map((item) => homeEcosystemCard(item))
    .join("") || emptyState("暂无公开战略生态。");

  document.querySelector("#home-reports").innerHTML = latestReports.length
    ? latestReports.map((item) => (item.sections ? themeCard(item) : reportCard(item))).join("")
    : emptyState("暂无公开研究报告。");

  document.querySelector("#home-cooperation").innerHTML = latestCooperation.length
    ? latestCooperation.map((item) => homeCooperationCard(item)).join("")
    : emptyState("暂无公开合作机会文章。");
}

function renderDaily() {
  document.querySelector("#daily-list").innerHTML = state.grouped.daily.length
    ? state.grouped.daily.map((item) => dailyCard(item)).join("")
    : emptyState("暂无公开科技动向日报。");
  document.querySelector("#daily-detail").innerHTML = "";
}

function isMarketRadarUnlocked() {
  return state.marketRadarUnlocked || sessionStorage.getItem("marketRadarUnlocked") === "true";
}

function setMarketRadarUnlocked(value) {
  state.marketRadarUnlocked = Boolean(value);
  if (value) {
    sessionStorage.setItem("marketRadarUnlocked", "true");
  } else {
    sessionStorage.removeItem("marketRadarUnlocked");
  }
}

function renderMarketRadarLock() {
  const lockView = document.querySelector("#market-radar-lock-view");
  const listView = document.querySelector("#market-radar-list-view");
  const detail = document.querySelector("#market-radar-detail");
  const unlocked = isMarketRadarUnlocked();
  lockView.hidden = unlocked;
  listView.hidden = !unlocked;
  if (!unlocked) {
    detail.innerHTML = "";
  }
  return unlocked;
}

function renderMarketRadar() {
  if (!renderMarketRadarLock()) return;
  document.querySelector("#market-radar-list").innerHTML = state.grouped.marketRadar.length
    ? state.grouped.marketRadar.map((item) => marketRadarCard(item)).join("")
    : emptyState("暂无市场雷达复盘报告。Coze 发布后会自动出现在这里。");
  document.querySelector("#market-radar-detail").innerHTML = "";
}

function stripFrontmatter(markdown) {
  const trimmed = markdown.replace(/^\uFEFF/, "").trimStart();
  const delimiter = trimmed.startsWith("---") ? "---" : trimmed.startsWith("⸻") ? "⸻" : null;
  if (!delimiter) return markdown;

  const lines = trimmed.split(/\r?\n/);
  if (lines[0].trim() !== delimiter) return markdown;
  const endIndex = lines.slice(1).findIndex((line) => line.trim() === delimiter);
  if (endIndex === -1) return markdown;
  return lines.slice(endIndex + 2).join("\n").trim();
}

function renderInlineMarkdown(text) {
  return escapeHtml(text).replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
}

function renderMarkdown(markdown) {
  const body = stripFrontmatter(markdown);
  const lines = body.split(/\r?\n/);
  const html = [];
  let inList = false;
  let inOrderedList = false;
  let inCode = false;
  let codeLines = [];
  let tableLines = [];

  function closeList() {
    if (inList) {
      html.push("</ul>");
      inList = false;
    }
    if (inOrderedList) {
      html.push("</ol>");
      inOrderedList = false;
    }
  }

  function closeCode() {
    if (inCode) {
      html.push(`<pre><code>${escapeHtml(codeLines.join("\n"))}</code></pre>`);
      codeLines = [];
      inCode = false;
    }
  }

  function closeTable() {
    if (!tableLines.length) return;
    const rows = tableLines
      .filter((line) => !/^\|\s*-+/.test(line.trim()))
      .map((line) =>
        line
          .trim()
          .replace(/^\|/, "")
          .replace(/\|$/, "")
          .split("|")
          .map((cell) => renderInlineMarkdown(cell.trim()))
      );
    if (rows.length) {
      const [head, ...bodyRows] = rows;
      html.push("<table>");
      html.push(`<thead><tr>${head.map((cell) => `<th>${cell}</th>`).join("")}</tr></thead>`);
      if (bodyRows.length) {
        html.push("<tbody>");
        bodyRows.forEach((row) => {
          html.push(`<tr>${row.map((cell) => `<td>${cell}</td>`).join("")}</tr>`);
        });
        html.push("</tbody>");
      }
      html.push("</table>");
    }
    tableLines = [];
  }

  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed.startsWith("```")) {
      closeTable();
      closeList();
      if (inCode) {
        closeCode();
      } else {
        inCode = true;
        codeLines = [];
      }
      continue;
    }

    if (inCode) {
      codeLines.push(line);
      continue;
    }

    if (!trimmed) {
      closeTable();
      closeList();
      continue;
    }

    if (trimmed.startsWith("|") && trimmed.endsWith("|")) {
      closeList();
      tableLines.push(line);
      continue;
    }

    closeTable();

    if (trimmed.startsWith("# ")) {
      closeList();
      html.push(`<h1>${renderInlineMarkdown(trimmed.slice(2))}</h1>`);
      continue;
    }

    if (trimmed.startsWith("## ")) {
      closeList();
      html.push(`<h2>${renderInlineMarkdown(trimmed.slice(3))}</h2>`);
      continue;
    }

    if (trimmed.startsWith("### ")) {
      closeList();
      html.push(`<h3>${renderInlineMarkdown(trimmed.slice(4))}</h3>`);
      continue;
    }

    if (/^[-*]\s+/.test(trimmed)) {
      if (!inList) {
        if (inOrderedList) {
          html.push("</ol>");
          inOrderedList = false;
        }
        html.push("<ul>");
        inList = true;
      }
      html.push(`<li>${renderInlineMarkdown(trimmed.replace(/^[-*]\s+/, ""))}</li>`);
      continue;
    }

    if (/^\d+\.\s+/.test(trimmed)) {
      if (!inOrderedList) {
        if (inList) {
          html.push("</ul>");
          inList = false;
        }
        html.push("<ol>");
        inOrderedList = true;
      }
      html.push(`<li>${renderInlineMarkdown(trimmed.replace(/^\d+\.\s+/, ""))}</li>`);
      continue;
    }

    closeList();
    html.push(`<p>${renderInlineMarkdown(trimmed)}</p>`);
  }

  closeTable();
  closeCode();
  closeList();
  return html.join("");
}

function findDailyByDate(date) {
  return state.grouped.daily.find((item) => item.date === date);
}

function findMarketRadarBySlug(slug) {
  return state.grouped.marketRadar.find((item) => marketRadarSlug(item) === slug);
}

function findEcosystemByTitle(title) {
  return state.ecosystems.find((item) => item.title === title);
}

function findThemeByTitle(title) {
  return state.themes.find((item) => item.title === title);
}

function findReportByTitle(title) {
  return state.grouped.reports.find((item) => item.title === title);
}

function findCooperationBySlug(slug) {
  return state.cooperation.find((item) => item.slug === slug);
}

async function openDailyDetail(item) {
  const detail = document.querySelector("#daily-detail");
  const listView = document.querySelector("#daily-list-view");
  listView.hidden = true;

  if (!item) {
    detail.innerHTML = `
      <section class="panel">
        <a class="text-button secondary" href="#daily-intelligence">返回科技动向日报列表</a>
        <p>未找到对应日期的科技动向日报。</p>
      </section>
    `;
    return;
  }

  if (!item.path) {
    detail.innerHTML = `
      <section class="panel">
        <a class="text-button secondary" href="#daily-intelligence">返回科技动向日报列表</a>
        <p>该日报缺少 Markdown 路径。</p>
      </section>
    `;
    return;
  }

  detail.innerHTML = `<section class="panel"><p>正在加载全文...</p></section>`;
  try {
    const response = await fetch(item.path, { cache: "no-cache" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const markdown = await response.text();
    detail.innerHTML = `
      <section class="panel markdown-body">
        <div class="daily-detail-header">
          <a class="text-button secondary" href="#daily-intelligence">返回科技动向日报列表</a>
          <h2>科技动向日报</h2>
          <div class="meta">
            <span>日期：${escapeHtml(item.date || "未标明")}</span>
            <span>来源：${escapeHtml(displaySource(item.source))}</span>
          </div>
        </div>
        ${renderMarkdown(markdown)}
      </section>
    `;
    detail.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) {
    detail.innerHTML = `
      <section class="panel">
        <a class="text-button secondary" href="#daily-intelligence">返回科技动向日报列表</a>
        <p>无法加载 Markdown 全文：${escapeHtml(error.message)}</p>
      </section>
    `;
  }
}

async function openMarketRadarDetail(item) {
  if (!renderMarketRadarLock()) return;
  const detail = document.querySelector("#market-radar-detail");
  const listView = document.querySelector("#market-radar-list-view");
  listView.hidden = true;

  if (!item) {
    detail.innerHTML = `
      <section class="panel">
        <a class="text-button secondary" href="#market-radar">返回市场雷达列表</a>
        <p>未找到对应市场雷达复盘报告。</p>
      </section>
    `;
    return;
  }

  if (!item.path) {
    detail.innerHTML = `
      <section class="panel">
        <a class="text-button secondary" href="#market-radar">返回市场雷达列表</a>
        <p>该复盘报告缺少 Markdown 路径。</p>
      </section>
    `;
    return;
  }

  detail.innerHTML = `<section class="panel"><p>正在加载复盘报告...</p></section>`;
  try {
    const response = await fetch(item.path, { cache: "no-cache" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const markdown = await response.text();
    detail.innerHTML = `
      <section class="panel markdown-body">
        <div class="daily-detail-header">
          <a class="text-button secondary" href="#market-radar">返回市场雷达列表</a>
          <h2>${escapeHtml(item.title || "市场雷达复盘报告")}</h2>
          <div class="meta">
            ${item.date ? `<span>日期：${escapeHtml(item.date)}</span>` : ""}
            ${item.market || item.markets ? `<span>市场：${escapeHtml(formatMetaValue(item.market || item.markets))}</span>` : ""}
            <span>来源：${escapeHtml(displaySource(item.source))}</span>
          </div>
          ${formatTags(item.tags)}
        </div>
        ${renderMarkdown(markdown)}
      </section>
    `;
    detail.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) {
    detail.innerHTML = `
      <section class="panel">
        <a class="text-button secondary" href="#market-radar">返回市场雷达列表</a>
        <p>无法加载复盘报告：${escapeHtml(error.message)}</p>
      </section>
    `;
  }
}

function renderEcosystems() {
  const publicEcosystemMap = new Map(state.ecosystems.map((item) => [item.title || item.ecosystem, item]));
  document.querySelector("#ecosystem-list").innerHTML = ECOSYSTEMS
    .map((name) => ecosystemCard(publicEcosystemMap.get(name), name))
    .join("");
  document.querySelector("#ecosystem-detail").innerHTML = "";
}

function stripSectionHeading(markdown) {
  return String(markdown || "")
    .replace(/^##\s+(?:\d+\.\s*)?.+?\s*\n+/, "")
    .trim();
}

function sectionBlock(title, markdown) {
  if (!markdown) return "";
  const body = stripSectionHeading(markdown);
  if (!body) return "";
  return `
    <section class="ecosystem-section">
      <h3 class="ecosystem-section-title">${escapeHtml(title)}</h3>
      ${renderMarkdown(body)}
    </section>
  `;
}

function openEcosystemDetail(item) {
  const detail = document.querySelector("#ecosystem-detail");
  const listView = document.querySelector("#ecosystem-list-view");
  listView.hidden = true;

  if (!item) {
    detail.innerHTML = `
      <section class="panel">
        <a class="text-button secondary" href="#strategic-ecosystems">返回战略生态列表</a>
        <p>未找到对应战略生态。</p>
      </section>
    `;
    return;
  }

  const sections = item.sections || {};
  const detailSections = {
    definition: sections.definition || sections.ecosystem_definition,
    industry_chain: sections.industry_chain,
    value_chain: sections.value_chain,
    sub_chains: sections.sub_chains,
    companies: sections.companies || sections.company_pool,
    indicators: sections.indicators || sections.tracking_indicators,
    questions: sections.questions || sections.key_questions,
    relations: sections.relations || sections.related_ecosystems,
    coze_rules: sections.coze_rules,
  };
  const sectionHtml = ecosystemSectionOrder
    .filter(([key]) => stripSectionHeading(detailSections[key]).length > 0)
    .map(([key, title], index) => sectionBlock(`${index + 1}. ${title}`, detailSections[key]))
    .join("");
  detail.innerHTML = `
    <section class="panel markdown-body ecosystem-detail">
      <div class="daily-detail-header">
        <a class="text-button secondary" href="#strategic-ecosystems">返回战略生态列表</a>
        <h2>${escapeHtml(item.title || "战略生态")}</h2>
        <div class="meta">
          <span>重点公司数量：${Number(item.company_count ?? asArray(item.linked_companies).length ?? 0)}</span>
          ${item.source_path ? `<span>来源：${escapeHtml(item.source_path)}</span>` : ""}
        </div>
        ${formatTags(item.tags)}
      </div>
      ${sectionHtml}
    </section>
  `;
  detail.scrollIntoView({ behavior: "smooth", block: "start" });
}

function openThemeDetail(item) {
  const detail = document.querySelector("#report-detail");
  const listView = document.querySelector("#report-list-view");
  listView.hidden = true;

  if (!item) {
    detail.innerHTML = `
      <section class="panel">
        <a class="text-button secondary" href="#research-reports">返回研究报告列表</a>
        <p>未找到对应专题。</p>
      </section>
    `;
    return;
  }

  const sections = item.sections || {};
  const sectionHtml = themeSectionOrder
    .filter(([key]) => stripSectionHeading(sections[key]).length > 0)
    .map(([key, title], index) => sectionBlock(`${index + 1}. ${title}`, sections[key]))
    .join("");

  detail.innerHTML = `
    <section class="panel markdown-body ecosystem-detail">
      <div class="daily-detail-header">
        <a class="text-button secondary" href="#research-reports">返回研究报告列表</a>
        <h2>${escapeHtml(item.title || "长期专题")}</h2>
        ${formatTags(item.tags)}
      </div>
      ${sectionHtml}
    </section>
  `;
  detail.scrollIntoView({ behavior: "smooth", block: "start" });
}

async function openReportDetail(item) {
  const detail = document.querySelector("#report-detail");
  const listView = document.querySelector("#report-list-view");
  listView.hidden = true;

  if (!item) {
    detail.innerHTML = `
      <section class="panel">
        <a class="text-button secondary" href="#research-reports">返回研究报告列表</a>
        <p>未找到对应研究报告。</p>
      </section>
    `;
    return;
  }

  if (!item.path) {
    detail.innerHTML = `
      <section class="panel">
        <a class="text-button secondary" href="#research-reports">返回研究报告列表</a>
        <p>该研究报告缺少 Markdown 路径。</p>
      </section>
    `;
    return;
  }

  detail.innerHTML = `<section class="panel"><p>正在加载研究报告...</p></section>`;
  try {
    const response = await fetch(item.path, { cache: "no-cache" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const markdown = await response.text();
    detail.innerHTML = `
      <section class="panel markdown-body ecosystem-detail">
        <div class="daily-detail-header">
          <a class="text-button secondary" href="#research-reports">返回研究报告列表</a>
          <h2>${escapeHtml(item.title || "研究报告")}</h2>
          ${formatTags(item.tags)}
        </div>
        ${renderMarkdown(markdown)}
      </section>
    `;
    detail.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) {
    detail.innerHTML = `
      <section class="panel">
        <a class="text-button secondary" href="#research-reports">返回研究报告列表</a>
        <p>无法加载研究报告：${escapeHtml(error.message)}</p>
      </section>
    `;
  }
}

function renderCooperation() {
  document.querySelector("#cooperation-list").innerHTML = cooperationTable(state.cooperation);
  document.querySelector("#cooperation-detail").innerHTML = "";
}

function openCooperationDetail(item) {
  const detail = document.querySelector("#cooperation-detail");
  const listView = document.querySelector("#cooperation-list-view");
  listView.hidden = true;

  if (!item) {
    detail.innerHTML = `
      <section class="panel">
        <a class="text-button secondary" href="#cooperation-opportunities">返回合作机会列表</a>
        <p>未找到对应合作机会文章。</p>
      </section>
    `;
    return;
  }

  detail.innerHTML = `
    <section class="panel markdown-body cooperation-detail">
      <div class="daily-detail-header">
        <a class="text-button secondary" href="#cooperation-opportunities">返回合作机会列表</a>
        <h2>${escapeHtml(item.title || "合作机会")}</h2>
        <div class="meta">
          ${item.date ? `<span>发布日期：${escapeHtml(item.date)}</span>` : ""}
          ${item.opportunity_type ? `<span>机会类型：${escapeHtml(item.opportunity_type)}</span>` : ""}
        </div>
      </div>
      ${item.summary ? `<p class="lead">${escapeHtml(item.summary)}</p>` : ""}
      ${item.content ? renderMarkdown(item.content) : ""}
      <section class="ecosystem-section">
        <h3 class="ecosystem-section-title">联系方式</h3>
        <p>${escapeHtml(item.contact_note || "微信：rachelao")}</p>
      </section>
      <section class="notice large">
        <h3>免责声明</h3>
        <p>${escapeHtml(item.disclaimer || "本文章仅用于产业研究、合作交流和商业机会对接。")}</p>
      </section>
    </section>
  `;
  detail.scrollIntoView({ behavior: "smooth", block: "start" });
}

function renderReports() {
  const standaloneReports = state.grouped.reports.filter((item) => {
    const sameThemeTitle = state.themes.some((theme) => item.title === theme.title);
    return !sameThemeTitle;
  });
  const reportItems = [
    ...state.themes.map((item) => themeCard(item)),
    ...standaloneReports.map((item) => reportCard(item)),
  ];
  document.querySelector("#report-list").innerHTML = reportItems.length
    ? reportItems.join("")
    : emptyState("暂无公开报告或知识图谱。");
  document.querySelector("#report-detail").innerHTML = "";
}

function navigate() {
  const rawHash = decodeURIComponent(location.hash || "#home");
  const dailyDetailMatch = rawHash.match(/^#\/daily-intelligence\/([^/]+)$/)
    || rawHash.match(/^#\/daily\/([^/]+)$/);
  const marketRadarDetailMatch = rawHash.match(/^#\/market-radar\/([^/]+)$/);
  const ecosystemDetailMatch = rawHash.match(/^#\/strategic-ecosystems\/([^/]+)$/)
    || rawHash.match(/^#\/ecosystems\/([^/]+)$/);
  const themeDetailMatch = rawHash.match(/^#\/research-reports\/([^/]+)$/)
    || rawHash.match(/^#\/themes\/([^/]+)$/);
  const cooperationDetailMatch = rawHash.match(/^#\/cooperation-opportunities\/([^/]+)$/)
    || rawHash.match(/^#\/company-observations\/([^/]+)$/)
    || rawHash.match(/^#\/companies\/([^/]+)$/);
  const hashRoute = rawHash.replace("#", "") || "home";
  const routeAliases = {
    daily: "daily",
    "daily-intelligence": "daily",
    "/daily": "daily",
    "/daily-intelligence": "daily",
    "market-radar": "market-radar",
    "/market-radar": "market-radar",
    ecosystems: "ecosystems",
    "strategic-ecosystems": "ecosystems",
    "/ecosystems": "ecosystems",
    "/strategic-ecosystems": "ecosystems",
    reports: "reports",
    themes: "reports",
    "research-reports": "reports",
    "/reports": "reports",
    "/themes": "reports",
    "/research-reports": "reports",
    companies: "cooperation-opportunities",
    "company-observations": "cooperation-opportunities",
    "/companies": "cooperation-opportunities",
    "/company-observations": "cooperation-opportunities",
    "cooperation-opportunities": "cooperation-opportunities",
    "/cooperation-opportunities": "cooperation-opportunities",
  };
  const normalizedHashRoute = routeAliases[hashRoute] || hashRoute;
  const route = dailyDetailMatch
    ? "daily"
    : marketRadarDetailMatch
      ? "market-radar"
      : ecosystemDetailMatch
        ? "ecosystems"
        : themeDetailMatch
          ? "reports"
          : cooperationDetailMatch
            ? "cooperation-opportunities"
            : normalizedHashRoute === "disclaimer"
            ? "about"
            : normalizedHashRoute;

  document.querySelectorAll(".view").forEach((view) => {
    view.classList.toggle("is-active", view.dataset.route === route);
  });
  document.querySelectorAll("nav a").forEach((link) => {
    const navRoute = route === "daily"
      ? "#daily-intelligence"
      : route === "market-radar"
        ? "#market-radar"
        : route === "ecosystems"
          ? "#strategic-ecosystems"
          : route === "cooperation-opportunities"
            ? "#cooperation-opportunities"
            : route === "reports"
              ? "#research-reports"
            : `#${route}`;
    link.classList.toggle("is-active", link.getAttribute("href") === navRoute);
  });

  const dailyListView = document.querySelector("#daily-list-view");
  const dailyDetail = document.querySelector("#daily-detail");
  const marketRadarListView = document.querySelector("#market-radar-list-view");
  const marketRadarDetail = document.querySelector("#market-radar-detail");
  const ecosystemListView = document.querySelector("#ecosystem-list-view");
  const ecosystemDetail = document.querySelector("#ecosystem-detail");
  const reportListView = document.querySelector("#report-list-view");
  const reportDetail = document.querySelector("#report-detail");
  const cooperationListView = document.querySelector("#cooperation-list-view");
  const cooperationDetail = document.querySelector("#cooperation-detail");
  if (route !== "daily") {
    dailyListView.hidden = false;
    dailyDetail.innerHTML = "";
  }

  if (route !== "market-radar") {
    marketRadarListView.hidden = !isMarketRadarUnlocked();
    marketRadarDetail.innerHTML = "";
  }

  if (route !== "ecosystems") {
    ecosystemListView.hidden = false;
    ecosystemDetail.innerHTML = "";
  }

  if (route !== "reports") {
    reportListView.hidden = false;
    reportDetail.innerHTML = "";
  }

  if (route !== "cooperation-opportunities") {
    cooperationListView.hidden = false;
    cooperationDetail.innerHTML = "";
  }

  if (route === "daily") {
    if (dailyDetailMatch) {
      const dailyItem = findDailyByDate(dailyDetailMatch[1]);
      updateDocumentMeta(route, dailyItem);
      openDailyDetail(dailyItem);
    } else {
      updateDocumentMeta(route);
      dailyListView.hidden = false;
      dailyDetail.innerHTML = "";
    }
  }

  if (route === "market-radar") {
    if (marketRadarDetailMatch) {
      const marketRadarItem = findMarketRadarBySlug(marketRadarDetailMatch[1]);
      updateDocumentMeta(route, marketRadarItem);
      openMarketRadarDetail(marketRadarItem);
    } else {
      updateDocumentMeta(route);
      renderMarketRadar();
    }
  }

  if (route === "ecosystems") {
    if (ecosystemDetailMatch) {
      const ecosystemItem = findEcosystemByTitle(ecosystemDetailMatch[1]);
      updateDocumentMeta(route, ecosystemItem);
      openEcosystemDetail(ecosystemItem);
    } else {
      updateDocumentMeta(route);
      ecosystemListView.hidden = false;
      ecosystemDetail.innerHTML = "";
    }
  }

  if (route === "reports") {
    if (themeDetailMatch) {
      const themeItem = findThemeByTitle(themeDetailMatch[1]);
      const reportItem = themeItem ? null : findReportByTitle(themeDetailMatch[1]);
      updateDocumentMeta(route, themeItem || reportItem);
      if (themeItem) {
        openThemeDetail(themeItem);
      } else {
        openReportDetail(reportItem);
      }
    } else {
      updateDocumentMeta(route);
      reportListView.hidden = false;
      reportDetail.innerHTML = "";
    }
  }

  if (route === "cooperation-opportunities") {
    if (cooperationDetailMatch) {
      const cooperationItem = findCooperationBySlug(cooperationDetailMatch[1]);
      updateDocumentMeta(route, cooperationItem);
      openCooperationDetail(cooperationItem);
    } else {
      updateDocumentMeta(route);
      cooperationListView.hidden = false;
      cooperationDetail.innerHTML = "";
    }
  }

  if (!["daily", "market-radar", "ecosystems", "reports", "cooperation-opportunities"].includes(route)) {
    updateDocumentMeta(route);
  }
}

async function loadContent() {
  try {
    const [contentResponse, ecosystemResponse, themeResponse, cooperationResponse] = await Promise.all([
      fetch("data/public_content.json", { cache: "no-cache" }),
      fetch("data/ecosystems.json", { cache: "no-cache" }),
      fetch("data/themes.json", { cache: "no-cache" }),
      fetch("data/cooperation_opportunities.json", { cache: "no-cache" }),
    ]);
    if (!contentResponse.ok) throw new Error(`public_content HTTP ${contentResponse.status}`);
    if (!ecosystemResponse.ok) throw new Error(`ecosystems HTTP ${ecosystemResponse.status}`);
    if (!themeResponse.ok) throw new Error(`themes HTTP ${themeResponse.status}`);
    if (!cooperationResponse.ok) throw new Error(`cooperation_opportunities HTTP ${cooperationResponse.status}`);
    const payload = await contentResponse.json();
    const ecosystemsPayload = await ecosystemResponse.json();
    const themesPayload = await themeResponse.json();
    const cooperationPayload = await cooperationResponse.json();
    state.content = Array.isArray(payload.items) ? payload.items : [];
    state.ecosystems = Array.isArray(ecosystemsPayload) ? ecosystemsPayload : [];
    state.themes = Array.isArray(themesPayload) ? themesPayload : [];
    state.cooperation = Array.isArray(cooperationPayload)
      ? cooperationPayload
      : Array.isArray(cooperationPayload.items)
        ? cooperationPayload.items
        : [];
    document.querySelector("#last-updated").textContent = payload.generated_at
      ? `公开数据更新时间：${payload.generated_at}`
      : "公开数据已加载";
  } catch (error) {
    state.content = [];
    state.ecosystems = [];
    state.themes = [];
    state.cooperation = [];
    document.querySelector("#last-updated").textContent = "尚未导出公开数据";
  }

  groupContent(state.content);
  if (!state.ecosystems.length) {
    state.ecosystems = state.grouped.ecosystems;
  }
  renderHome();
  renderDaily();
  renderMarketRadar();
  renderEcosystems();
  renderCooperation();
  renderReports();
  navigate();
}

document.querySelector("#market-radar-password-form")?.addEventListener("submit", (event) => {
  event.preventDefault();
  const input = document.querySelector("#market-radar-password");
  const error = document.querySelector("#market-radar-password-error");
  const value = String(input?.value || "");
  if (value === MARKET_RADAR_PASSWORD) {
    setMarketRadarUnlocked(true);
    if (error) error.hidden = true;
    if (input) input.value = "";
    renderMarketRadar();
    navigate();
    return;
  }
  if (error) error.hidden = false;
});

window.addEventListener("hashchange", navigate);
loadContent();
