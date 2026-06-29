from pathlib import Path

from app.services.company_pool_loader import load_company_pool_overview, load_ecosystem_company_pools


def test_load_company_pool_overview(tmp_path: Path) -> None:
    pool_dir = tmp_path / "03_公司数据库" / "战略生态公司池"
    pool_dir.mkdir(parents=True)
    (pool_dir / "七大战略生态公司池总览.md").write_text(
        """---
type: strategic_ecosystem_company_pool_overview
title: 七大战略生态公司池总览
public: false
---

# 七大战略生态公司池总览

## 1. 定位

公司池定位内容。
""",
        encoding="utf-8",
    )

    overview = load_company_pool_overview(vault_path=str(tmp_path))

    assert overview["status"] == "已读取"
    assert overview["public"] is False
    assert overview["sections"]["定位"] == "公司池定位内容。"


def test_load_ecosystem_company_pools(tmp_path: Path) -> None:
    pool_dir = tmp_path / "03_公司数据库" / "战略生态公司池"
    pool_dir.mkdir(parents=True)
    (pool_dir / "AI基础设施生态公司池.md").write_text(
        """---
type: strategic_ecosystem_company_pool
title: AI基础设施生态公司池
public: false
ecosystem: AI基础设施生态
---

# AI基础设施生态公司池

## 2. 公司池表格

| 公司 / 项目 | 市场类型 | 代码 / 编号 | 细分环节 | 核心业务 | 生态相关性 | 研究优先级 | 当前研究状态 | 关联文件 | 备注 |
|---|---|---|---|---|---|---|---|---|---|
| 待补充：AI服务器公司 | 其他 | 待补充 | AI服务器 | AI训练与推理服务器 | 核心受益 | 高 | 待建档 | 待补充 | 关注订单 |

## 3. 细分环节分类

- AI芯片
- AI服务器

## 4. 高优先级跟踪对象

- AI服务器公司

## 5. 待补充清单

- A股公司

## 6. 与其他生态交叉

[[七大战略生态交叉关系图谱]]

## 7. 后续研究任务

- 建立公司卡片。
""",
        encoding="utf-8",
    )

    pools = load_ecosystem_company_pools(vault_path=str(tmp_path))
    ai_pool = pools[0]

    assert ai_pool["status"] == "已读取"
    assert ai_pool["public"] is False
    assert ai_pool["companies"][0]["name"] == "待补充：AI服务器公司"
    assert ai_pool["companies"][0]["segment"] == "AI服务器"
    assert ai_pool["segments"] == ["AI芯片", "AI服务器"]
    assert ai_pool["priority_targets"] == ["AI服务器公司"]
    assert ai_pool["to_fill"] == ["A股公司"]
    assert ai_pool["cross_links"] == ["七大战略生态交叉关系图谱"]
    assert ai_pool["tasks"] == ["建立公司卡片。"]
    assert pools[1]["status"] == "待建设"
