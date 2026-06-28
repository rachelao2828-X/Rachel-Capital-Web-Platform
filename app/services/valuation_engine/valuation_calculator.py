from __future__ import annotations

from datetime import date
import math
import re
from statistics import mean, median
from typing import Any


MODEL_ORDER = [
    "收入倍数法",
    "利润倍数法",
    "EBITDA 倍数法",
    "订单倍数法",
    "DCF 简化法",
    "IRR / 投资回收期校验",
    "资产重估 / 重置成本法",
]

DISCOUNT_FIELDS = {
    "流动性折扣": "流动性折扣",
    "技术成熟度折扣": "技术成熟度折扣",
    "团队风险折扣": "团队风险折扣",
    "退出路径折扣": "退出路径折扣",
    "信息透明度折扣": "信息透明度折扣",
}


def run_basic_private_market_valuation(assumption_data: dict[str, Any]) -> dict[str, Any]:
    target_name = assumption_data.get("target_name") or "未命名项目"
    readiness = assumption_data.get("readiness_summary", {})
    inputs = assumption_data.get("valuation_inputs") or build_inputs_from_groups(assumption_data.get("assumption_groups", {}))
    input_summary = summarize_inputs(inputs, readiness)
    warnings = list(assumption_data.get("warnings", []))
    if not assumption_data.get("ready_for_valuation_calculation", False):
        warnings.append("关键假设准备度不足或仍需确认，本次结果仅作为低置信度试算。")

    model_results = [
        revenue_multiple_model(inputs),
        profit_multiple_model(inputs),
        ebitda_multiple_model(inputs),
        order_multiple_model(inputs),
        simplified_dcf_model(inputs),
        irr_payback_check_model(inputs),
        asset_revaluation_model(inputs),
    ]
    discounts = extract_discounts(inputs)
    model_results = [apply_discount_to_model(result, discounts) for result in model_results]
    available_models = [result["model"] for result in model_results if result["status"] in {"可计算", "部分可计算"}]
    unavailable_models = [
        {"model": result["model"], "missing_fields": result["missing_fields"], "主要限制": result["main_limitations"]}
        for result in model_results
        if result["status"] == "不可计算"
    ]
    valuation_range = build_weighted_range(model_results)
    missing_data = collect_missing_data(model_results, readiness)
    confidence_level, confidence_reason = confidence_from_results(model_results, readiness, valuation_range)
    sensitivity_notes = build_sensitivity_notes(inputs, model_results)
    risk_adjustments = [
        {
            "折扣项": discount["name"],
            "折扣率": discount["rate_display"],
            "原因": discount["reason"],
            "是否应用": "是" if discount["applied"] else "否",
        }
        for discount in discounts
    ] or [{"折扣项": "未设置风险折扣", "折扣率": "", "原因": "当前未设置风险折扣，因此结果为未折扣估值。", "是否应用": "否"}]
    return {
        "target_name": target_name,
        "valuation_date": date.today().isoformat(),
        "input_summary": input_summary,
        "available_models": available_models,
        "unavailable_models": unavailable_models,
        "model_results": model_results,
        "valuation_range": valuation_range,
        "confidence_level": confidence_level,
        "confidence_reason": confidence_reason,
        "missing_data": missing_data,
        "sensitivity_notes": sensitivity_notes,
        "risk_adjustments": risk_adjustments,
        "warnings": warnings,
        "for_v0_7_multi_model_comparison": {
            "model_results": model_results,
            "valuation_range": valuation_range,
            "confidence_level": confidence_level,
            "weighting_candidates": [result["model"] for result in model_results if result.get("range_values") and result["confidence"] != "仅供框架参考"],
        },
    }


def revenue_multiple_model(inputs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    revenue = first_number(inputs, "revenue", ["预测收入", "历史收入"])
    multiples = scenario_multiples(inputs, ["收入倍数"], "收入倍数")
    if revenue and multiples:
        values = scenario_values(revenue, multiples)
        return model_result("收入倍数法", "可计算", "高" if len(values) >= 3 else "中", values, "预测收入或历史收入 × 收入倍数", "适用于收入可验证、利润尚未稳定的成长型业务。", missing=[])
    missing = []
    if not revenue:
        missing.append("预测收入或历史收入")
    if not multiples:
        missing.append("收入倍数或情景收入倍数")
    return unavailable_result("收入倍数法", missing)


def profit_multiple_model(inputs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    profit = first_number(inputs, "cost_profit", ["预测净利润", "净利润"])
    if not profit:
        net_margin = first_number(inputs, "cost_profit", ["净利率"])
        revenue = first_number(inputs, "revenue", ["预测收入", "历史收入"])
        if net_margin and revenue:
            profit = revenue * normalize_rate(net_margin)
    multiples = scenario_multiples(inputs, ["利润倍数", "净利润倍数"], "利润倍数")
    if profit and multiples:
        values = scenario_values(profit, multiples)
        return model_result("利润倍数法", "可计算", "中", values, "预测净利润 × 利润倍数", "利润口径需人工确认，若由净利率推导则置信度降低。", missing=[])
    missing = []
    if not profit:
        missing.append("预测净利润或净利率")
    if not multiples:
        missing.append("利润倍数或情景利润倍数")
    return unavailable_result("利润倍数法", missing)


def ebitda_multiple_model(inputs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    ebitda = first_number(inputs, "cost_profit", ["EBITDA"])
    multiples = scenario_multiples(inputs, ["EBITDA 倍数", "EBITDA倍数"], "EBITDA 倍数")
    if ebitda and multiples:
        values = scenario_values(ebitda, multiples)
        return model_result("EBITDA 倍数法", "可计算", "中", values, "EBITDA × EBITDA 倍数", "适用于 EBITDA 口径可靠且折旧影响较大的项目。", missing=[])
    missing = []
    if not ebitda:
        missing.append("EBITDA")
    if not multiples:
        missing.append("EBITDA 倍数")
    return unavailable_result("EBITDA 倍数法", missing)


def order_multiple_model(inputs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    order_amount = first_number(inputs, "revenue", ["订单金额", "合同金额"])
    multiples = scenario_multiples(inputs, ["订单倍数"], "订单倍数")
    if order_amount and multiples:
        values = scenario_values(order_amount, multiples)
        return model_result("订单倍数法", "可计算", "中", values, "订单金额或合同金额 × 订单倍数", "适用于订单已披露但利润尚未兑现的项目。", missing=[])
    missing = []
    if not order_amount:
        missing.append("订单金额或合同金额")
    if not multiples:
        missing.append("订单倍数")
    return unavailable_result("订单倍数法", missing)


def simplified_dcf_model(inputs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    cash_flow = first_number(inputs, "cash_flow", ["年度自由现金流", "自由现金流", "项目现金流", "经营现金流"])
    discount_rate = first_number(inputs, "return_valuation", ["折现率"])
    terminal_growth = first_number(inputs, "return_valuation", ["终值增长率"])
    forecast_years = int(first_number(inputs, "return_valuation", ["预测期"]) or 5)
    exit_value = first_number(inputs, "return_valuation", ["退出价值"])
    if cash_flow and discount_rate:
        rate = normalize_rate(discount_rate)
        growth = normalize_rate(terminal_growth) if terminal_growth else 0.0
        present_value = sum(cash_flow / ((1 + rate) ** year) for year in range(1, forecast_years + 1))
        if exit_value:
            present_value += exit_value / ((1 + rate) ** forecast_years)
        elif terminal_growth is not None and growth < rate:
            terminal_value = cash_flow * (1 + growth) / (rate - growth)
            present_value += terminal_value / ((1 + rate) ** forecast_years)
        values = {"base": present_value}
        values["low"] = present_value * 0.85
        values["high"] = present_value * 1.15
        return model_result("DCF 简化法", "可计算", "中", values, f"单一年现金流按 {forecast_years} 年折现", "若缺少年度现金流序列，本结果为简化估算。", missing=[])
    missing = []
    if not cash_flow:
        missing.append("年度自由现金流或项目现金流")
    if not discount_rate:
        missing.append("折现率")
    return unavailable_result("DCF 简化法", missing)


def irr_payback_check_model(inputs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    investment = first_number(inputs, "capex_capacity", ["项目总投资", "CAPEX"])
    cash_flow = first_number(inputs, "cash_flow", ["年现金流", "项目现金流", "自由现金流", "经营现金流"])
    disclosed_irr = first_number(inputs, "return_valuation", ["IRR"])
    disclosed_payback = first_number(inputs, "return_valuation", ["投资回收期"])
    if investment and cash_flow:
        payback = investment / cash_flow if cash_flow else None
        basis = f"项目总投资 / 年现金流，静态回收期约 {payback:.2f} 年" if payback else "项目总投资 / 年现金流"
        values = {"base": investment}
        return model_result("IRR / 投资回收期校验", "部分可计算", "仅供框架参考", values, basis, "本模型用于校验回收期，不单独形成企业价值结论。", missing=[])
    if disclosed_irr or disclosed_payback:
        values = {"base": investment or cash_flow or 0}
        result = model_result("IRR / 投资回收期校验", "部分可计算", "仅供框架参考", values, "展示已披露 IRR 或回收期", "缺少投资额与现金流，无法独立复算。", missing=[])
        result["主要依据"] = f"IRR: {display_number(disclosed_irr) if disclosed_irr else '缺失'}；回收期: {display_number(disclosed_payback) if disclosed_payback else '缺失'}"
        return result
    return unavailable_result("IRR / 投资回收期校验", ["项目总投资", "年现金流", "IRR 或投资回收期"])


def asset_revaluation_model(inputs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    book_value = first_number(inputs, "capex_capacity", ["资产账面价值"])
    replacement_cost = first_number(inputs, "capex_capacity", ["重置成本"])
    comparable_price = first_number(inputs, "capex_capacity", ["可比交易价格"])
    capacity_value = first_number(inputs, "capex_capacity", ["单位产能价值"])
    capacity_scale = first_number(inputs, "capex_capacity", ["产能规模", "设计产能", "当前产能"])
    values = {}
    basis = []
    if book_value:
        values["low"] = book_value
        basis.append("资产账面价值")
    if replacement_cost:
        values["base"] = replacement_cost
        basis.append("重置成本")
    if comparable_price:
        values["high"] = comparable_price
        basis.append("可比交易价格")
    if capacity_value and capacity_scale:
        values.setdefault("base", capacity_value * capacity_scale)
        basis.append("单位产能价值 × 产能规模")
    if values:
        if "base" not in values:
            values["base"] = median(values.values())
        values.setdefault("low", min(values.values()))
        values.setdefault("high", max(values.values()))
        return model_result("资产重估 / 重置成本法", "可计算", "中", values, "；".join(basis), "适用于资产权属、重置成本和可比交易口径清晰的资产型项目。", missing=[])
    return unavailable_result("资产重估 / 重置成本法", ["资产账面价值", "重置成本", "可比交易价格", "单位产能价值和产能规模"])


def model_result(model: str, status: str, confidence: str, values: dict[str, float], basis: str, limitations: str, missing: list[str]) -> dict[str, Any]:
    low = values.get("low", values.get("base"))
    base = values.get("base", median([value for value in values.values() if value is not None]))
    high = values.get("high", values.get("base"))
    return {
        "model": model,
        "status": status,
        "适用度": status,
        "input_completeness": input_completeness_from_missing(missing, bool(values)),
        "raw_valuation": format_range(low, base, high),
        "discounted_valuation": "",
        "confidence": confidence,
        "主要依据": basis,
        "main_limitations": limitations,
        "missing_fields": missing,
        "range_values": {"low": low, "base": base, "high": high},
    }


def unavailable_result(model: str, missing: list[str]) -> dict[str, Any]:
    return {
        "model": model,
        "status": "不可计算",
        "适用度": "不可计算",
        "input_completeness": "不足",
        "raw_valuation": "",
        "discounted_valuation": "",
        "confidence": "仅供框架参考",
        "主要依据": "",
        "main_limitations": "缺少必要输入：" + "、".join(missing),
        "missing_fields": missing,
        "range_values": {},
    }


def apply_discount_to_model(result: dict[str, Any], discounts: list[dict[str, Any]]) -> dict[str, Any]:
    if not result.get("range_values"):
        return result
    applied = [discount for discount in discounts if discount["applied"]]
    if not applied:
        result["discounted_valuation"] = result["raw_valuation"]
        return result
    factor = math.prod(1 - discount["rate"] for discount in applied)
    discounted = {key: value * factor for key, value in result["range_values"].items() if value is not None}
    result["discounted_range_values"] = discounted
    result["discounted_valuation"] = format_range(discounted.get("low"), discounted.get("base"), discounted.get("high"))
    return result


def build_weighted_range(model_results: list[dict[str, Any]]) -> dict[str, Any]:
    usable = [
        result.get("discounted_range_values") or result.get("range_values")
        for result in model_results
        if result.get("range_values") and result.get("confidence") != "仅供框架参考"
    ]
    usable = [item for item in usable if item]
    if len(usable) < 2:
        if len(usable) == 1:
            item = usable[0]
            return {"low": item.get("low"), "base": item.get("base"), "high": item.get("high"), "currency": "万元 RMB", "method": "single_model_reference", "display": format_range(item.get("low"), item.get("base"), item.get("high"))}
        return {"low": None, "base": None, "high": None, "currency": "万元 RMB", "method": "insufficient_models", "display": "可计算模型不足，暂不生成综合区间。"}
    lows = [item["low"] for item in usable if item.get("low") is not None]
    bases = [item["base"] for item in usable if item.get("base") is not None]
    highs = [item["high"] for item in usable if item.get("high") is not None]
    low = min(lows) if lows else None
    base = mean(bases) if bases else None
    high = max(highs) if highs else None
    return {"low": low, "base": base, "high": high, "currency": "万元 RMB", "method": "weighted_range", "display": format_range(low, base, high)}


def extract_discounts(inputs: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    discounts = []
    for field, label in DISCOUNT_FIELDS.items():
        value = first_number(inputs, "return_valuation", [field]) or first_number(inputs, "risk_missing_data", [field])
        if value is None:
            continue
        rate = normalize_rate(value)
        discounts.append({"name": label, "rate": rate, "rate_display": f"{rate:.1%}", "reason": "来自用户已确认关键假设", "applied": 0 <= rate < 1})
    return discounts


def build_inputs_from_groups(groups: dict[str, list[dict[str, Any]]]) -> dict[str, dict[str, Any]]:
    inputs: dict[str, dict[str, Any]] = {}
    for group_key, items in groups.items():
        inputs.setdefault(group_key, {})
        for item in items:
            if item.get("use_in_valuation") and item.get("confidence") != "缺失" and item.get("confirmed_value"):
                inputs[group_key][item["field"]] = {
                    "confirmed_value": item.get("confirmed_value", ""),
                    "unit": item.get("unit", ""),
                    "period": item.get("period", ""),
                    "confidence": item.get("confidence", ""),
                    "source": item.get("source", ""),
                }
    return inputs


def first_number(inputs: dict[str, dict[str, Any]], group: str, fields: list[str]) -> float | None:
    for field in fields:
        payload = inputs.get(group, {}).get(field)
        if not payload:
            continue
        number = parse_number(payload.get("confirmed_value"))
        if number is not None:
            return number
    return None


def scenario_multiples(inputs: dict[str, dict[str, Any]], fields: list[str], base_name: str) -> dict[str, float]:
    result: dict[str, float] = {}
    scenario_fields = {
        "low": [f"保守{base_name}", f"保守 {base_name}"],
        "base": [f"中性{base_name}", f"中性 {base_name}", *fields],
        "high": [f"乐观{base_name}", f"乐观 {base_name}"],
    }
    for scenario, names in scenario_fields.items():
        value = first_number(inputs, "return_valuation", names)
        if value is not None:
            result[scenario] = value
    if "base" in result:
        result.setdefault("low", result["base"])
        result.setdefault("high", result["base"])
    return result


def scenario_values(base_value: float, multiples: dict[str, float]) -> dict[str, float]:
    return {scenario: base_value * multiple for scenario, multiple in multiples.items()}


def parse_number(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).replace(",", "").replace("，", "").strip()
    if not text or text == "缺失":
        return None
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return None
    number = float(match.group(0))
    if "%" in text:
        return number / 100
    if "亿元" in text or "亿" in text:
        return number * 10000
    return number


def normalize_rate(value: float) -> float:
    if value > 1:
        return value / 100
    return value


def input_completeness_from_missing(missing: list[str], has_values: bool) -> str:
    if not has_values:
        return "不足"
    if not missing:
        return "高"
    if len(missing) <= 1:
        return "中"
    return "低"


def summarize_inputs(inputs: dict[str, dict[str, Any]], readiness: dict[str, Any]) -> dict[str, Any]:
    return {
        "valuation_readiness_level": readiness.get("valuation_readiness_level", "不足"),
        "ready_for_v0_6_calculation": readiness.get("ready_for_v0_6_calculation", False),
        "input_groups": {group: list(values.keys()) for group, values in inputs.items() if values},
    }


def collect_missing_data(model_results: list[dict[str, Any]], readiness: dict[str, Any]) -> list[str]:
    missing = []
    for result in model_results:
        missing.extend(result.get("missing_fields", []))
    missing.extend(readiness.get("missing_before_calculation", []))
    return dedupe(missing)


def confidence_from_results(model_results: list[dict[str, Any]], readiness: dict[str, Any], valuation_range: dict[str, Any]) -> tuple[str, str]:
    calculable = [result for result in model_results if result["status"] == "可计算"]
    readiness_level = readiness.get("valuation_readiness_level", "不足")
    if valuation_range.get("method") == "weighted_range" and len(calculable) >= 2 and readiness_level == "高":
        return "高", "至少两个模型可计算，且关键假设准备度较高。"
    if calculable and readiness_level in {"高", "中"}:
        return "中", "已有模型可计算，但部分关键数据仍需确认。"
    if calculable:
        return "低", "可计算模型较少或估值准备度偏低，结果仅作为初步研究参考。"
    return "仅供框架参考", "缺少关键输入，当前结果不能形成可靠估值区间。"


def build_sensitivity_notes(inputs: dict[str, dict[str, Any]], model_results: list[dict[str, Any]]) -> list[str]:
    notes = []
    if any(result["model"] == "收入倍数法" and result["status"] != "不可计算" for result in model_results):
        notes.append("收入倍数法对预测收入和倍数假设高度敏感，请确认收入口径、期间和可比样本。")
    if any(result["model"] == "DCF 简化法" and result["status"] != "不可计算" for result in model_results):
        notes.append("DCF 简化法对折现率、现金流稳定性和终值假设高度敏感。")
    if not extract_discounts(inputs):
        notes.append("当前未设置风险折扣，因此结果为未折扣估值。")
    return notes or ["请补充情景倍数、折扣率和敏感性假设，以提升估值区间解释力。"]


def format_range(low: float | None, base: float | None, high: float | None) -> str:
    if low is None and base is None and high is None:
        return ""
    if low == base == high:
        return format_money(base)
    return f"{format_money(low)} / {format_money(base)} / {format_money(high)}"


def format_money(value: float | None) -> str:
    if value is None:
        return "缺失"
    if abs(value) >= 10000:
        return f"{value / 10000:.2f} 亿元"
    return f"{value:.2f} 万元"


def display_number(value: float | None) -> str:
    if value is None:
        return "缺失"
    return f"{value:g}"


def dedupe(items: list[str]) -> list[str]:
    seen = set()
    result = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result
