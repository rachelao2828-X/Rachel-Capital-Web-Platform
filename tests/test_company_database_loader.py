from pathlib import Path

from research_engine.company_database_loader import (
    build_company_database_linkage,
    infer_company_ecosystems,
    load_company_cards_by_directory,
    load_company_database,
    match_company_to_ecosystem_pools,
    parse_company_card,
)


def test_parse_company_card_and_infer_ecosystem(tmp_path: Path) -> None:
    company_dir = tmp_path / "03_公司数据库" / "A股公司"
    company_dir.mkdir(parents=True)
    company_path = company_dir / "光模块公司.md"
    company_path.write_text(
        """---
title: 光模块公司
market_type: A股
ticker: 300001
industry: 光通信
research_status: 跟踪中
research_priority: 高
public: false
tags:
  - AI基础设施生态
---

# 光模块公司

核心业务：高速光模块、数据中心互联和AI服务器配套。
""",
        encoding="utf-8",
    )

    card = parse_company_card(str(company_path), vault_path=str(tmp_path))
    ecosystems = infer_company_ecosystems(card)

    assert card["company_name"] == "光模块公司"
    assert card["market_type"] == "A股"
    assert card["ticker"] == "300001"
    assert card["public"] is False
    assert ecosystems == ["AI基础设施生态"]


def test_load_company_database_skips_non_company_files(tmp_path: Path) -> None:
    pool_dir = tmp_path / "03_公司数据库" / "战略生态公司池"
    pool_dir.mkdir(parents=True)
    (pool_dir / "七大战略生态公司池总览.md").write_text("# 总览\n", encoding="utf-8")
    (pool_dir / "AI基础设施生态公司池.md").write_text("# 公司池\n", encoding="utf-8")

    company_dir = tmp_path / "03_公司数据库" / "美股公司"
    company_dir.mkdir(parents=True)
    (company_dir / "NVIDIA.md").write_text(
        """---
title: NVIDIA
market_type: 美股
ticker: NVDA
---

# NVIDIA

GPU、AI算力和数据中心加速计算平台。
""",
        encoding="utf-8",
    )

    cards = load_company_database(vault_path=str(tmp_path))
    missing = load_company_cards_by_directory(str(tmp_path), "港股公司")

    assert len(cards) == 1
    assert cards[0]["company_name"] == "NVIDIA"
    assert "AI基础设施生态" in cards[0]["ecosystems"]
    assert missing == []


def test_match_company_to_ecosystem_pools_links_cards(tmp_path: Path) -> None:
    company_dir = tmp_path / "03_公司数据库" / "A股公司"
    company_dir.mkdir(parents=True)
    company_path = company_dir / "机器人公司.md"
    company_path.write_text(
        """---
title: 机器人公司
market_type: A股
ticker: 300024
linked_ecosystem:
  - 机器人生态
---

# 机器人公司

工业机器人和自动化系统。
""",
        encoding="utf-8",
    )
    cards = load_company_database(vault_path=str(tmp_path))
    pools = [
        {
            "ecosystem": "机器人生态",
            "companies": [
                {
                    "name": "机器人公司",
                    "market_type": "A股",
                    "ticker_or_id": "300024",
                    "segment": "工业机器人",
                    "core_business": "工业机器人",
                    "ecosystem_relevance": "强相关",
                    "research_priority": "高",
                    "research_status": "待建档",
                    "linked_file": "待补充",
                }
            ],
        }
    ]

    matches = match_company_to_ecosystem_pools(cards, pools)
    linked = matches["机器人生态"]["matched_companies"][0]

    assert linked["match_type"] == "公司池反向匹配"
    assert linked["source_status"] == "已建档"
    assert linked["linked_file"] == "03_公司数据库/A股公司/机器人公司.md"


def test_build_company_database_linkage_handles_missing_directories(tmp_path: Path) -> None:
    (tmp_path / "03_公司数据库").mkdir()
    linkage = build_company_database_linkage(str(tmp_path), [{"ecosystem": "AI基础设施生态", "companies": []}])

    assert linkage["status"] == "已读取"
    assert linkage["company_count"] == 0
    assert any("A股公司" in warning for warning in linkage["warnings"])
