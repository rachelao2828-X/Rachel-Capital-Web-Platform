from pathlib import Path

from app.services.quarterly_tracking_loader import (
    load_ecosystem_quarterly_trackings,
    load_quarterly_tracking_overview,
)


def test_load_quarterly_tracking_overview(tmp_path: Path) -> None:
    tracking_dir = tmp_path / "02_战略生态" / "季度跟踪表"
    tracking_dir.mkdir(parents=True)
    (tracking_dir / "七大战略生态季度跟踪总览.md").write_text(
        """---
type: strategic_ecosystem_quarterly_tracking_overview
title: 七大战略生态季度跟踪总览
public: false
---

# 七大战略生态季度跟踪总览

## 1. 定位

季度跟踪定位内容。
""",
        encoding="utf-8",
    )

    overview = load_quarterly_tracking_overview(vault_path=str(tmp_path))

    assert overview["status"] == "已读取"
    assert overview["public"] is False
    assert overview["sections"]["定位"] == "季度跟踪定位内容。"


def test_load_ecosystem_quarterly_trackings(tmp_path: Path) -> None:
    tracking_dir = tmp_path / "02_战略生态" / "季度跟踪表"
    tracking_dir.mkdir(parents=True)
    (tracking_dir / "AI基础设施生态季度跟踪表.md").write_text(
        """---
type: strategic_ecosystem_quarterly_tracking
title: AI基础设施生态季度跟踪表
public: false
ecosystem: AI基础设施生态
---

# AI基础设施生态季度跟踪表

## 2. 当前季度

2026-Q2

## 4. 关键指标跟踪

| 指标 | 上季度 | 本季度 | 变化方向 | 重要性 | 备注 |
|---|---|---|---|---|---|
| AI算力需求变化 | 待补充 | 待补充 | 待判断 | 高 | 待补充 |

## 5. 公司池变化

| 公司 / 项目 | 所属环节 | 市场类型 | 本季度变化 | 研究状态 | 后续动作 |
|---|---|---|---|---|---|
| 待补充：AI服务器公司 | AI服务器 | 其他 | 待补充 | 待建档 | 待跟踪 |

## 6. 一级项目变化

| 项目 | 所属环节 | 本季度变化 | 当前状态 | 后续动作 |
|---|---|---|---|---|
| 待补充 | 待补充 | 待补充 | 待初筛 | 待跟踪 |

## 10. 风险变化

| 风险 | 本季度变化 | 风险等级 | 是否需要继续跟踪 |
|---|---|---|---|
| 算力利用率波动 | 待补充 | 中 | 是 |

## 11. 研究任务复盘

| 任务 | 状态 | 结果 | 下步动作 |
|---|---|---|---|
| 更新 AI基础设施公司池 | todo | 待补充 | 待跟踪 |

## 12. 下季度重点跟踪方向

- AI推理基础设施
- 国产算力替代
""",
        encoding="utf-8",
    )

    trackings = load_ecosystem_quarterly_trackings(vault_path=str(tmp_path))
    ai_tracking = trackings[0]

    assert ai_tracking["status"] == "已读取"
    assert ai_tracking["public"] is False
    assert ai_tracking["current_quarter"] == "2026-Q2"
    assert ai_tracking["key_indicators"][0]["指标"] == "AI算力需求变化"
    assert ai_tracking["company_changes"][0]["公司 / 项目"] == "待补充：AI服务器公司"
    assert ai_tracking["project_changes"][0]["当前状态"] == "待初筛"
    assert ai_tracking["risk_changes"][0]["风险"] == "算力利用率波动"
    assert ai_tracking["research_task_review"][0]["任务"] == "更新 AI基础设施公司池"
    assert ai_tracking["next_quarter_focus"] == ["AI推理基础设施", "国产算力替代"]
    assert trackings[1]["status"] == "待建设"
