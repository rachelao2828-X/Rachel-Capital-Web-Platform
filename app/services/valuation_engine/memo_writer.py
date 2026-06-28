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
    financial_model: dict[str, Any] | None = None,
    created: date | None = None,
) -> Path:
    created = created or date.today()
    project_name = project_name_from_extraction(extraction)
    output_dir = Path(vault_path).expanduser() / "15_估值引擎" / "估值历史" / "未上市一级市场"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{safe_filename(project_name)}_{created.isoformat()}_未上市一级市场估值框架.md"
    output_path.write_text(private_document_valuation_markdown(extraction, parsed_document, created, financial_model), encoding="utf-8")
    return output_path


def write_private_market_financial_model_analysis(
    financial_model: dict[str, Any],
    vault_path: str | Path,
    project_name: str | None = None,
    created: date | None = None,
) -> Path:
    created = created or date.today()
    project_name = project_name or project_name_from_financial_model(financial_model)
    output_dir = Path(vault_path).expanduser() / "15_估值引擎" / "一级市场财务模型解析"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{safe_filename(project_name)}_{created.isoformat()}_财务模型解析.md"
    output_path.write_text(financial_model_analysis_markdown(financial_model, project_name, created), encoding="utf-8")
    return output_path


def write_assumption_confirmation_report(
    assumption_data: dict[str, Any],
    vault_path: str | Path,
    created: date | None = None,
) -> Path:
    created = created or date.today()
    project_name = assumption_data.get("target_name") or "未命名项目"
    output_dir = Path(vault_path).expanduser() / "15_估值引擎" / "关键假设确认"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{safe_filename(project_name)}_{created.isoformat()}_关键假设确认.md"
    output_path.write_text(assumption_confirmation_markdown(assumption_data, created), encoding="utf-8")
    return output_path


def write_basic_valuation_calculation_report(
    valuation_result: dict[str, Any],
    vault_path: str | Path,
    created: date | None = None,
) -> Path:
    created = created or date.today()
    project_name = valuation_result.get("target_name") or "未命名项目"
    output_dir = Path(vault_path).expanduser() / "15_估值引擎" / "基础估值计算"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{safe_filename(project_name)}_{created.isoformat()}_基础估值计算.md"
    output_path.write_text(basic_valuation_calculation_markdown(valuation_result, created), encoding="utf-8")
    return output_path


def write_multi_model_valuation_report(
    multi_model_result: dict[str, Any],
    vault_path: str | Path,
    created: date | None = None,
) -> Path:
    created = created or date.today()
    project_name = multi_model_result.get("target_name") or "未命名项目"
    output_dir = Path(vault_path).expanduser() / "15_估值引擎" / "多模型估值对比"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{safe_filename(project_name)}_{created.isoformat()}_多模型估值对比.md"
    output_path.write_text(multi_model_valuation_markdown(multi_model_result, created), encoding="utf-8")
    return output_path


def write_private_market_investment_memo(
    memo_data: dict[str, Any],
    vault_path: str | Path,
    created: date | None = None,
) -> Path:
    created = created or date.today()
    project_name = memo_data.get("target_name") or "未命名项目"
    output_dir = Path(vault_path).expanduser() / "16_投资决策引擎" / "投资备忘录"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{safe_filename(project_name)}_{created.isoformat()}_投资备忘录草稿.md"
    output_path.write_text(private_market_investment_memo_markdown(memo_data, created), encoding="utf-8")
    return output_path


def write_due_diligence_questions(
    memo_data: dict[str, Any],
    vault_path: str | Path,
    created: date | None = None,
) -> Path:
    created = created or date.today()
    project_name = memo_data.get("target_name") or "未命名项目"
    output_dir = Path(vault_path).expanduser() / "16_投资决策引擎" / "尽调问题清单"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{safe_filename(project_name)}_{created.isoformat()}_尽调问题清单.md"
    output_path.write_text(due_diligence_questions_markdown(memo_data, created), encoding="utf-8")
    return output_path


def write_private_market_project_card(
    tracking_record: dict[str, Any],
    vault_path: str | Path,
    created: date | None = None,
) -> Path:
    created = created or date.today()
    project_name = tracking_record.get("target_name") or "未命名项目"
    output_dir = Path(vault_path).expanduser() / "03_公司数据库" / "一级市场项目"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{safe_filename(project_name)}.md"
    output_path.write_text(private_market_project_card_markdown(tracking_record, created), encoding="utf-8")
    return output_path


def write_project_tracking_tasks(
    tracking_record: dict[str, Any],
    vault_path: str | Path,
    created: date | None = None,
) -> Path:
    created = created or date.today()
    project_name = tracking_record.get("target_name") or "未命名项目"
    output_dir = Path(vault_path).expanduser() / "16_投资决策引擎" / "项目跟踪任务"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{safe_filename(project_name)}_{created.isoformat()}_项目跟踪任务.md"
    output_path.write_text(project_tracking_tasks_markdown(tracking_record, created), encoding="utf-8")
    return output_path


def update_private_market_project_watchlist(
    tracking_record: dict[str, Any],
    vault_path: str | Path,
    created: date | None = None,
) -> Path:
    created = created or date.today()
    output_dir = Path(vault_path).expanduser() / "03_公司数据库" / "一级市场项目"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "一级市场项目观察池.md"
    existing_rows = watchlist_rows_from_markdown(output_path.read_text(encoding="utf-8") if output_path.exists() else "")
    new_row = watchlist_row_from_tracking(tracking_record)
    rows = [row for row in existing_rows if row.get("项目") != new_row["项目"]]
    rows.append(new_row)
    output_path.write_text(private_market_project_watchlist_markdown(rows, tracking_record, created), encoding="utf-8")
    return output_path


def write_target_profile_confirmation_report(
    target_profile: dict[str, Any],
    vault_path: str | Path,
    created: date | None = None,
) -> Path:
    created = created or date.today()
    project_name = target_profile_field(target_profile, "target_name") or "未命名项目"
    output_dir = Path(vault_path).expanduser() / "15_估值引擎" / "标的基本信息确认"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{safe_filename(project_name)}_{created.isoformat()}_标的基本信息确认.md"
    output_path.write_text(target_profile_confirmation_markdown(target_profile, created), encoding="utf-8")
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
    summary = extraction.get("project_basic_info", {})
    financing = extraction.get("financing_info", {})
    founder_team = extraction.get("founder_team", {})
    commercial_model = extraction.get("business_model", {})
    product_and_customers = extraction.get("products_and_customers", {})
    financial = extraction.get("financial_data", {})
    capacity_data = extraction.get("capacity_data", {})
    cost_structure = extraction.get("cost_structure", {})
    technology = extraction.get("technology_route", {})
    market = extraction.get("market_space", {})
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

## 9. 财务数据

{dict_section(financial)}

## 10. 融资信息

{dict_section(financing)}

## 11. 产能数据

{dict_section(capacity_data)}

## 12. 成本结构

{dict_section(cost_structure)}

## 13. 退出路径

{dict_section(exit_path)}

## 14. 风险因素

{dict_section(risks)}

## 15. 估值可用性

{dict_section(readiness)}

## 16. 推荐估值模型

{bullet_list(readiness.get("recommended_models", [])) if readiness.get("recommended_models") else "- 待补充"}

暂不可用模型：

{bullet_list(readiness.get("unavailable_models", [])) if readiness.get("unavailable_models") else "- 暂无"}

## 17. 缺失数据清单

{bullet_list(readiness.get("missing_data", [])) if readiness.get("missing_data") else "- 暂无"}

数据可信度：

{markdown_table(extraction.get("field_assessments", []), ["分组", "字段", "提取结果", "来源", "可信度", "是否需要确认"])}

## 18. 需要向项目方追问的问题

{bullet_list(readiness.get("questions_for_company", [])) if readiness.get("questions_for_company") else "- 暂无"}

## 19. 后续研究任务

- 核验创始团队履历、股权结构、核心人员稳定性和关键人依赖。
- 核验项目主体、股权结构、融资条款和历史经营数据。
- 补齐可比融资交易、可比上市公司和退出路径假设。
- 对关键数据进行来源标注，区分披露、推断、待确认和缺失。
- 建立乐观、中性、保守三种情景，不输出最终投资结论。

## 20. 免责声明

本文件仅用于 Rachel Capital OS 内部研究，不构成任何投资建议、投资邀约或买卖依据。

## 21. 原始资料关键摘录

{extraction.get("raw_excerpt") or "未能提取有效文本。"}
"""


def private_document_valuation_markdown(
    extraction: dict[str, Any],
    parsed_document: dict[str, Any],
    created: date,
    financial_model: dict[str, Any] | None = None,
) -> str:
    summary = extraction.get("project_basic_info", {})
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

## 1. 标的基本信息

- 项目名称：{project_name}
- 公司名称：{summary.get("company_name") or "待补充"}
- 一句话摘要：{summary.get("one_sentence_summary") or "待补充"}
- 行业：{summary.get("industry") or "待确认"}
- Rachel 战略生态：{summary.get("rachel_ecosystem_guess") or "待确认"}

## 2. 主分类与辅助分类

- 主分类：{target_type}
- 辅助分类：待后续人工确认。

## 3. 判断理由

- 基于上传资料关键词和已披露信息自动初判，需人工复核。
- 当前输出仅作为内部研究草稿，不构成投资建议。

## 4. 推荐估值模型

{bullet_list(readiness.get("recommended_models", [])) if readiness.get("recommended_models") else "- 待补充"}

## 5. 多模型适用性对比

{markdown_table(model_rows_for_readiness(readiness), ["模型", "适用度", "适用原因", "必需数据", "输出结果", "权重建议"])}

## 6. 必须考虑的折扣或敏感性因素

{bullet_list(readiness.get("unavailable_models", [])) if readiness.get("unavailable_models") else "- 需结合流动性、退出路径、技术成熟度、团队风险和数据可信度继续确认。"}

## 7. 需要补充的数据

{bullet_list(readiness.get("missing_data", [])) if readiness.get("missing_data") else "- 暂无"}

## 8. 初步估值思路

- 先核验资料中明确披露的数据，剔除无法确认的宣传性表述。
- 按主分类选择估值模型，并为每个模型列出所需输入数据。
- 建立可比交易、可比上市公司和退出路径假设。
- 输出情景框架和数据缺口，不输出买入、卖出、推荐、目标价或收益承诺。

## 9. 风险与不确定性

{dict_section(risks)}

## 10. 创始团队对估值的影响

{dict_section(founder_team)}

团队风险：

- {risks.get("team_risk") or "待补充"}
- {risks.get("key_person_risk") or "待补充"}

## 11. Excel / 财务模型补充信息

{financial_model_supplement_markdown(financial_model)}

## 12. 后续研究任务

- 向项目方追问缺失数据和关键假设。
- 核验创始团队履历、股权结构、核心人员稳定性和融资经验。
- 建立可比公司、可比交易和退出路径数据库。
- 明确折扣、敏感性和估值区间的输入条件。

## 13. 免责声明

本文件仅用于 Rachel Capital OS 内部研究，不构成任何投资建议、投资邀约或买卖依据。
"""


def financial_model_analysis_markdown(financial_model: dict[str, Any], project_name: str, created: date) -> str:
    extracted = financial_model.get("extracted_financial_data", {})
    return f"""---
type: private_market_financial_model_analysis
title: {project_name}财务模型解析
status: draft
public: false
created: {created.isoformat()}
source_file: {financial_model.get("file_name", "")}
target_name: {project_name}
tags:
  - 一级市场
  - 财务模型解析
  - 估值引擎
---

# {project_name}财务模型解析

## 1. 文件信息

- 文件名：{financial_model.get("file_name", "")}
- 本地路径：{financial_model.get("file_path", "")}
- 文件类型：{financial_model.get("file_type", "")}
- 解析器：{financial_model.get("parser", "")}
- 解析质量：{financial_model.get("extraction_quality", "")}
- 解析提示：{", ".join(financial_model.get("warnings", [])) or "无"}

## 2. Sheet 列表

{sheet_list_markdown(financial_model.get("sheets", []))}

## 3. 自动识别的财务表类型

{detected_sections_markdown(financial_model.get("detected_financial_sections", {}))}

## 4. 收入与增长

{dict_section(extracted.get("revenue_related", {}))}

## 5. 毛利与利润

{dict_section(extracted.get("gross_profit_and_profit", {}))}

## 6. 成本费用结构

{dict_section(extracted.get("costs_and_expenses", {}))}

## 7. 现金流

{dict_section(extracted.get("cash_flow", {}))}

## 8. CAPEX 与产能

{dict_section(extracted.get("investment_and_capacity", {}))}

## 9. 融资与回报

{dict_section(extracted.get("financing_and_returns", {}))}

## 10. 敏感性假设

{dict_section(extracted.get("sensitivity_assumptions", {}))}

## 11. 关键财务数据可信度

{markdown_table(extracted.get("field_assessments", []), ["field", "extraction_result", "source_sheet", "source_position", "confidence", "needs_confirmation"])}

## 12. 缺失财务数据

{bullet_list(extracted.get("missing_financial_data", [])) if extracted.get("missing_financial_data") else "- 暂无"}

## 13. 需要用户确认的数据

{bullet_list(extracted.get("requires_user_confirmation", [])) if extracted.get("requires_user_confirmation") else "- 暂无"}

## 14. 可支持的估值模型

{bullet_list(extracted.get("supported_valuation_models", [])) if extracted.get("supported_valuation_models") else "- 待补充"}

## 15. 风险与异常点

- Excel / CSV 数据来自项目方或用户上传资料，需核验公式、版本、口径和审计来源。
- 如果文本资料与财务模型数据存在冲突，应优先标记并向项目方追问。
- 当前解析只提取关键字段和表格结构，不自动给出目标价、推荐或收益承诺。

## 16. 后续研究任务

{bullet_list(extracted.get("recommended_supplemental_materials", [])) if extracted.get("recommended_supplemental_materials") else "- 补齐财务模型关键假设。"}

## 17. 免责声明

本文件仅用于 Rachel Capital OS 内部研究，不构成任何投资建议、投资邀约或买卖依据。
"""


def assumption_confirmation_markdown(assumption_data: dict[str, Any], created: date) -> str:
    project_name = assumption_data.get("target_name") or "未命名项目"
    readiness = assumption_data.get("readiness_summary", {})
    groups = assumption_data.get("assumption_groups", {})
    return f"""---
type: private_market_assumption_confirmation
title: {project_name}关键假设确认
status: draft
public: false
created: {created.isoformat()}
target_name: {project_name}
valuation_readiness: {readiness.get("valuation_readiness_level", "不足")}
tags:
  - 一级市场
  - 关键假设确认
  - 估值引擎
---

# {project_name}关键假设确认

## 1. 来源文件

{source_files_markdown(assumption_data.get("source_files", []))}

## 2. 估值准备度

- 准备度等级：{readiness.get("valuation_readiness_level", "不足")}
- 判断理由：{readiness.get("reason", "待确认")}
- 是否可以进入 V0.6 自动估值计算：{"是" if readiness.get("ready_for_v0_6_calculation") else "否"}

进入计算前必须补充的数据：

{bullet_list(readiness.get("missing_before_calculation", [])) if readiness.get("missing_before_calculation") else "- 暂无"}

## 3. 项目基本假设

{assumption_group_markdown(groups.get("project_basic", []))}

## 4. 融资与估值假设

{assumption_group_markdown(groups.get("financing_valuation", []))}

## 5. 收入假设

{assumption_group_markdown(groups.get("revenue", []))}

## 6. 成本与利润假设

{assumption_group_markdown(groups.get("cost_profit", []))}

## 7. 现金流假设

{assumption_group_markdown(groups.get("cash_flow", []))}

## 8. CAPEX 与产能假设

{assumption_group_markdown(groups.get("capex_capacity", []))}

## 9. 回报与估值计算假设

{assumption_group_markdown(groups.get("return_valuation", []))}

## 10. 情景与敏感性假设

{assumption_group_markdown(groups.get("scenario_sensitivity", []))}

## 11. 创始团队假设

{assumption_group_markdown(groups.get("founder_team", []))}

## 12. 风险与缺失数据假设

{assumption_group_markdown(groups.get("risk_missing_data", []))}

## 13. 进入 V0.6 自动估值计算前必须补充的数据

{bullet_list(readiness.get("missing_before_calculation", [])) if readiness.get("missing_before_calculation") else "- 暂无"}

## 14. 后续研究任务

- 逐项核验所有需要确认的关键假设。
- 对项目方预测口径、合同、订单、成本、现金流和退出路径进行交叉验证。
- 将确认后的 JSON 作为 V0.6 自动估值计算的输入，不读取未确认或缺失字段。
- 保留 human review gate，不输出买入、卖出、推荐、目标价或收益承诺。

## 15. 免责声明

本文件仅用于 Rachel Capital OS 内部研究，不构成任何投资建议、投资邀约或买卖依据。
"""


def basic_valuation_calculation_markdown(valuation_result: dict[str, Any], created: date) -> str:
    project_name = valuation_result.get("target_name") or "未命名项目"
    valuation_range = valuation_result.get("valuation_range", {})
    return f"""---
type: private_market_basic_valuation_calculation
title: {project_name}基础估值计算
status: draft
public: false
created: {created.isoformat()}
target_name: {project_name}
valuation_confidence: {valuation_result.get("confidence_level", "仅供框架参考")}
tags:
  - 一级市场
  - 基础估值计算
  - 估值引擎
---

# {project_name}基础估值计算

## 1. 输入来源

本报告基于 V0.5 已确认关键假设生成，只读取 confirmed_value、use_in_valuation = true 且 confidence 不为“缺失”的输入。

## 2. 关键假设摘要

{dict_section(valuation_result.get("input_summary", {}))}

## 3. 估值准备度

- 综合估值置信度：{valuation_result.get("confidence_level", "仅供框架参考")}
- 置信度说明：{valuation_result.get("confidence_reason", "待确认")}

## 4. 可计算模型

{bullet_list(valuation_result.get("available_models", [])) if valuation_result.get("available_models") else "- 暂无"}

## 5. 不可计算模型与缺失字段

{unavailable_models_markdown(valuation_result.get("unavailable_models", []))}

## 6. 模型结果表

{model_results_markdown(valuation_result.get("model_results", []))}

## 7. 折扣与风险调整

{markdown_table(valuation_result.get("risk_adjustments", []), ["折扣项", "折扣率", "原因", "是否应用"])}

## 8. 初步估值区间

- 初步估值区间：{valuation_range.get("display", "可计算模型不足，暂不生成综合区间。")}
- 货币单位：{valuation_range.get("currency", "万元 RMB")}
- 生成方法：{valuation_range.get("method", "")}
- 使用方式：研究参考，需人工确认。

## 9. 敏感性提示

{bullet_list(valuation_result.get("sensitivity_notes", [])) if valuation_result.get("sensitivity_notes") else "- 暂无"}

## 10. 主要限制

{bullet_list(valuation_result.get("warnings", [])) if valuation_result.get("warnings") else "- 本阶段仅生成基础估值计算结果，不构成最终投资结论。"}

## 11. 后续需要补充的数据

{bullet_list(valuation_result.get("missing_data", [])) if valuation_result.get("missing_data") else "- 暂无"}

## 12. 后续研究任务

- 核验所有估值输入的来源、口径、期间和可比样本。
- 补充收入倍数、利润倍数、折现率、现金流、CAPEX 和退出路径假设。
- 在 V0.7 中进行多模型对比、权重调整和综合估值区间校验。
- 保留 human review gate，不输出买入、卖出、推荐、目标价或收益承诺。

## 13. 免责声明

本文件仅用于 Rachel Capital OS 内部研究，不构成任何投资建议、投资邀约或买卖依据。
"""


def multi_model_valuation_markdown(multi_model_result: dict[str, Any], created: date) -> str:
    project_name = multi_model_result.get("target_name") or "未命名项目"
    weighted_range = multi_model_result.get("weighted_valuation_range", {})
    dispersion = multi_model_result.get("model_dispersion", {})
    return f"""---
type: private_market_multi_model_valuation
title: {project_name}多模型估值对比
status: draft
public: false
created: {created.isoformat()}
target_name: {project_name}
valuation_confidence: {multi_model_result.get("confidence_level", "仅供框架参考")}
tags:
  - 一级市场
  - 多模型估值对比
  - 估值引擎
---

# {project_name}多模型估值对比

## 1. 输入来源

- 输入来源：{multi_model_result.get("input_source", "V0.6 基础估值计算结果")}
- 标的类型：{multi_model_result.get("target_type", "未确认")}
- 估值日期：{multi_model_result.get("valuation_date", created.isoformat())}

## 2. V0.6 基础估值结果摘要

本报告基于 V0.6 基础估值计算结果生成，所有模型结果需人工确认，不构成最终投资结论。

## 3. 纳入综合区间的模型

{included_models_markdown(multi_model_result.get("weighting_table", []))}

## 4. 未纳入模型及原因

{excluded_models_markdown(multi_model_result.get("excluded_models", []))}

## 5. 模型权重表

{weighting_table_markdown(multi_model_result.get("weighting_table", []))}

## 6. 模型结果对比

{multi_model_comparison_markdown(multi_model_result.get("model_comparison", []))}

## 7. 加权综合估值区间

- 保守估值：{format_report_money(weighted_range.get("low"))}
- 中性估值：{format_report_money(weighted_range.get("base"))}
- 乐观估值：{format_report_money(weighted_range.get("high"))}
- 区间展示：{weighted_range.get("display", "暂不生成综合区间")}
- 货币单位：{weighted_range.get("currency", "万元 RMB")}
- 生成方法：{weighted_range.get("method", "")}
- 权重来源：{weighted_range.get("weight_source", "")}
- 纳入模型数量：{weighted_range.get("included_model_count", 0)}
- 剔除模型数量：{weighted_range.get("excluded_model_count", 0)}

## 8. 模型分歧度

- 最低模型估值：{format_report_money(dispersion.get("min_value"))}
- 最高模型估值：{format_report_money(dispersion.get("max_value"))}
- 分歧倍数：{format_ratio(dispersion.get("spread_ratio"))}
- 分歧等级：{dispersion.get("dispersion_level", "无法判断")}
- 主要原因：{dispersion.get("reason", "待确认")}

## 9. 综合置信度

- 综合置信度：{multi_model_result.get("confidence_level", "仅供框架参考")}
- 说明：{multi_model_result.get("confidence_reason", "待确认")}

## 10. 主要分歧来源

{bullet_list(multi_model_result.get("major_divergence_drivers", [])) if multi_model_result.get("major_divergence_drivers") else "- 暂无"}

## 11. 敏感性提示

{bullet_list(multi_model_result.get("sensitivity_notes", [])) if multi_model_result.get("sensitivity_notes") else "- 暂无"}

## 12. 主要限制

{bullet_list(multi_model_result.get("warnings", [])) if multi_model_result.get("warnings") else "- 本阶段仅生成多模型估值对比与综合区间，不构成最终投资结论。"}

## 13. 后续需要补充的数据

{bullet_list(multi_model_result.get("for_v0_8_decision_memo", {}).get("data_gaps", [])) if multi_model_result.get("for_v0_8_decision_memo", {}).get("data_gaps") else "- 暂无"}

## 14. 后续研究任务

- 核验各模型输入数据、口径、期间、权重和剔除原因。
- 补充可比公司、可比交易、退出路径、现金流和折扣假设。
- 在 V0.8 中形成投资备忘录草稿前，保留 human review gate。
- 不输出买入、卖出、推荐、目标价或收益承诺。

## 15. 免责声明

本文件仅用于 Rachel Capital OS 内部研究，不构成任何投资建议、投资邀约、买卖依据、目标价或收益承诺。
"""


def private_market_investment_memo_markdown(memo_data: dict[str, Any], created: date) -> str:
    project_name = memo_data.get("target_name") or "未命名项目"
    research_action = memo_data.get("research_action", {})
    return f"""---
type: private_market_investment_memo
title: {project_name}投资备忘录草稿
status: draft
public: false
created: {created.isoformat()}
target_name: {project_name}
memo_completeness: {memo_data.get("memo_completeness", "不足")}
research_action: {research_action.get("suggested_action", "需要补充数据")}
tags:
  - 一级市场
  - 投资备忘录
  - 投资决策引擎
---

# {project_name}投资备忘录草稿

## 1. 项目快照

{dict_section(memo_data.get("project_snapshot", {}))}

## 2. 创始团队评估

{dict_section(memo_data.get("founder_team_review", {}))}

## 3. 商业模式评估

{dict_section(memo_data.get("business_model_review", {}))}

## 4. 技术与壁垒评估

{dict_section(memo_data.get("technology_review", {}))}

## 5. 产品与客户评估

{dict_section(memo_data.get("product_customer_review", {}))}

## 6. 市场与竞争评估

{dict_section(memo_data.get("market_competition_review", {}))}

## 7. 财务与经营评估

{dict_section(memo_data.get("financial_review", {}))}

## 8. 融资与估值评估

{dict_section(memo_data.get("financing_valuation_review", {}))}

## 9. 主要风险

{dict_section(memo_data.get("risk_summary", {}))}

## 10. 尽调问题清单

{due_diligence_questions_table(memo_data.get("due_diligence_questions", []))}

## 11. 数据缺口

{bullet_list(memo_data.get("data_gaps", [])) if memo_data.get("data_gaps") else "- 暂无"}

## 12. 研究动作建议

- 建议动作：{research_action.get("suggested_action", "需要补充数据")}
- 原因：{research_action.get("reason", "待补充")}

后续步骤：

{bullet_list(research_action.get("next_steps", [])) if research_action.get("next_steps") else "- 待补充"}

## 13. 后续研究任务

{bullet_list(memo_data.get("for_v0_9_project_tracking", {}).get("follow_up_tasks", [])) if memo_data.get("for_v0_9_project_tracking", {}).get("follow_up_tasks") else "- 待补充"}

## 14. 免责声明

本文件仅用于 Rachel Capital OS 内部研究，不构成任何投资建议、投资邀约、买卖依据、目标价或收益承诺。
"""


def due_diligence_questions_markdown(memo_data: dict[str, Any], created: date) -> str:
    project_name = memo_data.get("target_name") or "未命名项目"
    grouped = group_due_diligence_questions(memo_data.get("due_diligence_questions", []))
    return f"""---
type: private_market_due_diligence_questions
title: {project_name}尽调问题清单
status: draft
public: false
created: {created.isoformat()}
target_name: {project_name}
tags:
  - 一级市场
  - 尽调问题
  - 投资决策引擎
---

# {project_name}尽调问题清单

## 1. 团队尽调

{numbered_questions(grouped.get("团队尽调", []))}

## 2. 技术尽调

{numbered_questions(grouped.get("技术尽调", []))}

## 3. 产品与客户尽调

{numbered_questions(grouped.get("产品与客户尽调", []))}

## 4. 市场与竞争尽调

{numbered_questions(grouped.get("市场与竞争尽调", []))}

## 5. 财务尽调

{numbered_questions(grouped.get("财务尽调", []))}

## 6. 融资与股权结构尽调

{numbered_questions(grouped.get("融资与股权结构尽调", []))}

## 7. 法务与合规尽调

{numbered_questions(grouped.get("法务与合规尽调", []))}

## 8. 退出路径尽调

{numbered_questions(grouped.get("退出路径尽调", []))}

## 9. 数据补充清单

{bullet_list(memo_data.get("data_gaps", [])) if memo_data.get("data_gaps") else "- 暂无"}

## 10. 后续跟进任务

{bullet_list(memo_data.get("for_v0_9_project_tracking", {}).get("follow_up_tasks", [])) if memo_data.get("for_v0_9_project_tracking", {}).get("follow_up_tasks") else "- 待补充"}

## 11. 免责声明

本文件仅用于 Rachel Capital OS 内部研究，不构成任何投资建议、投资邀约、买卖依据、目标价或收益承诺。
"""


def private_market_project_card_markdown(tracking_record: dict[str, Any], created: date) -> str:
    card = tracking_record.get("project_card", {})
    project_name = tracking_record.get("target_name") or "未命名项目"
    ecosystem = card.get("rachel_ecosystem") or "待确认"
    return f"""---
type: private_market_project
title: {project_name}
status: active
public: false
created: {created.isoformat()}
updated: {created.isoformat()}
target_name: {project_name}
target_type: {card.get("target_type", "待确认")}
project_status: {tracking_record.get("project_status", "")}
watchlist_status: {tracking_record.get("watchlist_status", "")}
research_action: {tracking_record.get("research_action", "")}
next_review_date: {tracking_record.get("next_review_date", "")}
linked_ecosystem:
  - {ecosystem}
tags:
  - 一级市场项目
  - 估值驾驶舱
  - 项目观察池
---

# {project_name}

## 1. 项目快照

{dict_section(card)}

## 2. 一句话摘要

{card.get("one_sentence_summary") or "待补充"}

## 3. 创始团队摘要

{card.get("founder_team_summary") or "待补充"}

## 4. 商业模式摘要

{card.get("business_model_summary") or "待补充"}

## 5. 技术与壁垒摘要

{card.get("technology_summary") or "待补充"}

## 6. 产品与客户摘要

{card.get("product_customer_summary") or "待补充"}

## 7. 市场与竞争摘要

{card.get("market_summary") or "待补充"}

## 8. 财务与融资摘要

- 财务摘要：{card.get("financial_summary") or "待补充"}
- 融资摘要：{card.get("financing_summary") or "待补充"}

## 9. 估值摘要

{card.get("valuation_summary") or "待补充"}

## 10. 主要风险

{card.get("risk_summary") or "待补充"}

## 11. 当前研究动作

- 项目状态：{tracking_record.get("project_status", "")}
- 观察池状态：{tracking_record.get("watchlist_status_label", tracking_record.get("watchlist_status", ""))}
- 研究动作：{tracking_record.get("research_action", "")}
- 下次复查日期：{tracking_record.get("next_review_date", "") or "暂不设置"}

## 12. 数据缺口

{bullet_list(tracking_record.get("data_gaps", [])) if tracking_record.get("data_gaps") else "- 暂无"}

## 13. 需要向项目方追问的问题

{bullet_list(tracking_record.get("questions_for_company", [])) if tracking_record.get("questions_for_company") else "- 暂无"}

## 14. 后续跟踪任务

{tracking_tasks_markdown(tracking_record.get("tracking_tasks", []))}

## 15. 关联文件

{linked_files_markdown(card)}

## 16. 后续复查记录

- {created.isoformat()}：由 Valuation Cockpit V0.9 自动生成项目卡片。

## 17. 免责声明

本文件仅用于 Rachel Capital OS 内部研究，不构成任何投资建议、投资邀约、买卖依据、目标价或收益承诺。
"""


def project_tracking_tasks_markdown(tracking_record: dict[str, Any], created: date) -> str:
    project_name = tracking_record.get("target_name") or "未命名项目"
    tasks = tracking_record.get("tracking_tasks", [])
    return f"""---
type: private_market_project_tracking_tasks
title: {project_name}项目跟踪任务
status: active
public: false
created: {created.isoformat()}
target_name: {project_name}
next_review_date: {tracking_record.get("next_review_date", "")}
tags:
  - 一级市场
  - 项目跟踪
  - 投资决策引擎
---

# {project_name}项目跟踪任务

## 1. 项目状态

- 项目状态：{tracking_record.get("project_status", "")}
- 观察池状态：{tracking_record.get("watchlist_status_label", tracking_record.get("watchlist_status", ""))}
- 研究动作：{tracking_record.get("research_action", "")}

## 2. 下次复查日期

{tracking_record.get("next_review_date", "") or "暂不设置"}

## 3. 高优先级任务

{task_list_by_priority(tasks, "高")}

## 4. 中优先级任务

{task_list_by_priority(tasks, "中")}

## 5. 低优先级任务

{task_list_by_priority(tasks, "低")}

## 6. 数据补充任务

{task_list_by_category(tasks, "资料补充")}

## 7. 尽调任务

{task_list_by_categories(tasks, ["团队尽调", "技术尽调", "客户尽调", "财务尽调", "法务合规"])}

## 8. 估值复核任务

{task_list_by_category(tasks, "估值复核")}

## 9. 后续跟进记录

- {created.isoformat()}：由 Valuation Cockpit V0.9 自动生成项目跟踪任务。

## 10. 免责声明

本文件仅用于 Rachel Capital OS 内部研究，不构成任何投资建议、投资邀约、买卖依据、目标价或收益承诺。
"""


def private_market_project_watchlist_markdown(rows: list[dict[str, str]], tracking_record: dict[str, Any], created: date) -> str:
    return f"""---
type: private_market_project_watchlist
title: 一级市场项目观察池
status: active
public: false
updated: {created.isoformat()}
tags:
  - 一级市场项目
  - 项目观察池
  - Rachel Capital OS
---

# 一级市场项目观察池

## 1. 使用说明

本文件用于汇总 Rachel Capital OS 中由 Valuation Cockpit 生成或维护的一级市场项目观察对象。

所有项目仅作为内部研究观察对象，不构成投资建议。

## 2. 观察池总览

{markdown_table(rows, ["项目", "所属行业", "所属生态", "标的类型", "项目状态", "观察池状态", "研究动作", "估值置信度", "下次复查日期", "项目卡片"])}

## 3. 按状态分组

### 观察中

{watchlist_group(rows, "active")}

### 等待资料

{watchlist_group(rows, "pending_data")}

### 深度研究候选

{watchlist_group(rows, "deep_research_candidate")}

### 暂缓

{watchlist_group(rows, "paused")}

### 已进入投资决策

{watchlist_group(rows, "investment_decision_candidate")}

### 已归档 / 已放弃

{watchlist_groups(rows, ["archived", "rejected"])}

## 4. 本周需要复查项目

{watchlist_due_soon(rows, created)}

## 5. 更新记录

- {created.isoformat()}：由 Valuation Cockpit V0.9 生成或更新，最新项目：{tracking_record.get("target_name", "未命名项目")}。

## 6. 免责声明

本文件仅用于 Rachel Capital OS 内部研究，不构成任何投资建议、投资邀约、买卖依据、目标价或收益承诺。
"""


def target_profile_confirmation_markdown(target_profile: dict[str, Any], created: date) -> str:
    project_name = target_profile_field(target_profile, "target_name") or "未命名项目"
    target_type = target_profile_field(target_profile, "target_type") or "待确认"
    return f"""---
type: private_market_target_profile_confirmation
title: {project_name}标的基本信息确认
status: draft
public: false
created: {created.isoformat()}
target_name: {project_name}
target_type: {target_type}
tags:
  - 一级市场
  - 标的基本信息
  - 估值引擎
---

# {project_name}标的基本信息确认

## 1. 系统识别摘要

{target_profile_detected_summary(target_profile)}

## 2. 用户确认结果

{target_profile_confirmed_summary(target_profile)}

## 3. 字段来源与可信度

{target_profile_fields_markdown(target_profile)}

## 4. 标的类型判断理由

{target_profile.get("classification_reason") or "待确认"}

## 5. 对估值模型选择的影响

- 标的类型：{target_type}
- 估值模型选择应优先读取本确认结果中的 confirmed_value。
- 若标的类型为项目公司 / SPV，应优先关注 DCF、IRR、项目现金流和投资回收期。
- 若标的类型为资产型项目，应优先关注资产重估、重置成本、合同现金流和可交易性。
- 若标的类型为一级市场融资标的或未上市成长公司，应优先关注收入倍数、利润倍数、EBITDA 倍数和可比交易。

## 6. 需要继续确认的信息

{bullet_list(target_profile.get("warnings", [])) if target_profile.get("warnings") else "- 暂无"}

## 7. 免责声明

本文件仅用于 Rachel Capital OS 内部研究，不构成任何投资建议、投资邀约、买卖依据、目标价或收益承诺。
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
    summary = extraction.get("project_basic_info", {})
    return summary.get("project_name") or summary.get("company_name") or "未命名项目"


def project_name_from_financial_model(financial_model: dict[str, Any]) -> str:
    file_name = Path(str(financial_model.get("file_name") or "未命名项目")).stem
    cleaned = re.sub(r"[_\-\s]*(财务模型|财务预测|financial.?model|model)$", "", file_name, flags=re.IGNORECASE).strip()
    return cleaned or "未命名项目"


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
        elif isinstance(value, dict):
            display = value.get("extraction_result") or str(value)
        elif value is None or value == "":
            display = "待补充"
        else:
            display = str(value)
        lines.append(f"- {key}：{display}")
    return "\n".join(lines) or "- 待补充"


def model_rows_for_readiness(readiness: dict[str, Any]) -> list[dict[str, str]]:
    rows = []
    for model in readiness.get("recommended_models", []):
        rows.append(
            {
                "模型": model,
                "适用度": "待确认",
                "适用原因": "由标的类型和已提取数据自动推荐，需人工复核。",
                "必需数据": "详见缺失数据清单和追问清单",
                "输出结果": "估值框架或估值区间输入",
                "权重建议": "待人工确认",
            }
        )
    return rows


def sheet_list_markdown(sheets: list[dict[str, Any]]) -> str:
    rows = [
        {"Sheet": item.get("sheet_name", ""), "行数": str(item.get("max_row", "")), "列数": str(item.get("max_column", ""))}
        for item in sheets
    ]
    return markdown_table(rows, ["Sheet", "行数", "列数"]) if rows else "- 未识别到 Sheet。"


def detected_sections_markdown(sections: dict[str, Any]) -> str:
    rows = []
    for section, matches in sections.items():
        rows.append(
            {
                "财务表类型": section,
                "匹配 Sheet": "、".join(item.get("sheet_name", "") for item in matches) if matches else "未识别",
                "关键词": "、".join(item.get("matched_keywords", "") for item in matches) if matches else "",
            }
        )
    return markdown_table(rows, ["财务表类型", "匹配 Sheet", "关键词"]) if rows else "- 未识别到财务表类型。"


def source_files_markdown(source_files: list[dict[str, str]]) -> str:
    rows = [{"文件名": item.get("file_name", ""), "类型": item.get("source_type", "")} for item in source_files]
    return markdown_table(rows, ["文件名", "类型"]) if rows else "- 暂无来源文件。"


def assumption_group_markdown(items: list[dict[str, Any]]) -> str:
    rows = [
        {
            "字段": item.get("field", ""),
            "系统提取值": item.get("extracted_value", ""),
            "用户确认值": item.get("confirmed_value", ""),
            "单位": item.get("unit", ""),
            "期间/情景": item.get("period", ""),
            "来源": item.get("source", ""),
            "可信度": item.get("confidence", ""),
            "用于估值": "是" if item.get("use_in_valuation") else "否",
            "备注": item.get("notes", ""),
        }
        for item in items
    ]
    return markdown_table(rows, ["字段", "系统提取值", "用户确认值", "单位", "期间/情景", "来源", "可信度", "用于估值", "备注"]) if rows else "- 暂无"


def model_results_markdown(rows: list[dict[str, Any]]) -> str:
    display_rows = [
        {
            "模型": row.get("model", ""),
            "适用度": row.get("status", ""),
            "输入完整度": row.get("input_completeness", ""),
            "原始估值": row.get("raw_valuation", ""),
            "折扣后估值": row.get("discounted_valuation", ""),
            "置信度": row.get("confidence", ""),
            "主要依据": row.get("主要依据", ""),
            "主要限制": row.get("main_limitations", ""),
        }
        for row in rows
    ]
    return markdown_table(display_rows, ["模型", "适用度", "输入完整度", "原始估值", "折扣后估值", "置信度", "主要依据", "主要限制"]) if display_rows else "- 暂无"


def unavailable_models_markdown(rows: list[dict[str, Any]]) -> str:
    display_rows = [
        {
            "模型": row.get("model", ""),
            "缺失字段": "、".join(row.get("missing_fields", [])),
            "主要限制": row.get("主要限制", ""),
        }
        for row in rows
    ]
    return markdown_table(display_rows, ["模型", "缺失字段", "主要限制"]) if display_rows else "- 暂无"


def included_models_markdown(rows: list[dict[str, Any]]) -> str:
    included = [
        {
            "模型": row.get("model", ""),
            "归一化权重": format_percent(row.get("normalized_weight")),
            "模型置信度": row.get("model_confidence", ""),
        }
        for row in rows
        if row.get("include_in_range")
    ]
    return markdown_table(included, ["模型", "归一化权重", "模型置信度"]) if included else "- 暂无"


def excluded_models_markdown(rows: list[dict[str, Any]]) -> str:
    display_rows = [{"模型": row.get("model", ""), "原因": row.get("reason", "")} for row in rows]
    return markdown_table(display_rows, ["模型", "原因"]) if display_rows else "- 暂无"


def weighting_table_markdown(rows: list[dict[str, Any]]) -> str:
    display_rows = [
        {
            "模型": row.get("model", ""),
            "默认权重": f"{row.get('default_weight', 0):.1f}%",
            "用户调整权重": f"{row.get('user_weight', 0):.1f}%",
            "归一化权重": format_percent(row.get("normalized_weight")),
            "是否纳入综合区间": "是" if row.get("include_in_range") else "否",
            "权重原因": row.get("weight_reason", ""),
            "模型置信度": row.get("model_confidence", ""),
        }
        for row in rows
    ]
    return markdown_table(display_rows, ["模型", "默认权重", "用户调整权重", "归一化权重", "是否纳入综合区间", "权重原因", "模型置信度"]) if display_rows else "- 暂无"


def multi_model_comparison_markdown(rows: list[dict[str, Any]]) -> str:
    display_rows = [
        {
            "模型": row.get("model", ""),
            "适用度": row.get("status", ""),
            "输入完整度": row.get("input_completeness", ""),
            "折扣后估值": row.get("discounted_valuation", ""),
            "置信度": row.get("confidence", ""),
            "主要依据": row.get("basis", ""),
            "主要限制": row.get("limitations", ""),
            "是否可纳入": "是" if row.get("can_include") else "否",
        }
        for row in rows
    ]
    return markdown_table(display_rows, ["模型", "适用度", "输入完整度", "折扣后估值", "置信度", "主要依据", "主要限制", "是否可纳入"]) if display_rows else "- 暂无"


def due_diligence_questions_table(rows: list[dict[str, Any]]) -> str:
    display_rows = [
        {
            "分类": row.get("category", ""),
            "问题": row.get("question", ""),
            "优先级": row.get("priority", ""),
        }
        for row in rows
    ]
    return markdown_table(display_rows, ["分类", "问题", "优先级"]) if display_rows else "- 暂无"


def group_due_diligence_questions(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(row.get("category", "其他"), []).append(row)
    return grouped


def numbered_questions(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "- 暂无"
    return "\n".join(f"{index}. {row.get('question', '')}（优先级：{row.get('priority', '中')}）" for index, row in enumerate(rows, start=1))


def tracking_tasks_markdown(rows: list[dict[str, Any]]) -> str:
    display_rows = [
        {
            "任务": row.get("task", ""),
            "分类": row.get("category", ""),
            "优先级": row.get("priority", ""),
            "截止日期": row.get("due_date", ""),
            "状态": row.get("status", ""),
            "来源": row.get("source", ""),
        }
        for row in rows
    ]
    return markdown_table(display_rows, ["任务", "分类", "优先级", "截止日期", "状态", "来源"]) if display_rows else "- 暂无"


def task_list_by_priority(rows: list[dict[str, Any]], priority: str) -> str:
    return tracking_tasks_markdown([row for row in rows if row.get("priority") == priority])


def task_list_by_category(rows: list[dict[str, Any]], category: str) -> str:
    return tracking_tasks_markdown([row for row in rows if row.get("category") == category])


def task_list_by_categories(rows: list[dict[str, Any]], categories: list[str]) -> str:
    return tracking_tasks_markdown([row for row in rows if row.get("category") in categories])


def linked_files_markdown(card: dict[str, Any]) -> str:
    rows = []
    for item in card.get("linked_memos", []):
        rows.append(f"- {item}")
    for item in card.get("linked_questions", []):
        rows.append(f"- {item}")
    if not rows:
        return "- 暂无。可后续链接投资备忘录草稿、尽调问题清单、项目资料解析报告、财务模型解析报告、关键假设确认报告、基础估值计算报告、多模型估值对比报告。"
    return "\n".join(rows)


def watchlist_row_from_tracking(tracking_record: dict[str, Any]) -> dict[str, str]:
    card = tracking_record.get("project_card", {})
    project = tracking_record.get("target_name", "未命名项目")
    return {
        "项目": project,
        "所属行业": card.get("industry", ""),
        "所属生态": card.get("rachel_ecosystem", ""),
        "标的类型": card.get("target_type", ""),
        "项目状态": tracking_record.get("project_status", ""),
        "观察池状态": tracking_record.get("watchlist_status", ""),
        "研究动作": tracking_record.get("research_action", ""),
        "估值置信度": card.get("valuation_confidence", ""),
        "下次复查日期": tracking_record.get("next_review_date", ""),
        "项目卡片": f"[[{project}]]",
    }


def watchlist_rows_from_markdown(content: str) -> list[dict[str, str]]:
    columns = ["项目", "所属行业", "所属生态", "标的类型", "项目状态", "观察池状态", "研究动作", "估值置信度", "下次复查日期", "项目卡片"]
    rows = []
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or "---" in stripped or "项目 | 所属行业" in stripped:
            continue
        cells = [cell.strip().replace("\\|", "|") for cell in stripped.strip("|").split("|")]
        if len(cells) == len(columns):
            rows.append(dict(zip(columns, cells)))
    return rows


def watchlist_group(rows: list[dict[str, str]], status: str) -> str:
    names = [row.get("项目", "") for row in rows if row.get("观察池状态") == status]
    return bullet_list([f"[[{name}]]" for name in names]) if names else "- 暂无"


def watchlist_groups(rows: list[dict[str, str]], statuses: list[str]) -> str:
    names = [row.get("项目", "") for row in rows if row.get("观察池状态") in statuses]
    return bullet_list([f"[[{name}]]" for name in names]) if names else "- 暂无"


def watchlist_due_soon(rows: list[dict[str, str]], created: date) -> str:
    due = []
    for row in rows:
        next_date = row.get("下次复查日期", "")
        try:
            parsed = date.fromisoformat(next_date)
        except ValueError:
            continue
        if parsed <= created or (parsed - created).days <= 7:
            due.append(f"{row.get('项目', '')}：{next_date}")
    return bullet_list(due) if due else "- 暂无"


def target_profile_fields_markdown(target_profile: dict[str, Any]) -> str:
    rows = []
    for key, label in target_profile_labels().items():
        payload = target_profile.get(key, {})
        rows.append(
            {
                "字段": label,
                "系统识别值": payload.get("detected_value", ""),
                "用户确认值": payload.get("confirmed_value", ""),
                "来源": payload.get("source", ""),
                "可信度": payload.get("confidence", ""),
                "是否需要确认": "是" if payload.get("needs_confirmation") else "否",
                "备注": payload.get("notes", ""),
            }
        )
    return markdown_table(rows, ["字段", "系统识别值", "用户确认值", "来源", "可信度", "是否需要确认", "备注"])


def target_profile_detected_summary(target_profile: dict[str, Any]) -> str:
    rows = [{"字段": label, "系统识别值": target_profile.get(key, {}).get("detected_value", "")} for key, label in target_profile_labels().items()]
    return markdown_table(rows, ["字段", "系统识别值"])


def target_profile_confirmed_summary(target_profile: dict[str, Any]) -> str:
    rows = [{"字段": label, "用户确认值": target_profile.get(key, {}).get("confirmed_value", "")} for key, label in target_profile_labels().items()]
    return markdown_table(rows, ["字段", "用户确认值"])


def target_profile_field(target_profile: dict[str, Any], key: str) -> str:
    payload = target_profile.get(key, {})
    return str(payload.get("confirmed_value") or payload.get("detected_value") or "")


def target_profile_labels() -> dict[str, str]:
    return {
        "target_name": "标的名称",
        "target_type": "标的类型",
        "industry": "所属行业",
        "rachel_ecosystem": "所属 Rachel 战略生态",
        "is_financing_or_secondary_transfer": "是否正在融资或老股转让",
        "is_complete_company": "是否为完整公司主体",
        "is_single_project_spv": "是否为单一项目 / SPV",
        "is_asset_based": "是否主要依赖资产、资源、牌照或合同",
        "has_revenue": "是否已有收入",
        "is_profitable": "是否盈利",
        "revenue_growth_status": "收入增长状态",
        "cash_flow_stability": "现金流是否稳定",
        "exit_path": "退出路径",
    }


def format_report_money(value: Any) -> str:
    if value is None:
        return "缺失"
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return str(value)
    if abs(numeric) >= 10000:
        return f"{numeric / 10000:.2f} 亿元"
    return f"{numeric:.2f} 万元"


def format_ratio(value: Any) -> str:
    if value is None:
        return "无法判断"
    try:
        return f"{float(value):.2f}x"
    except (TypeError, ValueError):
        return str(value)


def format_percent(value: Any) -> str:
    try:
        return f"{float(value):.1%}"
    except (TypeError, ValueError):
        return ""


def financial_model_supplement_markdown(financial_model: dict[str, Any] | None) -> str:
    if not financial_model:
        return "- 尚未上传 Excel / 财务模型。"
    extracted = financial_model.get("extracted_financial_data", {})
    return f"""- 已上传财务模型文件：{financial_model.get("file_name", "")}
- 已识别财务表类型：{', '.join(section for section, matches in financial_model.get("detected_financial_sections", {}).items() if matches) or "待确认"}
- 可用财务数据：{', '.join(extracted.get("usable_financial_data", [])) or "暂无"}
- 缺失财务数据：{', '.join(extracted.get("missing_financial_data", [])) or "暂无"}
- 需要用户确认的数据：{', '.join(extracted.get("requires_user_confirmation", [])) or "暂无"}
- 对估值模型选择的影响：{', '.join(extracted.get("supported_valuation_models", [])) or "待补充财务数据后确认"}

如果项目资料文本与 Excel / 财务模型数据存在冲突，请优先标记为“需要用户确认”，并向项目方追问口径、版本和数据来源。
"""
