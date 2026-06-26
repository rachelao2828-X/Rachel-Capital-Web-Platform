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
  ["companies", "关键公司观察池"],
  ["indicators", "长期跟踪指标"],
  ["questions", "关键问题"],
  ["relations", "与其他生态的关系"],
  ["coze_rules", "Coze 日报自动关联规则"],
  ["next_tasks", "下一步研究任务"],
];

const state = {
  content: [],
  ecosystems: [],
  grouped: {
    daily: [],
    companies: [],
    ecosystems: [],
    reports: [],
  },
};

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
    company: "公司观察",
    ecosystem: "战略生态",
    report: "研究报告",
    knowledge_graph: "知识图谱",
  };
  return labels[value] || value || "";
}

function dailyUrl(item) {
  return item?.date ? `#/daily/${encodeURIComponent(item.date)}` : "#daily";
}

function ecosystemUrl(item) {
  return item?.title ? `#/ecosystems/${encodeURIComponent(item.title)}` : "#ecosystems";
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

function groupContent(items) {
  state.grouped.daily = items.filter((item) => item.type === "daily_intelligence");
  state.grouped.companies = items.filter((item) => item.type === "company");
  state.grouped.ecosystems = items.filter((item) => item.type === "ecosystem");
  state.grouped.reports = items.filter((item) => item.type === "report" || item.type === "knowledge_graph");
}

function renderHome() {
  const latestDaily = state.grouped.daily.slice(0, 1);
  const latestReports = state.grouped.reports.slice(0, 3);
  const latestCompanies = state.grouped.companies.slice(0, 4);

  document.querySelector("#home-daily").innerHTML = latestDaily.length
    ? latestDaily.map((item) => homeDailyCard(item)).join("")
    : emptyState("暂无公开日报。请在 Obsidian 中将可公开日报标记为 public: true 后导出。");

  document.querySelector("#home-ecosystems").innerHTML = ECOSYSTEMS
    .map((name) => state.ecosystems.find((item) => item.title === name))
    .filter(Boolean)
    .map((item) => homeEcosystemCard(item))
    .join("") || emptyState("暂无公开战略生态。");

  document.querySelector("#home-reports").innerHTML = latestReports.length
    ? latestReports.map((item) => itemCard(item)).join("")
    : emptyState("暂无公开研究报告。");

  document.querySelector("#home-companies").innerHTML = latestCompanies.length
    ? latestCompanies.map((item) => itemCard(item)).join("")
    : emptyState("暂无公开公司观察。");
}

function renderDaily() {
  document.querySelector("#daily-list").innerHTML = state.grouped.daily.length
    ? state.grouped.daily.map((item) => dailyCard(item)).join("")
    : emptyState("暂无公开科技动向日报。");
  document.querySelector("#daily-detail").innerHTML = "";
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
  let inCode = false;
  let codeLines = [];
  let tableLines = [];

  function closeList() {
    if (inList) {
      html.push("</ul>");
      inList = false;
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
        html.push("<ul>");
        inList = true;
      }
      html.push(`<li>${renderInlineMarkdown(trimmed.replace(/^[-*]\s+/, ""))}</li>`);
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

function findEcosystemByTitle(title) {
  return state.ecosystems.find((item) => item.title === title);
}

async function openDailyDetail(item) {
  const detail = document.querySelector("#daily-detail");
  const listView = document.querySelector("#daily-list-view");
  listView.hidden = true;

  if (!item) {
    detail.innerHTML = `
      <section class="panel">
        <a class="text-button secondary" href="#daily">返回科技动向日报列表</a>
        <p>未找到对应日期的科技动向日报。</p>
      </section>
    `;
    return;
  }

  if (!item.path) {
    detail.innerHTML = `
      <section class="panel">
        <a class="text-button secondary" href="#daily">返回科技动向日报列表</a>
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
          <a class="text-button secondary" href="#daily">返回科技动向日报列表</a>
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
        <a class="text-button secondary" href="#daily">返回科技动向日报列表</a>
        <p>无法加载 Markdown 全文：${escapeHtml(error.message)}</p>
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
        <a class="text-button secondary" href="#ecosystems">返回战略生态列表</a>
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
    next_tasks: sections.next_tasks || sections.next_research_tasks || item.next_research_tasks,
  };
  const sectionHtml = ecosystemSectionOrder
    .filter(([key]) => stripSectionHeading(detailSections[key]).length > 0)
    .map(([key, title], index) => sectionBlock(`${index + 1}. ${title}`, detailSections[key]))
    .join("");
  detail.innerHTML = `
    <section class="panel markdown-body ecosystem-detail">
      <div class="daily-detail-header">
        <a class="text-button secondary" href="#ecosystems">返回战略生态列表</a>
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

function renderCompanies() {
  document.querySelector("#company-list").innerHTML = state.grouped.companies.length
    ? state.grouped.companies.map((item) => itemCard(item, { detail: true })).join("")
    : emptyState("暂无公开公司研究摘要。");
}

function renderReports() {
  document.querySelector("#report-list").innerHTML = state.grouped.reports.length
    ? state.grouped.reports.map((item) => itemCard(item, { detail: true })).join("")
    : emptyState("暂无公开报告或知识图谱。");
}

function navigate() {
  const rawHash = decodeURIComponent(location.hash || "#home");
  const dailyDetailMatch = rawHash.match(/^#\/daily\/([^/]+)$/);
  const ecosystemDetailMatch = rawHash.match(/^#\/ecosystems\/([^/]+)$/);
  const hashRoute = rawHash.replace("#", "") || "home";
  const route = dailyDetailMatch
    ? "daily"
    : ecosystemDetailMatch
      ? "ecosystems"
      : hashRoute === "disclaimer"
        ? "about"
        : hashRoute;

  document.querySelectorAll(".view").forEach((view) => {
    view.classList.toggle("is-active", view.dataset.route === route);
  });
  document.querySelectorAll("nav a").forEach((link) => {
    const navRoute = route === "daily" ? "#daily" : route === "ecosystems" ? "#ecosystems" : `#${route}`;
    link.classList.toggle("is-active", link.getAttribute("href") === navRoute);
  });

  const dailyListView = document.querySelector("#daily-list-view");
  const dailyDetail = document.querySelector("#daily-detail");
  const ecosystemListView = document.querySelector("#ecosystem-list-view");
  const ecosystemDetail = document.querySelector("#ecosystem-detail");
  if (route !== "daily") {
    dailyListView.hidden = false;
    dailyDetail.innerHTML = "";
  }

  if (route !== "ecosystems") {
    ecosystemListView.hidden = false;
    ecosystemDetail.innerHTML = "";
  }

  if (route === "daily") {
    if (dailyDetailMatch) {
      openDailyDetail(findDailyByDate(dailyDetailMatch[1]));
    } else {
      dailyListView.hidden = false;
      dailyDetail.innerHTML = "";
    }
  }

  if (route === "ecosystems") {
    if (ecosystemDetailMatch) {
      openEcosystemDetail(findEcosystemByTitle(ecosystemDetailMatch[1]));
    } else {
      ecosystemListView.hidden = false;
      ecosystemDetail.innerHTML = "";
    }
  }
}

async function loadContent() {
  try {
    const [contentResponse, ecosystemResponse] = await Promise.all([
      fetch("data/public_content.json", { cache: "no-cache" }),
      fetch("data/ecosystems.json", { cache: "no-cache" }),
    ]);
    if (!contentResponse.ok) throw new Error(`public_content HTTP ${contentResponse.status}`);
    if (!ecosystemResponse.ok) throw new Error(`ecosystems HTTP ${ecosystemResponse.status}`);
    const payload = await contentResponse.json();
    const ecosystemsPayload = await ecosystemResponse.json();
    state.content = Array.isArray(payload.items) ? payload.items : [];
    state.ecosystems = Array.isArray(ecosystemsPayload) ? ecosystemsPayload : [];
    document.querySelector("#last-updated").textContent = payload.generated_at
      ? `公开数据更新时间：${payload.generated_at}`
      : "公开数据已加载";
  } catch (error) {
    state.content = [];
    state.ecosystems = [];
    document.querySelector("#last-updated").textContent = "尚未导出公开数据";
  }

  groupContent(state.content);
  if (!state.ecosystems.length) {
    state.ecosystems = state.grouped.ecosystems;
  }
  renderHome();
  renderDaily();
  renderEcosystems();
  renderCompanies();
  renderReports();
  navigate();
}

window.addEventListener("hashchange", navigate);
loadContent();
