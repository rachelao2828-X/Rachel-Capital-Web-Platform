from pathlib import Path

from app.services.ecosystem_loader import load_ecosystem, load_ecosystem_cross_map


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

## 核心公司观察池

公司池内容。

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
    assert document.sections["代表公司 / 项目类型"] == "公司池内容。"
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


def test_load_medical_technology_ecosystem_sections(tmp_path: Path) -> None:
    ecosystem_dir = tmp_path / "02_战略生态"
    ecosystem_dir.mkdir()
    (ecosystem_dir / "医疗科技生态.md").write_text(
        """---
id: ECO-MEDTECH-001
type: ecosystem
title: 医疗科技生态
public: false
tags:
  - 战略生态
---

# 医疗科技生态

## 1. 生态定位

医疗科技生态定位内容。

## 2. 核心逻辑

核心逻辑内容。

## 3. 产业链结构

产业链结构内容。

## 4. 关键环节

关键环节内容。

## 5. 关键技术

关键技术内容。

## 7. 主要瓶颈与风险

风险内容。

## 11. 与其他战略生态的关系

关系内容。
""",
        encoding="utf-8",
    )

    document = load_ecosystem("医疗科技生态", vault_path=str(tmp_path))

    assert document.exists is True
    assert document.status == "已读取"
    assert document.public is False
    assert document.sections["生态定位"] == "医疗科技生态定位内容。"
    assert document.sections["核心逻辑"] == "核心逻辑内容。"
    assert document.sections["产业链结构"] == "产业链结构内容。"
    assert document.sections["关键环节"] == "关键环节内容。"
    assert document.sections["关键技术"] == "关键技术内容。"
    assert document.sections["主要瓶颈与风险"] == "风险内容。"
    assert document.sections["与其他生态关系"] == "关系内容。"


def test_load_ecosystem_cross_map(tmp_path: Path) -> None:
    ecosystem_dir = tmp_path / "02_战略生态"
    ecosystem_dir.mkdir()
    (ecosystem_dir / "七大战略生态交叉关系图谱.md").write_text(
        """---
id: ECO-CROSS-MAP-001
type: ecosystem_cross_map
title: 七大战略生态交叉关系图谱
public: false
---

# 七大战略生态交叉关系图谱

## 1. 核心定位

七大战略生态关系说明。

## 3. 生态交叉矩阵

| 生态A | 生态B | 交叉关系 | 核心连接点 | 研究价值 | 跟踪优先级 |
|---|---|---|---|---|---|
| AI基础设施生态 | 半导体生态 | 算力需求拉动芯片升级 | GPU | 观察产业传导 | 高 |

## 4. 高优先级交叉主题

### 4.1 AI算力国产替代

主题内容。

## 5. 交叉关系跟踪指标

### 5.1 技术传导指标

- 指标内容
""",
        encoding="utf-8",
    )

    cross_map = load_ecosystem_cross_map(vault_path=str(tmp_path))

    assert cross_map["status"] == "已读取"
    assert cross_map["public"] is False
    assert cross_map["summary"] == "七大战略生态关系说明。"
    assert cross_map["cross_matrix"] == [
        {
            "生态A": "AI基础设施生态",
            "生态B": "半导体生态",
            "交叉关系": "算力需求拉动芯片升级",
            "核心连接点": "GPU",
            "研究价值": "观察产业传导",
            "跟踪优先级": "高",
        }
    ]
    assert cross_map["priority_themes"][0]["title"] == "AI算力国产替代"
    assert cross_map["tracking_indicators"][0]["title"] == "技术传导指标"
