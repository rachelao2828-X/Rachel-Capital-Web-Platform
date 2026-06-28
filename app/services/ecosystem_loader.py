from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from app.core.config import settings
from app.services.valuation_engine.model_registry import ECOSYSTEM_OPTIONS


ECOSYSTEM_SOURCE_DIR = "02_战略生态"
SECTION_ALIASES = {
    "生态定位": ["生态定位", "生态定义"],
    "核心逻辑": ["核心逻辑"],
    "产业链结构": ["产业链结构"],
    "关键环节": ["关键环节"],
    "关键技术": ["关键技术"],
    "代表公司 / 项目类型": ["代表公司 / 项目类型", "代表公司", "关键公司观察池"],
    "主要瓶颈与风险": ["主要瓶颈与风险", "风险因素"],
    "跟踪优先级": ["跟踪优先级"],
    "跟踪指标": ["跟踪指标", "长期跟踪指标"],
    "研究任务": ["研究任务", "下一步研究任务"],
    "与其他生态关系": ["与其他战略生态的关系", "与其他生态的关系"],
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
