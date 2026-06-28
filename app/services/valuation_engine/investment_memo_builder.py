from __future__ import annotations

from datetime import date, timedelta
from typing import Any


ALLOWED_RESEARCH_ACTIONS = {
    "进入观察池",
    "需要补充数据",
    "进入深度研究",
    "暂不进入估值",
    "等待更多财务或项目数据",
}

MODULE_LABELS = {
    "target_profile": "标的基本信息确认",
    "document_extraction": "项目资料解析",
    "financial_extraction": "财务模型解析",
    "assumption_confirmation": "关键假设确认",
    "basic_valuation_result": "基础估值计算",
    "multi_model_result": "多模型估值对比",
}


def build_private_market_investment_memo(
    document_extraction: dict[str, Any] | None,
    financial_extraction: dict[str, Any] | None,
    assumption_confirmation: dict[str, Any] | None,
    basic_valuation_result: dict[str, Any] | None,
    multi_model_result: dict[str, Any] | None,
    target_profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    document_extraction = normalize_document_extraction(document_extraction)
    financial_extraction = normalize_financial_extraction(financial_extraction)
    target_profile = target_profile or (assumption_confirmation or {}).get("target_profile") or (basic_valuation_result or {}).get("target_profile") or (multi_model_result or {}).get("target_profile") or {}
    input_status = build_input_status(document_extraction, financial_extraction, assumption_confirmation, basic_valuation_result, multi_model_result, target_profile)
    target_name = target_profile_value(target_profile, "target_name") or infer_target_name(document_extraction, financial_extraction, assumption_confirmation, basic_valuation_result, multi_model_result)
    project_snapshot = build_project_snapshot(document_extraction, assumption_confirmation, multi_model_result, target_profile)
    founder_team_review = build_founder_team_review(document_extraction)
    business_model_review = build_business_model_review(document_extraction)
    technology_review = build_technology_review(document_extraction)
    product_customer_review = build_product_customer_review(document_extraction)
    market_competition_review = build_market_competition_review(document_extraction)
    financial_review = build_financial_review(document_extraction, financial_extraction, assumption_confirmation)
    financing_valuation_review = build_financing_valuation_review(document_extraction, assumption_confirmation, basic_valuation_result, multi_model_result)
    valuation_summary = build_valuation_summary(basic_valuation_result, multi_model_result)
    risk_summary = build_risk_summary(document_extraction, multi_model_result)
    data_gaps = build_data_gaps(document_extraction, financial_extraction, assumption_confirmation, basic_valuation_result, multi_model_result, input_status)
    due_diligence_questions = build_due_diligence_questions(document_extraction, financial_extraction, assumption_confirmation, data_gaps)
    memo_completeness, completeness_reason = memo_completeness_from_inputs(input_status, project_snapshot, financial_review, financing_valuation_review)
    research_action = build_research_action(memo_completeness, data_gaps, multi_model_result, risk_summary)
    warnings = build_warnings(input_status, memo_completeness, data_gaps)
    next_review_date = (date.today() + timedelta(days=30)).isoformat()
    questions_for_company = [item["question"] for item in due_diligence_questions[:20]]
    follow_up_tasks = research_action["next_steps"] + [f"补充：{item}" for item in data_gaps[:8]]

    return {
        "target_name": target_name,
        "target_profile": target_profile,
        "memo_date": date.today().isoformat(),
        "input_status": input_status,
        "memo_completeness": memo_completeness,
        "memo_completeness_reason": completeness_reason,
        "project_snapshot": project_snapshot,
        "founder_team_review": founder_team_review,
        "business_model_review": business_model_review,
        "technology_review": technology_review,
        "product_customer_review": product_customer_review,
        "market_competition_review": market_competition_review,
        "financial_review": financial_review,
        "financing_valuation_review": financing_valuation_review,
        "valuation_summary": valuation_summary,
        "risk_summary": risk_summary,
        "due_diligence_questions": due_diligence_questions,
        "data_gaps": data_gaps,
        "research_action": research_action,
        "warnings": warnings,
        "for_v0_9_project_tracking": {
            "target_name": target_name,
            "research_action": research_action["suggested_action"],
            "follow_up_tasks": follow_up_tasks,
            "data_gaps": data_gaps,
            "questions_for_company": questions_for_company,
            "next_review_date": next_review_date,
            "watchlist_status": watchlist_status_from_action(research_action["suggested_action"]),
        },
    }


def normalize_document_extraction(payload: dict[str, Any] | None) -> dict[str, Any]:
    if not payload:
        return {}
    if "extraction" in payload and isinstance(payload["extraction"], dict):
        return payload["extraction"]
    return payload


def normalize_financial_extraction(payload: dict[str, Any] | None) -> dict[str, Any]:
    if not payload:
        return {}
    return payload


def target_profile_value(target_profile: dict[str, Any] | None, key: str) -> str:
    payload = (target_profile or {}).get(key, {})
    if isinstance(payload, dict) and has_value(payload.get("confirmed_value")):
        return str(payload.get("confirmed_value"))
    return ""


def build_input_status(
    document_extraction: dict[str, Any],
    financial_extraction: dict[str, Any],
    assumption_confirmation: dict[str, Any] | None,
    basic_valuation_result: dict[str, Any] | None,
    multi_model_result: dict[str, Any] | None,
    target_profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    modules = {
        "target_profile": bool(target_profile),
        "document_extraction": bool(document_extraction),
        "financial_extraction": bool(financial_extraction),
        "assumption_confirmation": bool(assumption_confirmation),
        "basic_valuation_result": bool(basic_valuation_result),
        "multi_model_result": bool(multi_model_result),
    }
    loaded = [MODULE_LABELS[key] for key, value in modules.items() if value]
    missing = [MODULE_LABELS[key] for key, value in modules.items() if not value]
    return {
        "modules": modules,
        "loaded_modules": loaded,
        "missing_modules": missing,
        "quality_impact": quality_impact_from_modules(modules),
    }


def memo_completeness_from_inputs(
    input_status: dict[str, Any],
    project_snapshot: dict[str, Any],
    financial_review: dict[str, Any],
    financing_valuation_review: dict[str, Any],
) -> tuple[str, str]:
    modules = input_status["modules"]
    core_modules = {key: value for key, value in modules.items() if key != "target_profile"}
    if all(core_modules.values()):
        return "高", "项目资料、财务模型、关键假设、基础估值和多模型估值均已读取。"
    if modules["document_extraction"] and modules["assumption_confirmation"] and (modules["basic_valuation_result"] or modules["multi_model_result"]):
        return "中", "已具备项目资料、关键假设和至少一种估值结果，但仍缺少部分输入。"
    if modules["document_extraction"] or modules["financial_extraction"] or modules["assumption_confirmation"]:
        return "低", "只读取到部分基础资料，可以生成低完整度 Memo 草稿。"
    has_snapshot = any(has_value(value) for value in project_snapshot.values())
    has_finance = any(has_value(value) for value in financial_review.values())
    has_valuation = any(has_value(value) for value in financing_valuation_review.values())
    if not has_snapshot and not has_finance and not has_valuation:
        return "不足", "缺少项目摘要、财务数据、融资信息和估值结果，无法形成有效 Memo。"
    return "低", "输入模块不完整，Memo 只能作为低完整度草稿。"


def build_project_snapshot(
    document_extraction: dict[str, Any],
    assumption_confirmation: dict[str, Any] | None,
    multi_model_result: dict[str, Any] | None,
    target_profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    basic = document_extraction.get("project_basic_info", {})
    financing = document_extraction.get("financing_info", {})
    return {
        "项目名称": first_value(target_profile_value(target_profile, "target_name"), basic.get("project_name"), assumption_confirmation.get("target_name") if assumption_confirmation else None, multi_model_result.get("target_name") if multi_model_result else None),
        "公司名称": basic.get("company_name"),
        "所属行业": target_profile_value(target_profile, "industry") or basic.get("industry") or assumption_value(assumption_confirmation, "project_basic", "所属行业"),
        "所属 Rachel 战略生态": target_profile_value(target_profile, "rachel_ecosystem") or basic.get("rachel_ecosystem_guess") or assumption_value(assumption_confirmation, "project_basic", "所属 Rachel 战略生态"),
        "标的类型": target_profile_value(target_profile, "target_type") or basic.get("target_type_guess") or assumption_value(assumption_confirmation, "project_basic", "标的类型") or (multi_model_result or {}).get("target_type"),
        "项目阶段": basic.get("document_date") or assumption_value(assumption_confirmation, "project_basic", "项目阶段"),
        "地区": basic.get("location") or assumption_value(assumption_confirmation, "project_basic", "地区"),
        "一句话摘要": basic.get("one_sentence_summary"),
        "当前融资状态": financing.get("is_fundraising"),
        "本轮融资金额": financing.get("financing_amount") or assumption_value(assumption_confirmation, "financing_valuation", "本轮融资金额"),
        "投前估值": financing.get("pre_money_valuation") or assumption_value(assumption_confirmation, "financing_valuation", "投前估值"),
        "投后估值": financing.get("post_money_valuation") or assumption_value(assumption_confirmation, "financing_valuation", "投后估值"),
        "出让股权比例": financing.get("equity_offered") or assumption_value(assumption_confirmation, "financing_valuation", "出让股权比例"),
    }


def build_founder_team_review(document_extraction: dict[str, Any]) -> dict[str, Any]:
    founder = document_extraction.get("founder_team", {})
    return {
        "创始人 / 联合创始人": join_values(founder.get("founders"), founder.get("co_founders")),
        "核心高管": founder.get("core_executives"),
        "技术负责人": founder.get("technical_lead"),
        "商业负责人": founder.get("business_lead"),
        "财务负责人": founder.get("finance_lead"),
        "团队背景": join_values(founder.get("education_background"), founder.get("big_company_background")),
        "产业经验": founder.get("industry_experience"),
        "技术落地能力": founder.get("research_background") or founder.get("technical_lead"),
        "商业化能力": founder.get("business_lead"),
        "融资经验": founder.get("fundraising_experience"),
        "团队完整度": founder.get("team_completeness"),
        "关键人依赖": founder.get("key_person_dependency"),
        "团队风险": founder.get("team_risks"),
    }


def build_business_model_review(document_extraction: dict[str, Any]) -> dict[str, Any]:
    business = document_extraction.get("business_model", {})
    return {
        "收入来源": business.get("revenue_sources"),
        "客户类型": business.get("customer_type"),
        "付费模式": business.get("payment_model"),
        "是否项目制": business.get("is_project_based"),
        "是否产品化": business.get("is_productized"),
        "是否平台型": business.get("is_platform_based"),
        "是否资产/资源驱动": business.get("is_asset_or_resource_driven"),
        "是否依赖政府订单或大客户": business.get("depends_on_government_or_key_customers"),
        "商业模式可复制性": infer_copyability(business),
        "商业模式风险": business_model_risk(business),
    }


def build_technology_review(document_extraction: dict[str, Any]) -> dict[str, Any]:
    technology = document_extraction.get("technology_route", {})
    risks = document_extraction.get("risk_factors", {})
    return {
        "核心技术": technology.get("core_technology"),
        "技术路线": technology.get("technical_route") or technology.get("core_technology"),
        "专利": technology.get("patents"),
        "工艺": technology.get("process"),
        "技术成熟度": technology.get("technical_maturity"),
        "是否已中试": contains_any(technology.get("technical_maturity"), ["中试"]),
        "是否已量产": contains_any(technology.get("technical_maturity"), ["量产", "规模化"]),
        "替代对象": technology.get("substitution_target"),
        "技术壁垒": technology.get("competitive_advantage"),
        "关键依赖": technology.get("key_dependencies"),
        "技术风险": risks.get("technology_risk"),
    }


def build_product_customer_review(document_extraction: dict[str, Any]) -> dict[str, Any]:
    product = document_extraction.get("products_and_customers", {})
    return {
        "主要产品": product.get("products"),
        "客户类型": product.get("customer_type"),
        "已签客户": product.get("signed_customers"),
        "意向客户": product.get("intended_customers"),
        "订单情况": product.get("orders"),
        "合同情况": product.get("contracts"),
        "客户集中度": product.get("customer_concentration"),
        "复购情况": product.get("repurchase"),
        "渠道情况": product.get("channels"),
        "客户验证强度": customer_validation_strength(product),
    }


def build_market_competition_review(document_extraction: dict[str, Any]) -> dict[str, Any]:
    market = document_extraction.get("market_space", {})
    return {
        "市场规模": market.get("market_size"),
        "市场增速": market.get("market_growth"),
        "TAM / SAM / SOM": market.get("tam_sam_som"),
        "竞争格局": market.get("competition_landscape"),
        "主要竞争对手": market.get("competitors"),
        "国产替代空间": market.get("domestic_substitution"),
        "政策驱动因素": market.get("policy_drivers"),
        "行业景气度": market.get("market_growth"),
        "市场空间可信度": "中" if has_value(market.get("market_size")) else "待补充",
    }


def build_financial_review(
    document_extraction: dict[str, Any],
    financial_extraction: dict[str, Any],
    assumption_confirmation: dict[str, Any] | None,
) -> dict[str, Any]:
    financial = document_extraction.get("financial_data", {})
    capacity = document_extraction.get("capacity_data", {})
    cost = document_extraction.get("cost_structure", {})
    fields = financial_extraction.get("extracted_financial_data", {}).get("fields", {})
    return {
        "历史收入": first_value(financial.get("historical_revenue"), field_value(fields, "历史收入"), assumption_value(assumption_confirmation, "revenue", "历史收入")),
        "预测收入": first_value(financial.get("forecast_revenue"), field_value(fields, "预测收入"), assumption_value(assumption_confirmation, "revenue", "预测收入")),
        "毛利率": first_value(financial.get("gross_margin"), field_value(fields, "毛利率"), assumption_value(assumption_confirmation, "cost_profit", "毛利率")),
        "净利率": first_value(financial.get("net_margin"), field_value(fields, "净利率"), assumption_value(assumption_confirmation, "cost_profit", "净利率")),
        "EBITDA": first_value(financial.get("ebitda"), field_value(fields, "EBITDA"), assumption_value(assumption_confirmation, "cost_profit", "EBITDA")),
        "现金流": first_value(financial.get("cash_flow"), field_value(fields, "项目现金流"), assumption_value(assumption_confirmation, "cash_flow", "自由现金流"), assumption_value(assumption_confirmation, "cash_flow", "项目现金流")),
        "CAPEX": first_value(financial.get("capex"), cost.get("capex"), field_value(fields, "CAPEX"), assumption_value(assumption_confirmation, "capex_capacity", "CAPEX")),
        "OPEX": first_value(financial.get("opex"), cost.get("opex")),
        "项目总投资": first_value(field_value(fields, "项目总投资"), assumption_value(assumption_confirmation, "capex_capacity", "项目总投资")),
        "产能": first_value(capacity.get("designed_capacity"), capacity.get("current_capacity")),
        "产能利用率": first_value(capacity.get("capacity_utilization"), field_value(fields, "产能利用率")),
        "回收期": first_value(financial.get("payback_period"), field_value(fields, "回收期"), assumption_value(assumption_confirmation, "return_valuation", "投资回收期")),
        "IRR": first_value(field_value(fields, "IRR"), assumption_value(assumption_confirmation, "return_valuation", "IRR")),
        "现金流质量": "待核验" if not has_value(financial.get("cash_flow")) else "需结合合同、回款和营运资金继续核验",
        "财务数据可信度": financial_confidence(financial_extraction, assumption_confirmation),
    }


def build_financing_valuation_review(
    document_extraction: dict[str, Any],
    assumption_confirmation: dict[str, Any] | None,
    basic_valuation_result: dict[str, Any] | None,
    multi_model_result: dict[str, Any] | None,
) -> dict[str, Any]:
    financing = document_extraction.get("financing_info", {})
    exit_path = document_extraction.get("exit_path", {})
    weighted_range = (multi_model_result or {}).get("weighted_valuation_range", {})
    dispersion = (multi_model_result or {}).get("model_dispersion", {})
    return {
        "本轮融资金额": first_value(financing.get("financing_amount"), assumption_value(assumption_confirmation, "financing_valuation", "本轮融资金额")),
        "投前估值": first_value(financing.get("pre_money_valuation"), assumption_value(assumption_confirmation, "financing_valuation", "投前估值")),
        "投后估值": first_value(financing.get("post_money_valuation"), assumption_value(assumption_confirmation, "financing_valuation", "投后估值")),
        "出让股权比例": first_value(financing.get("equity_offered"), assumption_value(assumption_confirmation, "financing_valuation", "出让股权比例")),
        "上一轮估值": first_value(financing.get("previous_round"), assumption_value(assumption_confirmation, "financing_valuation", "上一轮估值")),
        "上一轮投资人": financing.get("previous_investors"),
        "资金用途": financing.get("use_of_proceeds"),
        "退出路径": first_value(exit_path.get("ipo"), exit_path.get("ma"), exit_path.get("asset_sale"), assumption_value(assumption_confirmation, "financing_valuation", "退出路径")),
        "预计退出时间": exit_path.get("expected_exit_time"),
        "多模型估值区间": weighted_range.get("display") or (basic_valuation_result or {}).get("valuation_range", {}).get("display"),
        "模型分歧度": dispersion.get("dispersion_level"),
        "综合置信度": (multi_model_result or {}).get("confidence_level") or (basic_valuation_result or {}).get("confidence_level"),
        "估值限制": join_values((multi_model_result or {}).get("warnings"), (basic_valuation_result or {}).get("warnings")),
    }


def build_valuation_summary(
    basic_valuation_result: dict[str, Any] | None,
    multi_model_result: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "基础估值区间": (basic_valuation_result or {}).get("valuation_range", {}).get("display"),
        "多模型综合区间": (multi_model_result or {}).get("weighted_valuation_range", {}).get("display"),
        "综合置信度": (multi_model_result or {}).get("confidence_level") or (basic_valuation_result or {}).get("confidence_level"),
        "模型分歧度": (multi_model_result or {}).get("model_dispersion", {}).get("dispersion_level"),
        "主要分歧来源": (multi_model_result or {}).get("major_divergence_drivers", []),
        "敏感性提示": (multi_model_result or {}).get("sensitivity_notes") or (basic_valuation_result or {}).get("sensitivity_notes", []),
    }


def build_risk_summary(document_extraction: dict[str, Any], multi_model_result: dict[str, Any] | None) -> dict[str, Any]:
    risks = document_extraction.get("risk_factors", {})
    divergence = (multi_model_result or {}).get("major_divergence_drivers", [])
    return {
        "技术风险": risks.get("technology_risk"),
        "市场风险": risks.get("market_risk"),
        "客户风险": risks.get("customer_risk"),
        "政策风险": risks.get("policy_risk"),
        "融资风险": risks.get("financing_risk"),
        "执行风险": risks.get("execution_risk"),
        "产能爬坡风险": risks.get("execution_risk"),
        "回款风险": risks.get("collection_risk"),
        "团队风险": risks.get("team_risk"),
        "关键人风险": risks.get("key_person_risk"),
        "数据真实性风险": risks.get("data_reliability_risk"),
        "估值过高风险": next((item for item in divergence if "估值" in item), ""),
        "退出路径风险": risks.get("exit_risk"),
        "合规风险": risks.get("compliance_risk"),
    }


def build_due_diligence_questions(
    document_extraction: dict[str, Any],
    financial_extraction: dict[str, Any],
    assumption_confirmation: dict[str, Any] | None,
    data_gaps: list[str],
) -> list[dict[str, str]]:
    sections = {
        "团队尽调": [
            "请提供创始人及核心团队完整履历，并标注各自职责边界。",
            "请说明技术负责人是否具备相关产业落地经验及过往项目案例。",
            "请说明商业化负责人是否具备客户开拓、销售交付和渠道管理经验。",
            "请说明核心团队股权分配、激励安排和关键人员稳定性。",
            "请说明公司是否存在对单一创始人的强依赖。",
        ],
        "技术尽调": [
            "请提供核心技术路线、替代对象和当前技术成熟度证明。",
            "请说明当前处于实验室、中试、量产或规模化应用的哪个阶段。",
            "请提供专利、论文、技术认证或第三方测试报告。",
            "请说明关键技术依赖、供应链瓶颈和外部授权情况。",
            "请说明与竞品相比的核心优势、劣势和可验证指标。",
        ],
        "产品与客户尽调": [
            "请提供已签客户、意向客户和潜在客户清单，并区分客户阶段。",
            "请区分已签合同、框架协议、意向订单和口头意向。",
            "请提供前五大客户收入占比和客户集中度说明。",
            "请说明客户复购情况、合同周期和续约条件。",
            "请说明是否存在大客户依赖及替代客户储备。",
        ],
        "市场与竞争尽调": [
            "请提供 TAM、SAM、SOM 测算口径和第三方来源。",
            "请列示主要竞争对手、竞品价格、性能和客户覆盖情况。",
            "请说明国产替代、政策驱动或行业景气度对需求的影响。",
            "请说明市场增速假设和核心下游需求来源。",
            "请说明公司在产业链中的议价能力和竞争壁垒。",
        ],
        "财务尽调": [
            "请提供过去三年及未来三年的收入、成本、利润和现金流预测。",
            "请提供毛利率、净利率、EBITDA 及其计算口径。",
            "请提供 CAPEX、OPEX、折旧和营运资金假设。",
            "请说明收入预测对应的客户、订单或产能基础。",
            "请提供保守、中性、乐观三种财务情景。",
        ],
        "融资与股权结构尽调": [
            "请提供本轮投前估值、投后估值、融资金额和出让比例。",
            "请说明上一轮融资估值、融资时间和投资人。",
            "请说明本轮估值依据、资金用途和交割条件。",
            "请提供完整股权结构、期权池和历史融资协议关键条款。",
            "请提供可比融资交易或可比上市公司样本。",
        ],
        "法务与合规尽调": [
            "请提供公司主体、股权、知识产权和核心合同的法务清单。",
            "请说明是否存在诉讼、仲裁、行政处罚或重大合规事项。",
            "请说明业务所需资质、牌照、认证和监管审批状态。",
            "请提供核心客户和供应商合同中的排他、违约和终止条款。",
            "请说明数据、环保、安全生产或行业监管的合规要求。",
        ],
        "退出路径尽调": [
            "请说明预期退出路径、退出时间和关键前置条件。",
            "请提供可比 IPO、并购、资产出售或股权转让案例。",
            "请说明潜在产业买方、财务买方或上市路径可行性。",
            "请说明退出倍数、退出估值和估值折扣假设。",
            "请说明影响退出的政策、行业周期和流动性风险。",
        ],
    }
    questions = []
    for category, category_questions in sections.items():
        for question in category_questions:
            questions.append({"category": category, "question": question, "priority": priority_for_question(question, document_extraction, financial_extraction, assumption_confirmation, data_gaps)})
    return questions


def build_data_gaps(
    document_extraction: dict[str, Any],
    financial_extraction: dict[str, Any],
    assumption_confirmation: dict[str, Any] | None,
    basic_valuation_result: dict[str, Any] | None,
    multi_model_result: dict[str, Any] | None,
    input_status: dict[str, Any],
) -> list[str]:
    gaps = list(input_status.get("missing_modules", []))
    readiness = document_extraction.get("valuation_readiness", {})
    gaps.extend(readiness.get("missing_data", []))
    gaps.extend(readiness.get("questions_for_company", []))
    gaps.extend((basic_valuation_result or {}).get("missing_data", []))
    gaps.extend((multi_model_result or {}).get("for_v0_8_decision_memo", {}).get("data_gaps", []))
    extracted = financial_extraction.get("extracted_financial_data", {})
    gaps.extend(extracted.get("missing_financial_data", []))
    gaps.extend(extracted.get("requires_user_confirmation", []))
    if assumption_confirmation:
        gaps.extend(assumption_confirmation.get("readiness_summary", {}).get("missing_before_calculation", []))
    return dedupe([str(item) for item in gaps if has_value(item)])


def build_research_action(
    memo_completeness: str,
    data_gaps: list[str],
    multi_model_result: dict[str, Any] | None,
    risk_summary: dict[str, Any],
) -> dict[str, Any]:
    confidence = (multi_model_result or {}).get("confidence_level", "")
    high_risk_count = sum(1 for value in risk_summary.values() if has_value(value))
    if memo_completeness in {"高", "中"} and confidence in {"高", "中"} and len(data_gaps) <= 8 and high_risk_count < 8:
        action = "进入深度研究"
        reason = "Memo 完整度和估值置信度较好，风险可识别但仍需进一步核验。"
    elif memo_completeness == "不足":
        action = "暂不进入估值"
        reason = "关键资料不足，暂不能形成有效估值框架。"
    elif any("财务模型解析" in item or "财务" in item or "现金流" in item for item in data_gaps):
        action = "等待更多财务或项目数据"
        reason = "财务、现金流或项目验证数据仍不足。"
    elif data_gaps:
        action = "需要补充数据"
        reason = "项目具备初步研究价值，但关键数据仍需补充。"
    else:
        action = "进入观察池"
        reason = "项目方向可继续跟踪，但现阶段仍需更多验证。"
    return {
        "suggested_action": safe_research_action(action),
        "reason": reason,
        "next_steps": next_steps_for_action(action, data_gaps),
    }


def infer_target_name(*payloads: dict[str, Any] | None) -> str:
    for payload in payloads:
        if not payload:
            continue
        if payload.get("target_name"):
            return str(payload["target_name"])
        basic = payload.get("project_basic_info", {})
        if basic.get("project_name") or basic.get("company_name"):
            return str(basic.get("project_name") or basic.get("company_name"))
        file_name = payload.get("file_name")
        if file_name:
            return str(file_name).split(".")[0]
    return "未命名项目"


def quality_impact_from_modules(modules: dict[str, bool]) -> str:
    missing = [MODULE_LABELS[key] for key, value in modules.items() if not value]
    if not missing:
        return "输入模块完整，可以生成较高完整度 Memo 草稿。"
    return "缺失：" + "、".join(missing) + "；Memo 质量和研究动作置信度会降低。"


def assumption_value(assumption_confirmation: dict[str, Any] | None, group: str, field: str) -> Any:
    if not assumption_confirmation:
        return None
    inputs = assumption_confirmation.get("valuation_inputs", {})
    payload = inputs.get(group, {}).get(field)
    if payload and payload.get("confirmed_value"):
        return payload.get("confirmed_value")
    for item in assumption_confirmation.get("assumption_groups", {}).get(group, []):
        if item.get("field") == field and item.get("confirmed_value"):
            return item.get("confirmed_value")
    return None


def field_value(fields: dict[str, Any], field: str) -> Any:
    payload = fields.get(field, {})
    return payload.get("extraction_result") if isinstance(payload, dict) else None


def first_value(*values: Any) -> Any:
    for value in values:
        if has_value(value):
            return value
    return ""


def has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip()) and value.strip() not in {"未披露", "待补充", "缺失", "无"}
    if isinstance(value, (list, dict)):
        return bool(value)
    return True


def join_values(*values: Any) -> str:
    parts = []
    for value in values:
        if isinstance(value, list):
            parts.extend(str(item) for item in value if has_value(item))
        elif has_value(value):
            parts.append(str(value))
    return "、".join(parts)


def contains_any(value: Any, keywords: list[str]) -> str:
    text = str(value or "")
    return "是" if any(keyword in text for keyword in keywords) else "待确认"


def infer_copyability(business: dict[str, Any]) -> str:
    if business.get("is_productized") or business.get("is_platform_based"):
        return "相对较高，需结合交付标准化程度核验"
    if business.get("is_project_based"):
        return "偏项目制，复制性需进一步核验"
    return "待补充"


def business_model_risk(business: dict[str, Any]) -> str:
    if business.get("depends_on_government_or_key_customers"):
        return "可能依赖政府订单或大客户，需核验集中度和回款周期"
    return "待补充"


def customer_validation_strength(product: dict[str, Any]) -> str:
    if has_value(product.get("signed_customers")) or has_value(product.get("contracts")):
        return "已有客户或合同线索，需核验合同金额和履约状态"
    if has_value(product.get("intended_customers")) or has_value(product.get("orders")):
        return "存在意向客户或订单线索，需区分已签与意向"
    return "待补充"


def financial_confidence(financial_extraction: dict[str, Any], assumption_confirmation: dict[str, Any] | None) -> str:
    if financial_extraction.get("extraction_quality") == "success":
        return "中"
    if assumption_confirmation and assumption_confirmation.get("readiness_summary", {}).get("valuation_readiness_level") in {"高", "中"}:
        return assumption_confirmation["readiness_summary"]["valuation_readiness_level"]
    return "待补充"


def priority_for_question(
    question: str,
    document_extraction: dict[str, Any],
    financial_extraction: dict[str, Any],
    assumption_confirmation: dict[str, Any] | None,
    data_gaps: list[str],
) -> str:
    text = " ".join(data_gaps)
    if any(keyword in question for keyword in ["财务", "现金流", "收入", "CAPEX", "估值"]) and any(keyword in text for keyword in ["财务", "现金流", "收入", "CAPEX", "估值"]):
        return "高"
    if any(keyword in question for keyword in ["创始", "团队"]) and not document_extraction.get("founder_team", {}).get("founders"):
        return "高"
    if any(keyword in question for keyword in ["客户", "订单", "合同"]) and not document_extraction.get("products_and_customers", {}).get("signed_customers"):
        return "高"
    return "中"


def safe_research_action(action: str) -> str:
    return action if action in ALLOWED_RESEARCH_ACTIONS else "需要补充数据"


def next_steps_for_action(action: str, data_gaps: list[str]) -> list[str]:
    base = {
        "进入深度研究": ["核验核心数据来源。", "建立可比公司与可比交易样本。", "准备下一版内部投资备忘录。"],
        "进入观察池": ["建立项目观察记录。", "跟踪客户、收入和融资进展。", "设置下一次复查日期。"],
        "需要补充数据": ["向项目方发送尽调问题清单。", "补齐关键财务、客户和融资数据。", "更新关键假设确认表。"],
        "暂不进入估值": ["记录资料不足原因。", "等待项目方补充基础资料。", "暂不生成进一步估值结论。"],
        "等待更多财务或项目数据": ["补充财务模型和项目测算表。", "核验订单、合同和产能爬坡数据。", "等待更多经营验证数据。"],
    }
    steps = list(base.get(action, base["需要补充数据"]))
    steps.extend(f"补充：{item}" for item in data_gaps[:3])
    return steps


def watchlist_status_from_action(action: str) -> str:
    if action == "进入深度研究":
        return "deep_research"
    if action == "进入观察池":
        return "watchlist"
    if action in {"需要补充数据", "等待更多财务或项目数据"}:
        return "pending_data"
    return "inactive"


def build_warnings(input_status: dict[str, Any], memo_completeness: str, data_gaps: list[str]) -> list[str]:
    warnings = [
        "本文件仅用于 Rachel Capital OS 内部研究，不构成投资建议、投资邀约、买卖依据、目标价或收益承诺。",
        "所有结论均需人工复核。",
    ]
    if memo_completeness in {"低", "不足"}:
        warnings.append("Memo 完整度较低，当前只能作为初步研究草稿。")
    if data_gaps:
        warnings.append("仍存在关键数据缺口，需要项目方或用户继续补充。")
    if input_status.get("missing_modules"):
        warnings.append("缺失输入模块：" + "、".join(input_status["missing_modules"]))
    return warnings


def dedupe(items: list[str]) -> list[str]:
    seen = set()
    result = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result
