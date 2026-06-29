from pathlib import Path

from app.services.ecosystem_loader import load_ecosystem


def test_load_huawei_ecosystem_sections(tmp_path: Path) -> None:
    ecosystem_dir = tmp_path / "02_战略生态"
    ecosystem_dir.mkdir()
    (ecosystem_dir / "华为生态.md").write_text(
        """---
id: ECO-HUAWEI-001
type: ecosystem
title: 华为生态
public: false
tags:
  - 战略生态
---

# 华为生态

## 1. 生态定位

华为生态定位内容。

## 2. 核心逻辑

核心逻辑内容。

## 11. 与其他战略生态的关系

关系内容。
""",
        encoding="utf-8",
    )

    document = load_ecosystem("华为生态", vault_path=str(tmp_path))

    assert document.exists is True
    assert document.status == "已读取"
    assert document.public is False
    assert document.sections["生态定位"] == "华为生态定位内容。"
    assert document.sections["核心逻辑"] == "核心逻辑内容。"
    assert document.sections["与其他生态关系"] == "关系内容。"


def test_load_robotics_ecosystem_sections(tmp_path: Path) -> None:
    ecosystem_dir = tmp_path / "02_战略生态"
    ecosystem_dir.mkdir()
    (ecosystem_dir / "机器人生态.md").write_text(
        """---
id: ECO-ROBOTICS-001
type: ecosystem
title: 机器人生态
public: false
tags:
  - 战略生态
---

# 机器人生态

## 1. 生态定位

机器人生态定位内容。

## 4. 关键环节

关键环节内容。

## 7. 主要瓶颈与风险

风险内容。

## 10. 研究任务

研究任务内容。
""",
        encoding="utf-8",
    )

    document = load_ecosystem("机器人生态", vault_path=str(tmp_path))

    assert document.exists is True
    assert document.status == "已读取"
    assert document.public is False
    assert document.sections["生态定位"] == "机器人生态定位内容。"
    assert document.sections["关键环节"] == "关键环节内容。"
    assert document.sections["主要瓶颈与风险"] == "风险内容。"
    assert document.sections["研究任务"] == "研究任务内容。"


def test_load_high_end_materials_ecosystem_sections(tmp_path: Path) -> None:
    ecosystem_dir = tmp_path / "02_战略生态"
    ecosystem_dir.mkdir()
    (ecosystem_dir / "高端材料生态.md").write_text(
        """---
id: ECO-ADV-MATERIALS-001
type: ecosystem
title: 高端材料生态
public: false
tags:
  - 战略生态
---

# 高端材料生态

## 1. 生态定位

高端材料生态定位内容。

## 3. 产业链结构

产业链结构内容。

## 5. 关键技术

关键技术内容。

## 7. 主要瓶颈与风险

风险内容。

## 11. 与其他战略生态的关系

关系内容。
""",
        encoding="utf-8",
    )

    document = load_ecosystem("高端材料生态", vault_path=str(tmp_path))

    assert document.exists is True
    assert document.status == "已读取"
    assert document.public is False
    assert document.sections["生态定位"] == "高端材料生态定位内容。"
    assert document.sections["产业链结构"] == "产业链结构内容。"
    assert document.sections["关键技术"] == "关键技术内容。"
    assert document.sections["主要瓶颈与风险"] == "风险内容。"
    assert document.sections["与其他生态关系"] == "关系内容。"


def test_load_shipbuilding_and_defense_ecosystem_sections(tmp_path: Path) -> None:
    ecosystem_dir = tmp_path / "02_战略生态"
    ecosystem_dir.mkdir()
    (ecosystem_dir / "船舶与国防生态.md").write_text(
        """---
id: ECO-SHIP-DEFENSE-001
type: ecosystem
title: 船舶与国防生态
public: false
tags:
  - 战略生态
---

# 船舶与国防生态

## 1. 生态定位

船舶与国防生态定位内容。

## 2. 核心逻辑

核心逻辑内容。

## 3. 产业链结构

产业链结构内容。

## 4. 关键环节

关键环节内容。

## 9. 跟踪指标

跟踪指标内容。

## 10. 研究任务

研究任务内容。
""",
        encoding="utf-8",
    )

    document = load_ecosystem("船舶与国防生态", vault_path=str(tmp_path))

    assert document.exists is True
    assert document.status == "已读取"
    assert document.public is False
    assert document.sections["生态定位"] == "船舶与国防生态定位内容。"
    assert document.sections["核心逻辑"] == "核心逻辑内容。"
    assert document.sections["产业链结构"] == "产业链结构内容。"
    assert document.sections["关键环节"] == "关键环节内容。"
    assert document.sections["跟踪指标"] == "跟踪指标内容。"
    assert document.sections["研究任务"] == "研究任务内容。"
