const ECOSYSTEMS = [
  "AI基础设施生态",
  "半导体生态",
  "华为生态",
  "机器人生态",
  "高端材料生态",
  "船舶与国防生态",
  "医疗科技生态",
];

const state = {
  content: [],
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

function formatTags(values) {
  const tags = asArray(values);
  if (!tags.length) return "";
  return `<div class="meta">${tags.map((tag) => `<span class="tag">${escapeHtml(tag)}</span>`).join("")}</div>`;
}

function itemCard(item, options = {}) {
  const title = escapeHtml(item.title || "Untitled");
  const date = escapeHtml(item.date || "");
  const ecosystem = escapeHtml(item.ecosystem || "");
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
        ${item.type ? `<span>${escapeHtml(item.type)}</span>` : ""}
      </div>
      ${summary ? `<p>${summary}</p>` : ""}
      ${tags}
      ${detail}
    </article>
  `;
}

function dailyCard(item) {
  const title = escapeHtml(item.title || "Untitled");
  const date = escapeHtml(item.date || "");
  const summary = escapeHtml(item.summary || item.excerpt || "");
  const tags = formatTags(item.tags);

  return `
    <article class="card">
      <h3>${title}</h3>
      <div class="meta">
        ${date ? `<span>${date}</span>` : ""}
        ${item.ecosystem ? `<span>${escapeHtml(item.ecosystem)}</span>` : ""}
      </div>
      ${summary ? `<p>${summary}</p>` : ""}
      ${tags}
      <button class="text-button" type="button" data-daily-path="${escapeHtml(item.path || "")}">
        阅读全文
      </button>
    </article>
  `;
}

function emptyState(label) {
  return `<div class="card"><p>${label}</p></div>`;
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
    ? latestDaily.map((item) => itemCard(item)).join("")
    : emptyState("暂无公开日报。请在 Obsidian 中将可公开日报标记为 public: true 后导出。");

  document.querySelector("#home-ecosystems").innerHTML = ECOSYSTEMS
    .map((name) => `<span class="tag">${escapeHtml(name)}</span>`)
    .join("");

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
    : emptyState("暂无公开 Daily Intelligence。");
  document.querySelector("#daily-detail").innerHTML = "";
  document.querySelectorAll("[data-daily-path]").forEach((button) => {
    button.addEventListener("click", () => openDailyDetail(button.dataset.dailyPath));
  });
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

  function closeList() {
    if (inList) {
      html.push("</ul>");
      inList = false;
    }
  }

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) {
      closeList();
      continue;
    }

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

  closeList();
  return html.join("");
}

async function openDailyDetail(path) {
  const detail = document.querySelector("#daily-detail");
  if (!path) {
    detail.innerHTML = `<section class="panel"><p>该日报缺少 Markdown 路径。</p></section>`;
    return;
  }

  detail.innerHTML = `<section class="panel"><p>正在加载全文...</p></section>`;
  try {
    const response = await fetch(path, { cache: "no-cache" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const markdown = await response.text();
    detail.innerHTML = `
      <section class="panel markdown-body">
        <button class="text-button secondary" type="button" id="close-daily-detail">关闭全文</button>
        ${renderMarkdown(markdown)}
      </section>
    `;
    document.querySelector("#close-daily-detail").addEventListener("click", () => {
      detail.innerHTML = "";
    });
    detail.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) {
    detail.innerHTML = `<section class="panel"><p>无法加载 Markdown 全文：${escapeHtml(error.message)}</p></section>`;
  }
}

function renderEcosystems() {
  const publicEcosystemMap = new Map(state.grouped.ecosystems.map((item) => [item.title || item.ecosystem, item]));
  document.querySelector("#ecosystem-list").innerHTML = ECOSYSTEMS
    .map((name) => {
      const item = publicEcosystemMap.get(name);
      return `
        <article class="card">
          <h3>${escapeHtml(name)}</h3>
          <p>${escapeHtml(item?.summary || "待发布公开生态观察。")}</p>
          ${item?.body ? `<details><summary>查看详情</summary><p>${escapeHtml(item.body).replaceAll("\n", "<br />")}</p></details>` : ""}
        </article>
      `;
    })
    .join("");
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
  const route = (location.hash || "#home").replace("#", "");
  document.querySelectorAll(".view").forEach((view) => {
    view.classList.toggle("is-active", view.dataset.route === route);
  });
  document.querySelectorAll("nav a").forEach((link) => {
    link.classList.toggle("is-active", link.getAttribute("href") === `#${route}`);
  });
}

async function loadContent() {
  try {
    const response = await fetch("data/public_content.json", { cache: "no-cache" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const payload = await response.json();
    state.content = Array.isArray(payload.items) ? payload.items : [];
    document.querySelector("#last-updated").textContent = payload.generated_at
      ? `Data updated: ${payload.generated_at}`
      : "Public data loaded";
  } catch (error) {
    state.content = [];
    document.querySelector("#last-updated").textContent = "No public data exported yet";
  }

  groupContent(state.content);
  renderHome();
  renderDaily();
  renderEcosystems();
  renderCompanies();
  renderReports();
  navigate();
}

window.addEventListener("hashchange", navigate);
loadContent();
