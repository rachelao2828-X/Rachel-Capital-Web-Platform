from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from app.services.valuation_engine.model_registry import (
    ECOSYSTEM_OPTIONS,
    EXIT_PATHS,
    FINANCING_ROUNDS,
    PRIVATE_REVENUE_GROWTH,
    PRIVATE_TARGET_TYPES,
)


DISCLOSED_BOOLEAN_TRUE = {"是", "是，需核验", "true", "True", True}


def build_private_market_autofill_from_document(extraction: dict[str, Any]) -> dict[str, Any]:
    summary = extraction.get("project_basic_info", {})
    financing = extraction.get("financing_info", {})
    financial = extraction.get("financial_data", {})
    business_model = extraction.get("business_model", {})
    product_and_customers = extraction.get("products_and_customers", {})
    capacity = extraction.get("capacity_data", {})
    cost = extraction.get("cost_structure", {})
    exit_path = extraction.get("exit_path", {})
    readiness = extraction.get("valuation_readiness", {})

    target_type = normalize_option(summary.get("target_type_guess"), PRIVATE_TARGET_TYPES)
    values: dict[str, Any] = {}
    put(values, "target_name", summary.get("project_name") or summary.get("company_name"))
    put(values, "initial_type", target_type)
    put(values, "industry", blank_if_pending(summary.get("industry")))
    put(values, "ecosystem", normalize_option(summary.get("rachel_ecosystem_guess"), ECOSYSTEM_OPTIONS))

    is_financing = financing.get("is_fundraising")
    values["is_financing_or_transfer"] = bool(is_financing) or has_any(
        financing,
        ["financing_stage", "pre_money_valuation", "post_money_valuation", "financing_amount", "equity_offered"],
    )
    values["is_single_project_spv"] = target_type == "项目公司 / SPV" or truthy_text(business_model.get("is_project_based"))
    values["is_asset_or_contract_based"] = target_type == "资产型项目" or truthy_text(
        business_model.get("is_asset_or_resource_driven")
    ) or has_any(capacity, ["designed_capacity", "current_capacity", "production_base", "equipment_investment"])
    values["is_complete_company"] = target_type not in {"项目公司 / SPV", "资产型项目"}
    values["has_revenue"] = has_any(financial, ["historical_revenue", "forecast_revenue"]) or "收入" in readiness.get(
        "usable_data", []
    )
    values["is_profitable"] = has_any(financial, ["net_margin", "ebitda"]) or has_positive_profit_text(financial)
    values["revenue_growth_status"] = infer_revenue_growth(financial, readiness)
    values["cash_flow_stable"] = has_any(financial, ["cash_flow"]) or has_any(product_and_customers, ["contracts"])
    put(values, "exit_path", infer_exit_path(exit_path))

    put(values, "financing_round", normalize_financing_round(financing.get("financing_stage")))
    put(values, "pre_money_valuation", financing.get("pre_money_valuation"))
    put(values, "post_money_valuation", financing.get("post_money_valuation"))
    put(values, "financing_amount", financing.get("financing_amount"))
    put(values, "equity_sold", financing.get("equity_offered"))
    put(values, "previous_round_valuation", financing.get("previous_round"))

    put(values, "project_total_investment", financial.get("capex") or cost.get("capex"))
    put(values, "construction_period", capacity.get("construction_period"))
    put(values, "expected_revenue", financial.get("forecast_revenue") or financial.get("historical_revenue"))
    put(values, "expected_gross_margin", financial.get("gross_margin"))
    put(values, "expected_net_margin", financial.get("net_margin"))
    put(values, "annual_cash_flow", financial.get("cash_flow"))
    put(values, "payback_period", financial.get("payback_period"))
    put(values, "utilization_rate", capacity.get("capacity_utilization"))
    values["key_contract_signed"] = bool(product_and_customers.get("contracts"))

    put(values, "asset_type", infer_asset_type(summary, business_model, capacity))
    put(values, "book_value", cost.get("asset_book_value"))
    put(values, "replacement_cost", cost.get("replacement_cost"))
    values["asset_generates_cash_flow"] = values["cash_flow_stable"]
    values["asset_has_long_contract"] = bool(product_and_customers.get("contracts"))
    return remove_empty(values)


def build_private_market_autofill_from_financial_model(financial_model: dict[str, Any]) -> dict[str, Any]:
    values: dict[str, Any] = {}
    put(values, "target_name", project_name_from_financial_filename(financial_model.get("file_name", "")))
    put(values, "pre_money_valuation", financial_field(financial_model, "投前估值"))
    put(values, "post_money_valuation", financial_field(financial_model, "投后估值"))
    put(values, "financing_amount", financial_field(financial_model, "融资金额"))
    put(values, "equity_sold", financial_field(financial_model, "出让股权比例"))
    put(values, "project_total_investment", financial_field(financial_model, "项目总投资") or financial_field(financial_model, "CAPEX"))
    put(values, "construction_period", financial_field(financial_model, "建设周期"))
    put(values, "expected_revenue", financial_field(financial_model, "预测收入") or financial_field(financial_model, "历史收入"))
    put(values, "expected_gross_margin", financial_field(financial_model, "毛利率"))
    put(values, "expected_net_margin", financial_field(financial_model, "净利率"))
    put(
        values,
        "annual_cash_flow",
        financial_field(financial_model, "项目现金流")
        or financial_field(financial_model, "自由现金流")
        or financial_field(financial_model, "经营现金流"),
    )
    put(values, "payback_period", financial_field(financial_model, "回收期"))
    put(values, "utilization_rate", financial_field(financial_model, "产能利用率"))

    has_revenue = bool(financial_field(financial_model, "历史收入") or financial_field(financial_model, "预测收入"))
    has_project_cash_flow = bool(
        financial_field(financial_model, "项目现金流")
        or financial_field(financial_model, "自由现金流")
        or financial_field(financial_model, "经营现金流")
    )
    has_project_metrics = bool(
        financial_field(financial_model, "项目总投资")
        or financial_field(financial_model, "IRR")
        or financial_field(financial_model, "回收期")
    )
    has_capacity = bool(
        financial_field(financial_model, "设计产能")
        or financial_field(financial_model, "当前产能")
        or financial_field(financial_model, "产能利用率")
    )

    values["has_revenue"] = has_revenue
    values["is_profitable"] = bool(
        financial_field(financial_model, "净利润")
        or financial_field(financial_model, "净利率")
        or financial_field(financial_model, "EBITDA")
    )
    values["cash_flow_stable"] = has_project_cash_flow
    values["revenue_growth_status"] = "高增长" if financial_field(financial_model, "收入增长率") else ("稳定增长" if has_revenue else "尚无收入")
    if has_project_metrics:
        values["initial_type"] = "项目公司 / SPV"
        values["is_single_project_spv"] = True
        values["is_complete_company"] = False
    if financial_field(financial_model, "融资金额") or financial_field(financial_model, "投前估值") or financial_field(financial_model, "投后估值"):
        values["is_financing_or_transfer"] = True
    if has_capacity:
        values["is_asset_or_contract_based"] = True
        values["asset_generates_cash_flow"] = has_project_cash_flow
    return remove_empty(values)


def financial_field(financial_model: dict[str, Any], field: str) -> str:
    value = (
        financial_model.get("extracted_financial_data", {})
        .get("fields", {})
        .get(field, {})
        .get("extraction_result", "")
    )
    value = str(value).strip()
    return "" if not value or value == "缺失" else value


def infer_exit_path(exit_path: dict[str, Any]) -> str:
    if has_value(exit_path.get("ipo")):
        return "IPO"
    if has_value(exit_path.get("ma")) or has_value(exit_path.get("strategic_acquisition")):
        return "并购"
    if has_value(exit_path.get("dividend_recovery")):
        return "分红回收"
    if has_value(exit_path.get("asset_sale")):
        return "资产出售"
    return "不确定"


def infer_revenue_growth(financial: dict[str, Any], readiness: dict[str, Any]) -> str:
    if "收入" in readiness.get("missing_data", []) and not has_any(financial, ["historical_revenue", "forecast_revenue"]):
        return "尚无收入"
    if has_value(financial.get("forecast_revenue")):
        return "高增长"
    if has_value(financial.get("historical_revenue")):
        return "稳定增长"
    return PRIVATE_REVENUE_GROWTH[0]


def normalize_financing_round(value: Any) -> str:
    text = str(value or "")
    for option in FINANCING_ROUNDS:
        if option.lower() in text.lower():
            return option
    return ""


def normalize_option(value: Any, options: list[str]) -> str:
    text = str(value or "").strip()
    if text in options:
        return text
    for option in options:
        if text and (text in option or option in text):
            return option
    return ""


def project_name_from_financial_filename(file_name: str) -> str:
    stem = Path(str(file_name or "")).stem
    stem = re.sub(r"^\d{8}_\d{6}_", "", stem)
    stem = re.sub(r"[_\-\s]*(财务模型|财务预测|项目测算表|financial.?model|model)$", "", stem, flags=re.IGNORECASE)
    return stem.strip("_- ")[:80]


def infer_asset_type(summary: dict[str, Any], business_model: dict[str, Any], capacity: dict[str, Any]) -> str:
    text = " ".join(str(item or "") for item in [summary.get("industry"), summary.get("one_sentence_summary"), business_model.get("business_model"), capacity.get("production_base")])
    if any(keyword in text for keyword in ["算力", "数据中心", "机柜"]):
        return "算力 / 数据中心资产"
    if any(keyword in text for keyword in ["储能", "光伏", "风电"]):
        return "新能源资产"
    if any(keyword in text for keyword in ["产线", "工厂", "设备"]):
        return "产能 / 设备资产"
    return ""


def has_positive_profit_text(financial: dict[str, Any]) -> bool:
    text = " ".join(str(financial.get(key, "")) for key in ["net_margin", "ebitda"])
    return bool(text and not any(keyword in text for keyword in ["亏损", "负", "缺失"]))


def has_any(values: dict[str, Any], keys: list[str]) -> bool:
    return any(has_value(values.get(key)) for key in keys)


def truthy_text(value: Any) -> bool:
    return value in DISCLOSED_BOOLEAN_TRUE or str(value).strip() in DISCLOSED_BOOLEAN_TRUE


def has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, list):
        return bool(value)
    if isinstance(value, bool):
        return value
    return bool(str(value).strip()) and str(value).strip() not in {"待确认", "未披露", "缺失"}


def blank_if_pending(value: Any) -> str:
    text = str(value or "").strip()
    return "" if text in {"待确认", "未披露", "缺失"} else text


def put(values: dict[str, Any], key: str, value: Any) -> None:
    if has_value(value):
        values[key] = value


def remove_empty(values: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in values.items() if isinstance(value, bool) or has_value(value)}
