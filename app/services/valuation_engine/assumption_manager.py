from __future__ import annotations

from copy import deepcopy
import re
from typing import Any


ASSUMPTION_GROUP_LABELS: dict[str, str] = {
    "project_basic": "项目基本假设",
    "financing_valuation": "融资与估值假设",
    "revenue": "收入假设",
    "cost_profit": "成本与利润假设",
    "cash_flow": "现金流假设",
    "capex_capacity": "CAPEX 与产能假设",
    "return_valuation": "回报与估值计算假设",
    "scenario_sensitivity": "情景与敏感性假设",
    "founder_team": "创始团队假设",
    "risk_missing_data": "风险与缺失数据假设",
}

VALUATION_INPUT_GROUPS = {
    "revenue",
    "cost_profit",
    "cash_flow",
    "capex_capacity",
    "return_valuation",
    "scenario_sensitivity",
}


def build_assumption_table(
    document_extraction: dict[str, Any] | None,
    financial_extraction: dict[str, Any] | None,
) -> dict[str, Any]:
    document_extraction = document_extraction or {}
    financial_extraction = financial_extraction or {}
    groups = {key: [] for key in ASSUMPTION_GROUP_LABELS}
    warnings: list[str] = []

    add_document_assumptions(groups, document_extraction)
    add_financial_assumptions(groups, financial_extraction)
    add_required_missing_assumptions(groups)

    target_name = target_name_from_sources(document_extraction, financial_extraction)
    source_files = source_files_from_sources(document_extraction, financial_extraction)
    readiness = score_valuation_readiness(groups)
    return {
        "target_name": target_name,
        "source_files": source_files,
        "assumption_groups": groups,
        "warnings": warnings,
        "readiness_summary": readiness,
        "ready_for_valuation_calculation": readiness["ready_for_v0_6_calculation"],
        "valuation_inputs": build_valuation_inputs(groups),
    }


def add_document_assumptions(groups: dict[str, list[dict[str, Any]]], extraction: dict[str, Any]) -> None:
    source_file = str(extraction.get("_source_file") or "")
    basic = extraction.get("project_basic_info", {})
    financing = extraction.get("financing_info", {})
    financial = extraction.get("financial_data", {})
    business = extraction.get("business_model", {})
    products = extraction.get("products_and_customers", {})
    capacity = extraction.get("capacity_data", {})
    cost = extraction.get("cost_structure", {})
    exit_path = extraction.get("exit_path", {})
    founder = extraction.get("founder_team", {})
    risks = extraction.get("risk_factors", {})
    readiness = extraction.get("valuation_readiness", {})

    add_many(groups, "project_basic", source_file, "文件明确披露", "中", [
        ("项目名称", basic.get("project_name")),
        ("公司名称", basic.get("company_name")),
        ("标的类型", basic.get("target_type_guess"), "", "", "系统推断", "中", True),
        ("所属行业", basic.get("industry"), "", "", "系统推断", "中", True),
        ("所属 Rachel 战略生态", basic.get("rachel_ecosystem_guess"), "", "", "系统推断", "中", True),
        ("项目阶段", basic.get("document_date")),
        ("地区", basic.get("location")),
        ("商业模式", business.get("revenue_sources") or basic.get("business_model")),
        ("收入模式", basic.get("business_model") or business.get("revenue_sources")),
    ])
    add_many(groups, "financing_valuation", source_file, "文件明确披露", "高", [
        ("本轮融资金额", financing.get("financing_amount")),
        ("投前估值", financing.get("pre_money_valuation")),
        ("投后估值", financing.get("post_money_valuation")),
        ("出让股权比例", financing.get("equity_offered")),
        ("上一轮估值", financing.get("previous_round")),
        ("上一轮融资时间", ""),
        ("资金用途", financing.get("use_of_proceeds")),
        ("退出路径", first_available(exit_path, ["ipo", "ma", "dividend_recovery", "asset_sale", "equity_transfer"])),
        ("预计退出时间", exit_path.get("expected_exit_time")),
    ])
    add_many(groups, "revenue", source_file, "文件明确披露", "中", [
        ("历史收入", financial.get("historical_revenue")),
        ("预测收入", financial.get("forecast_revenue")),
        ("收入增长率", ""),
        ("产品收入拆分", products.get("products")),
        ("客户收入拆分", products.get("customer_type")),
        ("单价", capacity.get("unit_price")),
        ("销量", ""),
        ("订单金额", products.get("orders")),
        ("合同金额", products.get("contracts")),
    ])
    add_many(groups, "cost_profit", source_file, "文件明确披露", "中", [
        ("毛利率", financial.get("gross_margin")),
        ("净利率", financial.get("net_margin")),
        ("EBITDA", financial.get("ebitda")),
        ("EBITDA Margin", ""),
        ("原材料成本", cost.get("raw_material_cost")),
        ("人工成本", cost.get("labor_cost")),
        ("能耗成本", cost.get("energy_cost")),
        ("研发费用", ""),
        ("销售费用", ""),
        ("管理费用", ""),
        ("财务费用", ""),
    ])
    add_many(groups, "cash_flow", source_file, "文件明确披露", "中", [
        ("经营现金流", financial.get("cash_flow")),
        ("自由现金流", ""),
        ("项目现金流", ""),
        ("累计现金流", ""),
        ("回款周期", ""),
        ("应收账款周期", ""),
        ("付款周期", ""),
    ])
    add_many(groups, "capex_capacity", source_file, "文件明确披露", "中", [
        ("项目总投资", financial.get("capex") or cost.get("capex")),
        ("CAPEX", financial.get("capex") or cost.get("capex")),
        ("建设周期", capacity.get("construction_period")),
        ("设计产能", capacity.get("designed_capacity")),
        ("当前产能", capacity.get("current_capacity")),
        ("在建产能", capacity.get("capacity_expansion_plan")),
        ("产能利用率", capacity.get("capacity_utilization")),
        ("产能爬坡节奏", capacity.get("capacity_expansion_plan")),
        ("单位产能投资", ""),
        ("设备投入", capacity.get("equipment_investment")),
    ])
    add_many(groups, "return_valuation", source_file, "系统推断", "低", [
        ("IRR", ""),
        ("NPV", ""),
        ("投资回收期", financial.get("payback_period")),
        ("折现率", ""),
        ("终值增长率", ""),
        ("退出倍数", ""),
        ("收入倍数", ""),
        ("利润倍数", ""),
        ("订单倍数", ""),
        ("流动性折扣", ""),
        ("技术成熟度折扣", ""),
        ("团队风险折扣", risks.get("team_risk")),
        ("退出路径折扣", ""),
    ])
    add_many(groups, "founder_team", source_file, "文件明确披露", "中", [
        ("创始人", founder.get("founders")),
        ("联合创始人", founder.get("co_founders")),
        ("核心高管", founder.get("core_executives")),
        ("技术负责人", founder.get("technical_lead")),
        ("商业负责人", founder.get("business_lead")),
        ("财务负责人", founder.get("finance_lead")),
        ("团队完整度", founder.get("team_completeness"), "", "", "系统推断", "中", True),
        ("关键人依赖", founder.get("key_person_dependency"), "", "", "系统推断", "中", True),
        ("产业经验", founder.get("industry_experience")),
        ("技术落地能力", founder.get("research_background") or founder.get("technical_lead")),
        ("商业化能力", founder.get("business_lead")),
        ("融资经验", founder.get("fundraising_experience")),
        ("团队风险", founder.get("team_risks"), "", "", "系统推断", "中", True),
    ])
    add_many(groups, "risk_missing_data", source_file, "系统推断", "中", [
        ("技术风险", risks.get("technology_risk")),
        ("市场风险", risks.get("market_risk")),
        ("客户风险", risks.get("customer_risk")),
        ("政策风险", risks.get("policy_risk")),
        ("融资风险", risks.get("financing_risk")),
        ("产能爬坡风险", risks.get("execution_risk")),
        ("回款风险", ""),
        ("团队风险", risks.get("team_risk")),
        ("数据真实性风险", risks.get("data_reliability_risk")),
        ("缺失数据", readiness.get("missing_data"), "", "", "系统推断", "中", True),
        ("需要向项目方追问的问题", readiness.get("questions_for_company"), "", "", "系统推断", "中", True),
    ])


def add_financial_assumptions(groups: dict[str, list[dict[str, Any]]], financial_model: dict[str, Any]) -> None:
    if not financial_model:
        return
    source_file = str(financial_model.get("file_name") or "")
    fields = financial_model.get("extracted_financial_data", {}).get("fields", {})
    financial_map = {
        "revenue": ["历史收入", "预测收入", "收入增长率", "产品收入拆分", "客户收入拆分", "单价", "销量"],
        "cost_profit": ["毛利", "毛利率", "净利润", "净利率", "EBITDA", "EBITDA Margin", "原材料成本", "人工成本", "能耗成本", "研发费用", "销售费用", "管理费用", "财务费用"],
        "cash_flow": ["经营现金流", "自由现金流", "项目现金流", "累计现金流"],
        "capex_capacity": ["项目总投资", "CAPEX", "建设周期", "设计产能", "当前产能", "产能利用率", "产能爬坡"],
        "financing_valuation": ["融资金额", "投前估值", "投后估值", "出让股权比例"],
        "return_valuation": ["IRR", "NPV", "回收期"],
        "scenario_sensitivity": ["保守情景", "中性情景", "乐观情景", "单价敏感性", "销量敏感性", "毛利率敏感性", "利用率敏感性", "折现率敏感性"],
    }
    field_aliases = {"融资金额": "本轮融资金额", "回收期": "投资回收期", "利用率敏感性": "产能利用率敏感性"}
    for group_key, field_names in financial_map.items():
        for field_name in field_names:
            payload = fields.get(field_name)
            if not payload:
                continue
            value = payload.get("extraction_result")
            if not has_value(value):
                continue
            groups[group_key].append(
                assumption_item(
                    field=field_aliases.get(field_name, field_name),
                    value=value,
                    source="Excel明确披露",
                    source_file=source_file,
                    source_location=payload.get("source_sheet") or payload.get("source_position") or "",
                    confidence=payload.get("confidence") or "高",
                    needs_confirmation=str(payload.get("needs_confirmation", "否")) == "是",
                )
            )


def add_required_missing_assumptions(groups: dict[str, list[dict[str, Any]]]) -> None:
    required = {
        "financing_valuation": ["退出路径"],
        "cash_flow": ["自由现金流", "项目现金流"],
        "capex_capacity": ["项目总投资", "CAPEX"],
        "return_valuation": ["折现率", "退出倍数", "流动性折扣"],
        "founder_team": ["财务负责人"],
    }
    for group_key, fields in required.items():
        existing = {item["field"] for item in groups[group_key] if has_value(item.get("extracted_value"))}
        for field in fields:
            if field not in existing:
                groups[group_key].append(assumption_item(field=field, value="", source="缺失", confidence="缺失"))


def add_many(
    groups: dict[str, list[dict[str, Any]]],
    group_key: str,
    source_file: str,
    default_source: str,
    default_confidence: str,
    rows: list[tuple[Any, ...]],
) -> None:
    for row in rows:
        field = str(row[0])
        value = row[1] if len(row) > 1 else ""
        source = row[4] if len(row) > 4 else default_source
        confidence = row[5] if len(row) > 5 else default_confidence
        needs_confirmation = row[6] if len(row) > 6 else source != "文件明确披露"
        groups[group_key].append(
            assumption_item(
                field=field,
                value=value,
                source=str(source),
                source_file=source_file,
                confidence=str(confidence),
                needs_confirmation=bool(needs_confirmation),
            )
        )


def assumption_item(
    field: str,
    value: Any,
    source: str,
    confidence: str,
    source_file: str = "",
    source_location: str = "",
    needs_confirmation: bool | None = None,
) -> dict[str, Any]:
    display = display_value(value)
    missing = not has_value(display)
    final_source = "缺失" if missing else source
    final_confidence = "缺失" if missing else confidence
    return {
        "field": field,
        "extracted_value": display if not missing else "缺失",
        "confirmed_value": "" if missing else display,
        "unit": guess_unit(display or field),
        "period": guess_period(display),
        "source": final_source,
        "source_file": source_file,
        "source_location": source_location,
        "confidence": final_confidence,
        "needs_confirmation": True if needs_confirmation is None else bool(needs_confirmation or missing),
        "use_in_valuation": not missing,
        "notes": "",
    }


def score_valuation_readiness(groups: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    required_fields = {
        "关键收入": has_confirmed(groups, "revenue", ["历史收入", "预测收入", "收入增长率"]),
        "成本或利润": has_confirmed(groups, "cost_profit", ["毛利率", "净利率", "EBITDA", "净利润"]),
        "现金流": has_confirmed(groups, "cash_flow", ["经营现金流", "自由现金流", "项目现金流"]),
        "CAPEX": has_confirmed(groups, "capex_capacity", ["项目总投资", "CAPEX"]),
        "融资估值": has_confirmed(groups, "financing_valuation", ["本轮融资金额", "投前估值", "投后估值", "出让股权比例"]),
        "退出路径": has_confirmed(groups, "financing_valuation", ["退出路径"]),
    }
    missing = [field for field, present in required_fields.items() if not present]
    if not missing:
        level = "高"
        reason = "关键收入、成本、现金流、CAPEX、融资估值和退出路径较完整。"
    elif required_fields["关键收入"] and required_fields["成本或利润"] and len(missing) <= 3:
        level = "中"
        reason = "收入和部分成本利润假设较完整，但现金流、CAPEX、融资估值或退出路径仍需补齐。"
    elif required_fields["关键收入"] or required_fields["融资估值"]:
        level = "低"
        reason = "已有部分商业或融资信息，但关键财务、现金流和退出假设不足。"
    else:
        level = "不足"
        reason = "目前主要是项目故事或定性信息，缺少进入估值计算的关键输入。"
    return {
        "valuation_readiness_level": level,
        "reason": reason,
        "ready_for_v0_6_calculation": level in {"高", "中"},
        "missing_before_calculation": missing,
    }


def build_valuation_inputs(groups: dict[str, list[dict[str, Any]]]) -> dict[str, dict[str, Any]]:
    inputs = {key: {} for key in VALUATION_INPUT_GROUPS}
    for group_key in VALUATION_INPUT_GROUPS:
        for item in groups.get(group_key, []):
            if item.get("use_in_valuation") and item.get("confidence") != "缺失" and has_value(item.get("confirmed_value")):
                inputs[group_key][item["field"]] = {
                    "confirmed_value": item.get("confirmed_value", ""),
                    "unit": item.get("unit", ""),
                    "period": item.get("period", ""),
                    "confidence": item.get("confidence", ""),
                    "source": item.get("source", ""),
                }
    return inputs


def finalize_assumption_data(assumption_data: dict[str, Any]) -> dict[str, Any]:
    data = deepcopy(assumption_data)
    groups = data.get("assumption_groups", {})
    readiness = score_valuation_readiness(groups)
    data["readiness_summary"] = readiness
    data["ready_for_valuation_calculation"] = readiness["ready_for_v0_6_calculation"]
    data["valuation_inputs"] = build_valuation_inputs(groups)
    return data


def flatten_assumptions(assumption_data: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for group_key, items in assumption_data.get("assumption_groups", {}).items():
        for item in items:
            rows.append({"group": group_key, "group_label": ASSUMPTION_GROUP_LABELS.get(group_key, group_key), **item})
    return rows


def assumption_counts(assumption_data: dict[str, Any]) -> dict[str, int]:
    rows = flatten_assumptions(assumption_data)
    return {
        "total": len(rows),
        "high": sum(1 for row in rows if row.get("confidence") == "高"),
        "medium": sum(1 for row in rows if row.get("confidence") == "中"),
        "low": sum(1 for row in rows if row.get("confidence") == "低"),
        "missing": sum(1 for row in rows if row.get("confidence") == "缺失"),
        "needs_confirmation": sum(1 for row in rows if row.get("needs_confirmation")),
        "usable": sum(1 for row in rows if row.get("use_in_valuation") and row.get("confidence") != "缺失"),
    }


def update_group_from_rows(group_items: list[dict[str, Any]], edited_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    updated = []
    for original, edited in zip(group_items, edited_rows):
        merged = {**original, **edited}
        merged["needs_confirmation"] = bool(merged.get("needs_confirmation"))
        merged["use_in_valuation"] = bool(merged.get("use_in_valuation"))
        updated.append(merged)
    return updated


def target_name_from_sources(document_extraction: dict[str, Any], financial_model: dict[str, Any]) -> str:
    basic = document_extraction.get("project_basic_info", {})
    if has_value(basic.get("project_name")):
        return str(basic.get("project_name"))
    if has_value(basic.get("company_name")):
        return str(basic.get("company_name"))
    file_name = str(financial_model.get("file_name") or "")
    return re.sub(r"[_\-\s]*(财务模型|财务预测|financial.?model|model)$", "", file_name.rsplit(".", 1)[0], flags=re.IGNORECASE) or "未命名项目"


def source_files_from_sources(document_extraction: dict[str, Any], financial_model: dict[str, Any]) -> list[dict[str, str]]:
    files = []
    if document_extraction.get("_source_file"):
        files.append({"file_name": str(document_extraction.get("_source_file")), "source_type": "项目资料"})
    if financial_model.get("file_name"):
        files.append({"file_name": str(financial_model.get("file_name")), "source_type": "财务模型"})
    return files


def has_confirmed(groups: dict[str, list[dict[str, Any]]], group_key: str, fields: list[str]) -> bool:
    for item in groups.get(group_key, []):
        if item.get("field") in fields and item.get("use_in_valuation") and item.get("confidence") != "缺失" and has_value(item.get("confirmed_value")):
            return True
    return False


def first_available(values: dict[str, Any], keys: list[str]) -> Any:
    for key in keys:
        if has_value(values.get(key)):
            return values.get(key)
    return ""


def display_value(value: Any) -> str:
    if isinstance(value, list):
        return "；".join(str(item) for item in value if str(item).strip())
    if isinstance(value, dict):
        return "；".join(f"{key}: {val}" for key, val in value.items() if has_value(val))
    if value is None:
        return ""
    return str(value).strip()


def has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    text = display_value(value)
    return bool(text) and text not in {"缺失", "未披露", "待确认", "None"}


def guess_unit(text: str) -> str:
    for unit in ["万元", "亿元", "%", "年", "月", "吨", "GW", "MW", "机柜", "家", "个"]:
        if unit in str(text):
            return unit
    return ""


def guess_period(text: str) -> str:
    match = re.search(r"20\d{2}(?:[AE])?", str(text))
    return match.group(0) if match else ""
