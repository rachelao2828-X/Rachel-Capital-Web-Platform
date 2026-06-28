from __future__ import annotations

from datetime import date
from pathlib import Path
import re
from typing import Any

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


def write_private_market_document_analysis(
    extraction: dict[str, Any],
    parsed_document: dict[str, Any],
    vault_path: str | Path,
    created: date | None = None,
) -> Path:
    created = created or date.today()
    project_name = project_name_from_extraction(extraction)
    output_dir = Path(vault_path).expanduser() / "15_估值引擎" / "一级市场项目资料解析"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{safe_filename(project_name)}_{created.isoformat()}_项目资料解析.md"
    output_path.write_text(private_document_analysis_markdown(extraction, parsed_document, created), encoding="utf-8")
    return output_path


def write_private_market_document_valuation_framework(
    extraction: dict[str, Any],
    parsed_document: dict[str, Any],
    vault_path: str | Path,
    created: date | None = None,
) -> Path:
    created = created or date.today()
    project_name = project_name_from_extraction(extraction)
    output_dir = Path(vault_path).expanduser() / "15_估值引擎" / "估值历史" / "未上市一级市场"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{safe_filename(project_name)}_{created.isoformat()}_未上市一级市场估值框架.md"
    output_path.write_text(private_document_valuation_markdown(extraction, parsed_document, created), encoding="utf-8")
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


def private_document_analysis_markdown(extraction: dict[str, Any], parsed_document: dict[str, Any], created: date) -> str:
    summary = extraction.get("project_summary", {})
    financing = extraction.get("financing_info", {})
    founder_team = extraction.get("founder_team", {})
    commercial_model = extraction.get("commercial_model", {})
    product_and_customers = extraction.get("product_and_customers", {})
    operating = extraction.get("operating_data", {})
    financial = extraction.get("financial_data", {})
    capacity_and_cost = extraction.get("capacity_and_cost", {})
    technology = extraction.get("technology_and_barriers", {})
    market = extraction.get("market_and_competition", {})
    risks = extraction.get("risk_factors", {})
    exit_path = extraction.get("exit_path", {})
    readiness = extraction.get("valuation_readiness", {})
    project_name = project_name_from_extraction(extraction)
    target_type = summary.get("target_type_guess") or "未确认"
    return f"""---
type: private_market_document_analysis
title: {project_name}项目资料解析
status: draft
public: false
created: {created.isoformat()}
source_file: {parsed_document.get("file_name", "")}
target_name: {project_name}
target_type: {target_type}
tags:
  - 一级市场
  - 项目资料解析
  - 估值引擎
---

# {project_name}项目资料解析

## 1. 文件信息

- 文件名：{parsed_document.get("file_name", "")}
- 本地路径：{parsed_document.get("file_path", "")}
- 文件类型：{parsed_document.get("file_type", "")}
- 解析器：{parsed_document.get("parser", "")}
- 解析质量：{parsed_document.get("extraction_quality", "")}
- 页数：{len(parsed_document.get("pages", []))}
- 幻灯片数量：{len(parsed_document.get("slides", []))}
- 段落数量：{len(parsed_document.get("paragraphs", []))}
- 表格数量：{len(parsed_document.get("tables", []))}
- 解析提示：{", ".join(parsed_document.get("warnings", [])) or "无"}

## 2. 项目一句话摘要

{summary.get("one_sentence_summary") or "待补充"}

## 3. 标的类型初判

- 初判类型：{target_type}
- Rachel 战略生态初判：{summary.get("rachel_ecosystem_guess") or "待确认"}
- 所属行业：{summary.get("industry") or "待确认"}
- 所在地：{summary.get("location") or "待确认"}

## 4. 创始团队信息

{dict_section(founder_team)}

需要进一步核验的问题：

{bullet_list(team_questions(founder_team)) if team_questions(founder_team) else "- 暂无"}

## 5. 商业模式

{dict_section(commercial_model)}

## 6. 核心技术与壁垒

{dict_section(technology)}

## 7. 产品与客户

{dict_section(product_and_customers)}

## 8. 市场与竞争

{dict_section(market)}

## 9. 融资信息

{dict_section(financing)}

## 10. 经营与产能数据

{dict_section(operating)}

## 11. 财务数据

{dict_section(financial)}

## 12. 成本结构

{dict_section(capacity_and_cost)}

## 13. 退出路径

{dict_section(exit_path)}

## 14. 推荐估值模型

{bullet_list(readiness.get("recommended_models", [])) if readiness.get("recommended_models") else "- 待补充"}

暂不可用模型：

{bullet_list(readiness.get("unavailable_models", [])) if readiness.get("unavailable_models") else "- 暂无"}

## 15. 数据可信度与缺失项

{markdown_table(extraction.get("field_assessments", []), ["分组", "字段", "提取结果", "来源", "可信度", "是否需要用户确认"])}

缺失项：

{bullet_list(readiness.get("missing_data", [])) if readiness.get("missing_data") else "- 暂无"}

## 16. 需要向项目方追问的问题

{bullet_list(readiness.get("questions_for_company", [])) if readiness.get("questions_for_company") else "- 暂无"}

## 17. 初步风险提示

{dict_section(risks)}

## 18. 后续研究任务

- 核验创始团队履历、股权结构、核心人员稳定性和关键人依赖。
- 核验项目主体、股权结构、融资条款和历史经营数据。
- 补齐可比融资交易、可比上市公司和退出路径假设。
- 对关键数据进行来源标注，区分披露、推断、待确认和缺失。
- 建立乐观、中性、保守三种情景，不输出最终投资结论。

## 19. 免责声明

本文件仅用于 Rachel Capital OS 内部研究，不构成任何投资建议、投资邀约或买卖依据。

## 20. 原始资料摘录

{extraction.get("raw_excerpt") or "未能提取有效文本。"}
"""


def private_document_valuation_markdown(extraction: dict[str, Any], parsed_document: dict[str, Any], created: date) -> str:
    summary = extraction.get("project_summary", {})
    readiness = extraction.get("valuation_readiness", {})
    risks = extraction.get("risk_factors", {})
    founder_team = extraction.get("founder_team", {})
    project_name = project_name_from_extraction(extraction)
    target_type = summary.get("target_type_guess") or "未确认"
    return f"""---
type: private_market_valuation
title: {project_name}未上市一级市场估值框架
status: draft
public: false
created: {created.isoformat()}
source_file: {parsed_document.get("file_name", "")}
target_name: {project_name}
target_type: {target_type}
tags:
  - 估值引擎
  - 未上市估值
  - 一级市场估值
---

# {project_name}未上市 / 一级市场估值框架

## 1. 项目摘要

- 项目名称：{project_name}
- 公司名称：{summary.get("company_name") or "待补充"}
- 一句话摘要：{summary.get("one_sentence_summary") or "待补充"}
- 行业：{summary.get("industry") or "待确认"}
- Rachel 战略生态：{summary.get("rachel_ecosystem_guess") or "待确认"}

## 2. 初判分类

- 标的类型初判：{target_type}
- 分类说明：基于上传资料关键词和已披露信息自动初判，需人工复核。

## 3. 创始团队与团队风险

{dict_section(founder_team)}

团队风险引用：

- {risks.get("team_risk") or "待补充"}
- {risks.get("key_person_risk") or "待补充"}

## 4. 推荐估值模型

{bullet_list(readiness.get("recommended_models", [])) if readiness.get("recommended_models") else "- 待补充"}

暂不可用模型：

{bullet_list(readiness.get("unavailable_models", [])) if readiness.get("unavailable_models") else "- 暂无"}

## 5. 可用数据

{bullet_list(readiness.get("usable_data", [])) if readiness.get("usable_data") else "- 暂无"}

## 6. 缺失数据

{bullet_list(readiness.get("missing_data", [])) if readiness.get("missing_data") else "- 暂无"}

## 7. 追问清单

{bullet_list(readiness.get("questions_for_company", [])) if readiness.get("questions_for_company") else "- 暂无"}

## 8. 风险提示

{dict_section(risks)}

## 9. 初步估值工作流

- 先核验资料中明确披露的数据，剔除无法确认的宣传性表述。
- 按主分类选择估值模型，并为每个模型列出所需输入数据。
- 建立可比交易、可比上市公司和退出路径假设。
- 输出情景框架和数据缺口，不输出买入、卖出或推荐结论。

## 10. 数据可信度

- 数据可信度：{readiness.get("data_confidence_level") or "待确认"}
- 估值置信度：{readiness.get("valuation_confidence_level") or "待确认"}
- 是否适合进入初步估值：{"是" if readiness.get("ready_for_preliminary_valuation") else "否"}

{markdown_table(extraction.get("field_assessments", []), ["分组", "字段", "提取结果", "来源", "可信度", "是否需要用户确认"])}

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


def project_name_from_extraction(extraction: dict[str, Any]) -> str:
    summary = extraction.get("project_summary", {})
    return summary.get("project_name") or summary.get("company_name") or "未命名项目"


def team_questions(founder_team: dict[str, Any]) -> list[str]:
    questions = []
    if founder_team.get("team_gaps"):
        questions.extend(f"请补充：{item}。" for item in founder_team.get("team_gaps", []))
    if not founder_team.get("founders"):
        questions.append("请确认创始人、联合创始人、核心高管姓名和职责分工。")
    questions.append("请核验创始团队过往履历、产业资源、融资经验和核心人员稳定性。")
    return questions


def dict_section(values: dict[str, Any]) -> str:
    lines = []
    for key, value in values.items():
        if isinstance(value, list):
            display = "、".join(str(item) for item in value) if value else "待补充"
        elif value is None or value == "":
            display = "待补充"
        else:
            display = str(value)
        lines.append(f"- {key}：{display}")
    return "\n".join(lines) or "- 待补充"
