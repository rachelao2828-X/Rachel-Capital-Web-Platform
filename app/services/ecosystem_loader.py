from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from app.core.config import settings
from app.services.valuation_engine.model_registry import ECOSYSTEM_OPTIONS


ECOSYSTEM_SOURCE_DIR = "02_战略生态"
CROSS_MAP_NAME = "七大战略生态交叉关系图谱"
SECTION_ALIASES = {
    "生态定位": ["生态定位", "生态定义"],
    "核心逻辑": ["核心逻辑"],
    "产业链结构": ["产业链结构"],
    "关键环节": ["关键环节"],
    "关键技术": ["关键技术"],
    "代表公司 / 项目类型": ["核心公司观察池", "关键公司观察池", "代表公司 / 项目类型", "代表公司"],
    "主要瓶颈与风险": ["主要瓶颈与风险", "风险因素"],
    "跟踪优先级": ["跟踪优先级"],
    "跟踪指标": ["跟踪指标", "长期跟踪指标"],
    "研究任务": ["研究任务", "下一步研究任务"],
    "与其他生态关系": ["与其他战略生态的关系", "与其他生态的关系"],
}
CROSS_MAP_SECTION_ALIASES = {
    "summary": ["核心定位", "总体关系框架"],
    "cross_matrix": ["生态交叉矩阵"],
    "priority_themes": ["高优先级交叉主题"],
    "tracking_indicators": ["交叉关系跟踪指标"],
}


@dataclass(frozen=True)
class EcosystemDocument:
    title: str
    path: Path
    exists: bool
    status: str
    public: bool | None
    metadata: dict[str, object]
    sections: dict[str, str]
    raw_preview: str


def ecosystem_names() -> list[str]:
    return [name for name in ECOSYSTEM_OPTIONS if name not in {"中国关键技术攻关长期跟踪", "其他"}]


def ecosystem_root(vault_path: str | None = None) -> Path:
    vault = Path(vault_path or settings.obsidian_vault_path or "")
    return vault / ECOSYSTEM_SOURCE_DIR


def ecosystem_path(name: str, vault_path: str | None = None) -> Path:
    return ecosystem_root(vault_path) / f"{name}.md"


def ecosystem_cross_map_path(vault_path: str | None = None) -> Path:
    return ecosystem_path(CROSS_MAP_NAME, vault_path=vault_path)


def load_ecosystems(vault_path: str | None = None) -> list[EcosystemDocument]:
    return [load_ecosystem(name, vault_path=vault_path) for name in ecosystem_names()]


def load_ecosystem(name: str, vault_path: str | None = None) -> EcosystemDocument:
    path = ecosystem_path(name, vault_path=vault_path)
    if not path.exists():
        return EcosystemDocument(
            title=name,
            path=path,
            exists=False,
            status="未读取",
            public=None,
            metadata={},
            sections={},
            raw_preview="",
        )

    raw = path.read_text(encoding="utf-8")
    metadata, body = split_frontmatter(raw)
    sections = extract_sections(body)
    normalized_sections = normalize_sections(sections)
    title = str(metadata.get("title") or first_heading(body) or name)
    public = parse_bool(metadata.get("public"))
    preview = body.strip()[:1200]

    return EcosystemDocument(
        title=title,
        path=path,
        exists=True,
        status="已读取",
        public=public,
        metadata=metadata,
        sections=normalized_sections,
        raw_preview=preview,
    )


def load_ecosystem_cross_map(vault_path: str | None = None) -> dict[str, object]:
    path = ecosystem_cross_map_path(vault_path=vault_path)
    if not path.exists():
        return {
            "name": CROSS_MAP_NAME,
            "file_path": str(path),
            "status": "待建设",
            "public": None,
            "summary": "",
            "cross_matrix": [],
            "priority_themes": [],
            "tracking_indicators": [],
            "raw_markdown": "",
        }

    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return {
            "name": CROSS_MAP_NAME,
            "file_path": str(path),
            "status": "读取失败",
            "public": None,
            "summary": "",
            "cross_matrix": [],
            "priority_themes": [],
            "tracking_indicators": [],
            "raw_markdown": "",
        }

    metadata, body = split_frontmatter(raw)
    sections = extract_sections(body)
    public = parse_bool(metadata.get("public"))
    summary = first_matching_section(sections, CROSS_MAP_SECTION_ALIASES["summary"])
    matrix_section = first_matching_section(sections, CROSS_MAP_SECTION_ALIASES["cross_matrix"])
    themes_section = first_matching_section(sections, CROSS_MAP_SECTION_ALIASES["priority_themes"])
    indicators_section = first_matching_section(sections, CROSS_MAP_SECTION_ALIASES["tracking_indicators"])

    return {
        "name": str(metadata.get("title") or first_heading(body) or CROSS_MAP_NAME),
        "file_path": str(path),
        "status": "已读取",
        "public": public,
        "summary": summary,
        "cross_matrix": parse_markdown_table(matrix_section),
        "priority_themes": extract_subsections(themes_section),
        "tracking_indicators": extract_subsections(indicators_section),
        "raw_markdown": body.strip()[:2400],
    }


def split_frontmatter(raw: str) -> tuple[dict[str, object], str]:
    text = raw.replace("\ufeff", "")
    if not text.lstrip().startswith("---"):
        return {}, text

    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text

    end_index = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_index = index
            break

    if end_index is None:
        return {}, text

    frontmatter = "\n".join(lines[1:end_index])
    body = "\n".join(lines[end_index + 1 :])
    return parse_frontmatter(frontmatter), body


def parse_frontmatter(frontmatter: str) -> dict[str, object]:
    metadata: dict[str, object] = {}
    current_key: str | None = None
    for raw_line in frontmatter.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("- ") and current_key:
            value = stripped[2:].strip().strip('"')
            current = metadata.setdefault(current_key, [])
            if isinstance(current, list):
                current.append(value)
            continue
        if ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()
        current_key = key
        if value == "":
            metadata[key] = []
        else:
            metadata[key] = parse_scalar(value)
    return metadata


def parse_scalar(value: str) -> object:
    cleaned = value.strip().strip('"')
    lowered = cleaned.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    return cleaned


def parse_bool(value: object) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.lower()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
    return None


def first_heading(body: str) -> str | None:
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return None


def extract_sections(body: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current_title: str | None = None
    heading_pattern = re.compile(r"^##\s+(?:\d+[.、]\s*)?(.+?)\s*$")

    for line in body.splitlines():
        match = heading_pattern.match(line)
        if match:
            current_title = match.group(1).strip()
            sections.setdefault(current_title, [])
            continue
        if current_title:
            sections[current_title].append(line)

    return {title: "\n".join(lines).strip() for title, lines in sections.items()}


def normalize_sections(sections: dict[str, str]) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for canonical, aliases in SECTION_ALIASES.items():
        for alias in aliases:
            if alias in sections and sections[alias].strip():
                normalized[canonical] = sections[alias].strip()
                break
    return normalized


def first_matching_section(sections: dict[str, str], aliases: list[str]) -> str:
    for alias in aliases:
        if alias in sections and sections[alias].strip():
            return sections[alias].strip()
    return ""


def parse_markdown_table(markdown: str) -> list[dict[str, str]]:
    lines = [line.strip() for line in markdown.splitlines() if line.strip().startswith("|")]
    if len(lines) < 3:
        return []

    headers = [cell.strip() for cell in lines[0].strip("|").split("|")]
    rows: list[dict[str, str]] = []
    for line in lines[2:]:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != len(headers):
            continue
        rows.append(dict(zip(headers, cells, strict=True)))
    return rows


def extract_subsections(markdown: str) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    current_title: str | None = None
    current_lines: list[str] = []

    for line in markdown.splitlines():
        if line.startswith("### "):
            if current_title:
                items.append({"title": current_title, "content": "\n".join(current_lines).strip()})
            current_title = re.sub(r"^\d+(?:\.\d+)*[.、]?\s*", "", line[4:].strip())
            current_lines = []
            continue
        if current_title:
            current_lines.append(line)

    if current_title:
        items.append({"title": current_title, "content": "\n".join(current_lines).strip()})

    if items:
        return items
    return [{"title": "内容", "content": markdown.strip()}] if markdown.strip() else []
