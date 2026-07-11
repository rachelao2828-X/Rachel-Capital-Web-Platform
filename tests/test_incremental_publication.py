from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]


def daily_markdown(report_date: str) -> str:
    section = "完整日报正文" * 120
    return f"""---
public: true
type: daily_intelligence
title: {report_date} 科技动向日报
date: {report_date}
summary: 当日完整摘要
source: coze
---

# {report_date} 科技动向日报

## 全球市场

{section}

## 科技产业

{section}

## 投资观察

{section}
"""


def test_daily_incremental_export_preserves_other_content(tmp_path: Path) -> None:
    report_date = "2026-07-11"
    vault = tmp_path / "vault"
    site = tmp_path / "public_site"
    source = (
        vault
        / "31_Inbox"
        / "Daily_Intelligence"
        / "2026"
        / "2026-07"
        / f"{report_date}_科技动向日报.md"
    )
    source.parent.mkdir(parents=True)
    source.write_text(daily_markdown(report_date), encoding="utf-8")

    data_dir = site / "data"
    data_dir.mkdir(parents=True)
    existing_items = [
        {
            "type": "report",
            "title": "保留的研究报告",
            "path": "reports/keep.md",
        },
        {
            "type": "daily_intelligence",
            "title": "2026-07-10 科技动向日报",
            "date": "2026-07-10",
            "path": "daily/2026/2026-07/2026-07-10_科技动向日报.md",
        },
        {
            "type": "market_radar",
            "title": "保留的市场复盘",
            "date": "2026-07-10",
            "path": "market-radar/keep.md",
        },
    ]
    (data_dir / "public_content.json").write_text(
        json.dumps({"items": existing_items}, ensure_ascii=False), encoding="utf-8"
    )

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts/export_daily_intelligence_incremental.py"),
            "--vault",
            str(vault),
            "--site-root",
            str(site),
            "--report-date",
            report_date,
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads((data_dir / "public_content.json").read_text(encoding="utf-8"))
    titles = {item["title"] for item in payload["items"]}
    assert "保留的研究报告" in titles
    assert "保留的市场复盘" in titles
    assert "2026-07-10 科技动向日报" in titles
    assert f"{report_date} 科技动向日报" in titles
    assert len(payload["items"]) == 4

    exported = site / "daily/2026/2026-07" / f"{report_date}_科技动向日报.md"
    assert exported.exists()
    assert "投资观察" in exported.read_text(encoding="utf-8")


def test_daily_source_quality_rejects_truncated_report(tmp_path: Path) -> None:
    report_date = "2026-07-11"
    source = (
        tmp_path
        / "31_Inbox"
        / "Daily_Intelligence"
        / "2026"
        / "2026-07"
        / f"{report_date}_科技动向日报.md"
    )
    source.parent.mkdir(parents=True)
    source.write_text(
        f"""---
public: true
type: daily_intelligence
title: {report_date} 科技动向日报
date: {report_date}
---

# {report_date} 科技动向日报

## 摘要

只有摘要，没有完整正文。
""",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts/check_daily_source_quality.py"),
            "--vault",
            str(tmp_path),
            "--report-date",
            report_date,
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "body is incomplete" in result.stdout
