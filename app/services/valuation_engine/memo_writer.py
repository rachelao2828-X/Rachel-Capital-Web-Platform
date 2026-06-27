from __future__ import annotations

from datetime import date
from pathlib import Path
import re

from app.services.valuation_engine.listed import ListedCompanyProfile, ListedValuationResult
from app.services.valuation_engine.private_market import PrivateMarketProfile, PrivateMarketValuationResult


def write_listed_memo(
    profile: ListedCompanyProfile,
    result: ListedValuationResult,
    vault_path: str | Path,
    created: date | None = None,
) -> Path:
    created = created or date.today()
    output_dir = Path(vault_path).expanduser() / "15_估值引擎" / "估值历史" / "已上市公司"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{safe_filename(profile.stock_name)}_{created.isoformat()}_已上市公司估值框架.md"
    output_path.write_text(listed_markdown(profile, result, created), encoding="utf-8")
    return output_path


def write_private_market_memo(
    profile: PrivateMarketProfile,
    result: PrivateMarketValuationResult,
    vault_path: str | Path,
    created: date | None = None,
) -> Path:
    created = created or date.today()
    output_dir = Path(vault_path).expanduser() / "15_估值引擎" / "估值历史" / "未上市一级市场"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{safe_filename(profile.target_name)}_{created.isoformat()}_未上市一级市场估值框架.md"
    output_path.write_text(private_markdown(profile, result, created), encoding="utf-8")
    return output_path


def listed_markdown(profile: ListedCompanyProfile, result: ListedValuationResult, created: date) -> str:
    return f"""---
type: listed_company_valuation
title: {profile.stock_name}已上市公司估值框架
status: draft
public: false
created: {created.isoformat()}
target_name: {profile.stock_name}
ticker: {profile.ticker}
market: {profile.market}
target_type: 已上市公司
linked_ecosystem:
  - {profile.ecosystem}
tags:
  - 估值引擎
  - 已上市公司估值
---

# {profile.stock_name}已上市公司估值框架

## 1. 标的基本信息

- 股票名称：{profile.stock_name}
- 股票代码：{profile.ticker}
- 市场：{profile.market}
- 所属行业：{profile.industry}
- 所属生态：{profile.ecosystem}

## 2. 公司画像识别

{bullet_list(result.portrait)}

研究动作建议：{result.research_action}

## 3. 推荐估值模型

主模型：

{bullet_list(result.primary_models)}

辅助模型：

{bullet_list(result.auxiliary_models) if result.auxiliary_models else "- 无"}

参考模型：

{bullet_list(result.reference_models) if result.reference_models else "- 无"}

不建议使用：

{bullet_list(result.unsuitable_models) if result.unsuitable_models else "- 无"}

## 4. 多模型适用性对比

{markdown_table(result.comparison_table, ["模型", "适用度", "适用原因", "需要的数据", "输出结果", "权重建议"])}

## 5. 需要补充的数据

{bullet_list(result.data_requirements)}

## 6. 初步估值思路

{bullet_list(result.valuation_framework)}

## 7. 风险与不确定性

{bullet_list(result.risks)}

## 8. 后续研究任务

- 补齐财务和经营数据。
- 建立同业和历史估值分位表。
- 建立乐观、中性、保守三种情景。
- 将估值框架与公司卡片和战略生态双链。

## 9. 免责声明

本文件仅用于 Rachel Capital OS 内部研究，不构成任何投资建议、投资邀约或买卖依据。
"""


def private_markdown(profile: PrivateMarketProfile, result: PrivateMarketValuationResult, created: date) -> str:
    secondary = "\n".join(f"  - {item}" for item in result.classification.secondary_types) or "  - 无"
    return f"""---
type: private_market_valuation
title: {profile.target_name}未上市一级市场估值框架
status: draft
public: false
created: {created.isoformat()}
target_name: {profile.target_name}
target_type: {result.classification.primary_type}
secondary_type:
{secondary}
linked_ecosystem:
  - {profile.ecosystem}
tags:
  - 估值引擎
  - 未上市估值
  - 一级市场估值
---

# {profile.target_name}未上市 / 一级市场估值框架

## 1. 标的基本信息

- 标的名称：{profile.target_name}
- 所属行业：{profile.industry}
- 所属生态：{profile.ecosystem}
- 退出路径：{profile.exit_path}

## 2. 主分类与辅助分类

- 主分类：{result.classification.primary_type}
- 辅助分类：{", ".join(result.classification.secondary_types) if result.classification.secondary_types else "无"}

## 3. 判断理由

{bullet_list(result.classification.reasons)}

研究动作建议：{result.research_action}

## 4. 推荐估值模型

主模型：

{bullet_list(result.primary_models)}

辅助模型：

{bullet_list(result.auxiliary_models) if result.auxiliary_models else "- 无"}

参考模型：

{bullet_list(result.reference_models) if result.reference_models else "- 无"}

不建议使用：

{bullet_list(result.unsuitable_models) if result.unsuitable_models else "- 无"}

## 5. 多模型适用性对比

{markdown_table(result.comparison_table, ["模型", "适用度", "适用原因", "必需数据", "输出结果", "权重建议"])}

## 6. 必须考虑的折扣或敏感性因素

{bullet_list(result.required_adjustments) if result.required_adjustments else "- 暂无，待补充交易和项目数据后确认。"}

## 7. 需要补充的数据

{bullet_list(result.data_requirements)}

## 8. 初步估值思路

{bullet_list(result.valuation_framework)}

## 9. 风险与不确定性

{bullet_list(result.risks)}

## 10. 后续研究任务

- 补齐交易、项目、资产和财务数据。
- 建立可比融资交易和可比上市公司样本。
- 明确折扣、敏感性和退出路径假设。
- 将估值框架与 Obsidian 主题、公司和项目文件双链。

## 11. 免责声明

本文件仅用于 Rachel Capital OS 内部研究，不构成任何投资建议、投资邀约或买卖依据。
"""


def bullet_list(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def markdown_table(rows: list[dict[str, str]], columns: list[str]) -> str:
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(escape(row.get(column, "")) for column in columns) + " |")
    return "\n".join(lines)


def escape(value: str) -> str:
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def safe_filename(name: str) -> str:
    cleaned = re.sub(r"[\\/:*?\"<>|]+", "_", name).strip()
    return cleaned or "未命名标的"
