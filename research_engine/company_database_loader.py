from __future__ import annotations

from collections import Counter
from pathlib import Path
import re
from typing import Any

from app.core.config import settings
from app.services.ecosystem_loader import first_heading, parse_bool, split_frontmatter
from app.services.valuation_engine.model_registry import ECOSYSTEM_OPTIONS


COMPANY_DATABASE_SOURCE_DIR = Path("03_公司数据库")

DIRECTORY_MARKET_TYPES = {
    "A股公司": "A股",
    "港股公司": "港股",
    "港股通公司": "港股通",
    "美股公司": "美股",
    "一级市场项目": "一级市场项目",
    "全球创新企业": "全球创新企业",
    "非上市公司": "非上市公司",
    "产业项目": "产业项目",
}

SUPPORTED_DIRECTORIES = list(DIRECTORY_MARKET_TYPES) + ["战略生态公司池"]

SKIP_NAME_KEYWORDS = (
    "README",
    "模板",
    "总览",
    "说明",
    "报告",
    "公司池",
    "季度跟踪",
)

ECOSYSTEM_NAMES = [name for name in ECOSYSTEM_OPTIONS if name not in {"中国关键技术攻关长期跟踪", "其他"}]

ECOSYSTEM_KEYWORDS = {
    "AI基础设施生态": [
        "AI基础设施",
        "算力",
        "GPU",
        "ASIC",
        "AI服务器",
        "光模块",
        "光器件",
        "交换机",
        "数据中心",
        "IDC",
        "液冷",
        "电力",
        "算力租赁",
        "云计算",
        "推理",
        "大模型基础设施",
    ],
    "半导体生态": [
        "半导体",
        "芯片",
        "晶圆",
        "封测",
        "设备",
        "材料",
        "EDA",
        "IP",
        "光刻胶",
        "电子特气",
        "CMP",
        "存储",
        "功率半导体",
        "先进封装",
        "传感器",
    ],
    "华为生态": [
        "华为",
        "昇腾",
        "鲲鹏",
        "鸿蒙",
        "HarmonyOS",
        "欧拉",
        "盘古",
        "华为云",
        "华为汽车",
        "智选车",
        "HI模式",
        "问界",
        "智界",
        "信创",
        "政企数字化",
        "5.5G",
        "5G-A",
    ],
    "机器人生态": [
        "机器人",
        "人形机器人",
        "工业机器人",
        "协作机器人",
        "AMR",
        "AGV",
        "减速器",
        "伺服",
        "控制器",
        "力传感器",
        "灵巧手",
        "具身智能",
        "VLA",
        "特种机器人",
        "机器视觉",
    ],
    "高端材料生态": [
        "高端材料",
        "新材料",
        "半导体材料",
        "电子特气",
        "光刻胶",
        "CMP",
        "靶材",
        "硅片",
        "碳纤维",
        "高温合金",
        "钛合金",
        "PEEK",
        "PI",
        "PPS",
        "导热材料",
        "液冷材料",
        "稀土永磁",
        "医用高分子",
        "资源回收",
        "氟化钙",
    ],
    "船舶与国防生态": [
        "船舶",
        "LNG船",
        "海工",
        "航空发动机",
        "燃气轮机",
        "军工电子",
        "雷达",
        "红外",
        "光电",
        "北斗",
        "卫星",
        "商业航天",
        "无人机",
        "无人船",
        "无人潜航器",
        "特种材料",
        "高端装备",
        "航空航天",
    ],
    "医疗科技生态": [
        "医疗科技",
        "医疗器械",
        "医学影像",
        "CT",
        "MRI",
        "PET",
        "超声",
        "内窥镜",
        "AI医疗",
        "创新药",
        "生命科学工具",
        "医疗信息化",
        "医疗机器人",
        "医用材料",
        "CRO",
        "CDMO",
        "生物科技",
        "医院数字化",
    ],
}


def company_database_root(vault_path: str | None = None) -> Path:
    vault = Path(vault_path or settings.obsidian_vault_path or "")
    return vault / COMPANY_DATABASE_SOURCE_DIR


def load_company_database(vault_path: str | None = None) -> list[dict[str, Any]]:
    root = company_database_root(vault_path)
    if not root.exists():
        return []

    cards: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*.md")):
        if should_skip_company_card(path):
            continue
        card = parse_company_card(str(path), vault_path=vault_path)
        if card["source_status"] != "解析失败":
            card["ecosystems"] = infer_company_ecosystems(card)
        cards.append(card)
    return cards


def load_company_cards_by_directory(vault_path: str | None, directory_name: str) -> list[dict[str, Any]]:
    directory = company_database_root(vault_path) / directory_name
    if not directory.exists():
        return []

    cards: list[dict[str, Any]] = []
    for path in sorted(directory.rglob("*.md")):
        if should_skip_company_card(path):
            continue
        card = parse_company_card(str(path), vault_path=vault_path)
        if card["source_status"] != "解析失败":
            card["ecosystems"] = infer_company_ecosystems(card)
        cards.append(card)
    return cards


def parse_company_card(markdown_path: str, vault_path: str | None = None) -> dict[str, Any]:
    path = Path(markdown_path)
    try:
        raw = path.read_text(encoding="utf-8")
        metadata, body = split_frontmatter(raw)
    except OSError:
        return empty_company_card(path, vault_path, "解析失败")

    title = first_text(metadata, ["title", "company_name", "name"]) or first_heading(body) or path.stem
    company_name = first_text(metadata, ["company_name", "name", "title"]) or title
    market_type = infer_market_type(path, metadata, vault_path)
    ticker = first_text(metadata, ["ticker", "code", "stock_code"]) or infer_ticker_from_text(str(company_name), path.stem)
    tags = as_list(metadata.get("tags"))
    rachel_ecosystem = explicit_ecosystem_values(metadata)
    summary = extract_summary(body)
    industry = first_text(metadata, ["industry", "sector"]) or ""
    segments = as_list(metadata.get("segments"))
    if not segments:
        segments = as_list(metadata.get("segment"))
    business = first_text(metadata, ["business"]) or ""
    core_business = first_text(metadata, ["core_business"]) or extract_core_business(body)
    research_status = first_text(metadata, ["research_status", "status"]) or "待完善"
    research_priority = first_text(metadata, ["research_priority"]) or ""
    valuation_status = first_text(metadata, ["valuation_status"]) or ""
    last_updated = first_text(metadata, ["updated", "last_updated"]) or ""

    return {
        "company_name": str(company_name),
        "display_name": str(title),
        "market_type": market_type,
        "ticker": ticker,
        "file_path": str(path),
        "relative_path": relative_to_vault(path, vault_path),
        "frontmatter": metadata,
        "summary": summary,
        "industry": industry,
        "segments": segments,
        "ecosystems": [],
        "rachel_ecosystem": rachel_ecosystem,
        "business": business,
        "core_business": core_business,
        "research_status": research_status,
        "research_priority": research_priority,
        "valuation_status": valuation_status,
        "last_updated": last_updated,
        "tags": tags,
        "public": parse_bool(metadata.get("public")),
        "source_status": "已建档" if metadata or summary else "待完善",
        "match_type": "",
        "match_reason": "",
        "raw_markdown": body.strip()[:2400],
    }


def infer_company_ecosystems(company_card: dict[str, Any]) -> list[str]:
    explicit_values = [value for value in as_list(company_card.get("rachel_ecosystem")) if value in ECOSYSTEM_NAMES]
    if explicit_values:
        company_card["match_type"] = "显式匹配"
        company_card["match_reason"] = "显式生态字段"
        return unique_values(explicit_values)

    text_parts = [
        company_card.get("company_name", ""),
        company_card.get("display_name", ""),
        company_card.get("market_type", ""),
        company_card.get("industry", ""),
        company_card.get("business", ""),
        company_card.get("core_business", ""),
        company_card.get("summary", ""),
        company_card.get("relative_path", ""),
        " ".join(as_list(company_card.get("tags"))),
        " ".join(as_list(company_card.get("segments"))),
        company_card.get("raw_markdown", ""),
    ]
    combined = "\n".join(str(part) for part in text_parts if part)
    matched: list[str] = []
    reasons: list[str] = []
    for ecosystem, keywords in ECOSYSTEM_KEYWORDS.items():
        hits = [keyword for keyword in keywords if keyword and keyword.lower() in combined.lower()]
        if hits:
            matched.append(ecosystem)
            reasons.append(f"{ecosystem}: {' / '.join(hits[:3])}")

    if matched:
        company_card["match_type"] = "关键词匹配"
        company_card["match_reason"] = "关键词匹配：" + "；".join(reasons)
        return unique_values(matched)

    company_card["match_type"] = "待人工确认"
    company_card["match_reason"] = "未识别到显式生态字段或关键词"
    return []


def match_company_to_ecosystem_pools(
    company_cards: list[dict[str, Any]], company_pools: list[dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    cards_by_name, cards_by_ticker = build_card_indexes(company_cards)
    unmatched_cards = [card for card in company_cards if not card.get("ecosystems")]
    results: dict[str, dict[str, Any]] = {}

    for pool in company_pools:
        ecosystem_name = str(pool.get("ecosystem") or "")
        if not ecosystem_name:
            continue
        matched_companies: list[dict[str, Any]] = []
        used_card_paths: set[str] = set()

        for pool_row in pool.get("companies") or []:
            card = find_matching_card(pool_row, cards_by_name, cards_by_ticker)
            if card:
                used_card_paths.add(str(card.get("file_path") or ""))
            matched_companies.append(build_matched_company(ecosystem_name, pool_row, card))

        for card in company_cards:
            if ecosystem_name not in as_list(card.get("ecosystems")):
                continue
            if str(card.get("file_path") or "") in used_card_paths:
                continue
            matched_companies.append(build_card_only_match(card))

        results[ecosystem_name] = {
            "ecosystem_name": ecosystem_name,
            "matched_companies": matched_companies,
            "unmatched_companies": unmatched_cards,
            "warnings": [],
        }

    return results


def build_company_database_linkage(
    vault_path: str | None, company_pools: list[dict[str, Any]]
) -> dict[str, Any]:
    root = company_database_root(vault_path)
    warnings = missing_directory_warnings(root)
    cards = load_company_database(vault_path)
    matches = match_company_to_ecosystem_pools(cards, company_pools)
    market_counts = Counter(str(card.get("market_type") or "其他") for card in cards)
    ecosystem_counts = Counter(
        ecosystem for card in cards for ecosystem in as_list(card.get("ecosystems")) if ecosystem in ECOSYSTEM_NAMES
    )
    unmatched = [card for card in cards if not card.get("ecosystems")]
    pending_confirmation = [
        row
        for match in matches.values()
        for row in match.get("matched_companies", [])
        if row.get("match_type") == "待人工确认" or row.get("ecosystem_relevance") == "待验证"
    ]
    return {
        "status": "已读取" if root.exists() else "待建设",
        "root_path": str(root),
        "company_cards": cards,
        "company_count": len(cards),
        "market_counts": dict(market_counts),
        "ecosystem_counts": dict(ecosystem_counts),
        "unmatched_companies": unmatched,
        "pending_confirmation": pending_confirmation,
        "matches": matches,
        "warnings": warnings,
    }


def market_statistics_rows(linkage: dict[str, Any]) -> list[dict[str, Any]]:
    cards = linkage.get("company_cards") or []
    rows: list[dict[str, Any]] = []
    for market_type in DIRECTORY_MARKET_TYPES.values():
        cards_for_market = [card for card in cards if card.get("market_type") == market_type]
        rows.append(
            {
                "市场类型": market_type,
                "读取数量": len(cards_for_market),
                "已匹配生态数量": sum(1 for card in cards_for_market if card.get("ecosystems")),
                "待人工确认数量": sum(1 for card in cards_for_market if not card.get("ecosystems")),
                "备注": "待建设" if len(cards_for_market) == 0 else "",
            }
        )
    return rows


def ecosystem_statistics_rows(linkage: dict[str, Any]) -> list[dict[str, Any]]:
    matches = linkage.get("matches") or {}
    rows: list[dict[str, Any]] = []
    for ecosystem in ECOSYSTEM_NAMES:
        companies = list((matches.get(ecosystem) or {}).get("matched_companies") or [])
        rows.append(
            {
                "战略生态": ecosystem,
                "匹配公司 / 项目数量": len(companies),
                "核心受益": sum(1 for item in companies if item.get("ecosystem_relevance") == "核心受益"),
                "强相关": sum(1 for item in companies if item.get("ecosystem_relevance") == "强相关"),
                "待验证": sum(
                    1
                    for item in companies
                    if item.get("ecosystem_relevance") == "待验证" or item.get("match_type") == "待人工确认"
                ),
                "备注": "含公司池待建档条目" if companies else "待建设",
            }
        )
    return rows


def should_skip_company_card(path: Path) -> bool:
    if path.name.startswith(".") or path.suffix.lower() != ".md":
        return True
    stem = path.stem
    return any(keyword in stem for keyword in SKIP_NAME_KEYWORDS)


def empty_company_card(path: Path, vault_path: str | None, status: str) -> dict[str, Any]:
    return {
        "company_name": path.stem,
        "display_name": path.stem,
        "market_type": infer_market_type(path, {}, vault_path),
        "ticker": "",
        "file_path": str(path),
        "relative_path": relative_to_vault(path, vault_path),
        "frontmatter": {},
        "summary": "",
        "industry": "",
        "segments": [],
        "ecosystems": [],
        "rachel_ecosystem": [],
        "business": "",
        "core_business": "",
        "research_status": "",
        "research_priority": "",
        "valuation_status": "",
        "last_updated": "",
        "tags": [],
        "source_status": status,
        "raw_markdown": "",
    }


def infer_market_type(path: Path, metadata: dict[str, Any], vault_path: str | None) -> str:
    explicit = first_text(metadata, ["market_type", "market"])
    if explicit:
        return str(explicit)

    parts = path.parts
    for directory, market_type in DIRECTORY_MARKET_TYPES.items():
        if directory in parts:
            return market_type
    return "其他"


def relative_to_vault(path: Path, vault_path: str | None) -> str:
    vault = Path(vault_path or settings.obsidian_vault_path or "")
    try:
        return str(path.relative_to(vault))
    except ValueError:
        return str(path)


def first_text(metadata: dict[str, Any], keys: list[str]) -> str:
    for key in keys:
        value = metadata.get(key)
        if isinstance(value, list):
            return str(value[0]) if value else ""
        if value not in (None, ""):
            return str(value)
    return ""


def as_list(value: Any) -> list[str]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, tuple | set):
        return [str(item) for item in value if str(item).strip()]
    text = str(value)
    if "," in text:
        return [part.strip() for part in text.split(",") if part.strip()]
    if "，" in text:
        return [part.strip() for part in text.split("，") if part.strip()]
    return [text.strip()] if text.strip() else []


def explicit_ecosystem_values(metadata: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for key in ["ecosystem", "rachel_ecosystem", "linked_ecosystem"]:
        values.extend(as_list(metadata.get(key)))
    values.extend(value for value in as_list(metadata.get("tags")) if value in ECOSYSTEM_NAMES)
    return unique_values(values)


def unique_values(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def infer_ticker_from_text(company_name: str, file_stem: str) -> str:
    text = f"{company_name} {file_stem}"
    match = re.search(r"(?<!\d)(\d{5,6})(?!\d)", text)
    if match:
        return match.group(1)
    match = re.search(r"\b([A-Z]{1,5})\b", text)
    return match.group(1) if match else ""


def extract_summary(body: str) -> str:
    lines: list[str] = []
    for raw_line in body.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith("|") or line.startswith("---"):
            continue
        if line.startswith("- "):
            line = line[2:].strip()
        lines.append(line)
        if len("".join(lines)) > 320:
            break
    return "\n".join(lines)[:500]


def extract_core_business(body: str) -> str:
    for raw_line in body.splitlines():
        line = raw_line.strip()
        if "核心业务" in line and "|" not in line:
            return line.split("：", 1)[-1].strip()
    return ""


def build_card_indexes(company_cards: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    by_name: dict[str, dict[str, Any]] = {}
    by_ticker: dict[str, dict[str, Any]] = {}
    for card in company_cards:
        for value in [card.get("company_name"), card.get("display_name")]:
            key = normalize_match_key(str(value or ""))
            if key:
                by_name[key] = card
        ticker = normalize_ticker(str(card.get("ticker") or ""))
        if ticker:
            by_ticker[ticker] = card
    return by_name, by_ticker


def find_matching_card(
    pool_row: dict[str, Any],
    cards_by_name: dict[str, dict[str, Any]],
    cards_by_ticker: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    name_key = normalize_match_key(str(pool_row.get("name") or ""))
    ticker_key = normalize_ticker(str(pool_row.get("ticker_or_id") or ""))
    return cards_by_name.get(name_key) or cards_by_ticker.get(ticker_key)


def build_matched_company(
    ecosystem_name: str, pool_row: dict[str, Any], card: dict[str, Any] | None
) -> dict[str, Any]:
    if card:
        linked_file = str(card.get("relative_path") or card.get("file_path") or "")
        return {
            "company_name": card.get("company_name") or pool_row.get("name") or "",
            "market_type": card.get("market_type") or pool_row.get("market_type") or "",
            "ticker": card.get("ticker") or pool_row.get("ticker_or_id") or "",
            "file_path": card.get("file_path") or "",
            "relative_path": card.get("relative_path") or "",
            "segment": pool_row.get("segment") or "待补充",
            "core_business": card.get("core_business") or pool_row.get("core_business") or "",
            "ecosystem_relevance": pool_row.get("ecosystem_relevance") or "待验证",
            "research_priority": card.get("research_priority") or pool_row.get("research_priority") or "",
            "research_status": card.get("research_status") or pool_row.get("research_status") or "",
            "match_type": "公司池反向匹配",
            "match_reason": f"公司池条目匹配到公司数据库卡片：{linked_file}",
            "linked_file": linked_file,
            "source_status": card.get("source_status") or "已建档",
            "summary": card.get("summary") or "",
            "raw_markdown": card.get("raw_markdown") or "",
            "company_card": card,
        }
    return {
        "company_name": pool_row.get("name") or "",
        "market_type": pool_row.get("market_type") or "",
        "ticker": pool_row.get("ticker_or_id") or "",
        "file_path": "",
        "relative_path": "",
        "segment": pool_row.get("segment") or "",
        "core_business": pool_row.get("core_business") or "",
        "ecosystem_relevance": pool_row.get("ecosystem_relevance") or "待验证",
        "research_priority": pool_row.get("research_priority") or "",
        "research_status": pool_row.get("research_status") or "待建档",
        "match_type": "待人工确认" if pool_row.get("ecosystem_relevance") == "待验证" else "公司池反向匹配",
        "match_reason": f"来自{ecosystem_name}公司池；公司数据库卡片待补充",
        "linked_file": pool_row.get("linked_file") if pool_row.get("linked_file") != "待补充" else "",
        "source_status": "待建档",
        "summary": pool_row.get("core_business") or "",
        "raw_markdown": "",
        "company_card": None,
    }


def build_card_only_match(card: dict[str, Any]) -> dict[str, Any]:
    return {
        "company_name": card.get("company_name") or "",
        "market_type": card.get("market_type") or "",
        "ticker": card.get("ticker") or "",
        "file_path": card.get("file_path") or "",
        "relative_path": card.get("relative_path") or "",
        "segment": "待补充",
        "core_business": card.get("core_business") or "",
        "ecosystem_relevance": "待验证",
        "research_priority": card.get("research_priority") or "",
        "research_status": card.get("research_status") or "",
        "match_type": card.get("match_type") or "关键词匹配",
        "match_reason": card.get("match_reason") or "",
        "linked_file": card.get("relative_path") or "",
        "source_status": card.get("source_status") or "已建档",
        "summary": card.get("summary") or "",
        "raw_markdown": card.get("raw_markdown") or "",
        "company_card": card,
    }


def normalize_match_key(value: str) -> str:
    return re.sub(r"[\s\[\]（）()/-]+", "", value).lower()


def normalize_ticker(value: str) -> str:
    cleaned = value.strip().upper()
    if "/" in cleaned:
        cleaned = cleaned.split("/", 1)[0].strip()
    return cleaned


def missing_directory_warnings(root: Path) -> list[str]:
    if not root.exists():
        return [f"公司数据库目录不存在：{root}"]
    warnings: list[str] = []
    for directory in SUPPORTED_DIRECTORIES:
        if not (root / directory).exists():
            warnings.append(f"目录待建设：{COMPANY_DATABASE_SOURCE_DIR / directory}")
    return warnings
