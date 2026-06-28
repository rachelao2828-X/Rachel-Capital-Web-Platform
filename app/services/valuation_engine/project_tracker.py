from __future__ import annotations

from datetime import date, timedelta
from typing import Any


PROJECT_STATUS_OPTIONS = [
    "新建观察",
    "等待资料",
    "初步解析完成",
    "估值框架完成",
    "待深度尽调",
    "深度尽调中",
    "暂缓跟踪",
    "已放弃",
    "已进入投资决策",
    "已归档",
]

WATCHLIST_STATUS_OPTIONS = [
    "active",
    "pending_data",
    "deep_research_candidate",
    "paused",
    "archived",
    "rejected",
    "investment_decision_candidate",
]

WATCHLIST_STATUS_LABELS = {
    "active": "观察中",
    "pending_data": "等待资料",
    "deep_research_candidate": "深度研究候选",
    "paused": "暂缓",
    "archived": "已归档",
    "rejected": "已放弃",
    "investment_decision_candidate": "投资决策候选",
}

ALLOWED_RESEARCH_ACTIONS = {
    "进入观察池",
    "需要补充数据",
    "进入深度研究",
    "暂不进入估值",
    "等待更多财务或项目数据",
}


def build_project_tracking_record(
    memo_data: dict[str, Any] | None,
    manual_inputs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    memo_data = memo_data or {}
    manual_inputs = manual_inputs or {}
    target_profile = manual_inputs.get("target_profile") or memo_data.get("target_profile") or {}
    target_name = first_value(manual_inputs.get("target_name"), target_profile_value(target_profile, "target_name"), memo_data.get("target_name"), "未命名项目")
    memo_tracking = memo_data.get("for_v0_9_project_tracking", {})
    research_action = safe_research_action(first_value(manual_inputs.get("research_action"), memo_tracking.get("research_action"), memo_data.get("research_action", {}).get("suggested_action"), "需要补充数据"))
    default_project_status, default_watchlist_status = status_from_research_action(research_action)
    project_status = safe_project_status(first_value(manual_inputs.get("project_status"), default_project_status))
    watchlist_status = safe_watchlist_status(first_value(manual_inputs.get("watchlist_status"), memo_tracking.get("watchlist_status"), default_watchlist_status))
    next_review_date = first_value(manual_inputs.get("next_review_date"), memo_tracking.get("next_review_date"), suggest_next_review_date(watchlist_status, project_status))
    project_card = build_project_card(memo_data, manual_inputs, target_name, project_status, watchlist_status, research_action, next_review_date, target_profile)
    data_gaps = dedupe(listify(manual_inputs.get("data_gaps")) + listify(memo_tracking.get("data_gaps")) + listify(memo_data.get("data_gaps")))
    questions_for_company = dedupe(listify(manual_inputs.get("questions_for_company")) + listify(memo_tracking.get("questions_for_company")) + [item.get("question", "") for item in memo_data.get("due_diligence_questions", [])[:20]])
    risk_flags = risk_flags_from_memo(memo_data)
    valuation_summary = memo_data.get("valuation_summary") or {
        "估值摘要": memo_data.get("financing_valuation_review", {}).get("多模型估值区间", ""),
        "估值置信度": memo_data.get("financing_valuation_review", {}).get("综合置信度", ""),
    }
    tracking_tasks = build_tracking_tasks(memo_data, data_gaps, questions_for_company, risk_flags, project_status, watchlist_status, next_review_date)
    if manual_inputs.get("tracking_tasks"):
        tracking_tasks = normalize_tasks(manual_inputs["tracking_tasks"], next_review_date)
    warnings = build_warnings(memo_data, research_action, watchlist_status)

    return {
        "target_name": target_name,
        "target_profile": target_profile,
        "tracking_date": date.today().isoformat(),
        "project_status": project_status,
        "watchlist_status": watchlist_status,
        "watchlist_status_label": WATCHLIST_STATUS_LABELS.get(watchlist_status, watchlist_status),
        "research_action": research_action,
        "next_review_date": next_review_date,
        "project_card": project_card,
        "tracking_tasks": tracking_tasks,
        "data_gaps": data_gaps,
        "questions_for_company": questions_for_company,
        "risk_flags": risk_flags,
        "valuation_summary": valuation_summary,
        "source_memo": memo_data.get("target_name", ""),
        "warnings": warnings,
        "for_v1_0_portfolio_decision": {
            "target_name": target_name,
            "project_status": project_status,
            "research_action": research_action,
            "valuation_summary": valuation_summary,
            "memo_links": project_card.get("linked_memos", []),
            "tracking_tasks": tracking_tasks,
            "next_review_date": next_review_date,
            "decision_readiness": decision_readiness(project_status, watchlist_status, memo_data),
            "suggested_next_gate": suggested_next_gate(project_status, watchlist_status),
        },
    }


def status_from_research_action(research_action: str) -> tuple[str, str]:
    mapping = {
        "进入观察池": ("新建观察", "active"),
        "需要补充数据": ("等待资料", "pending_data"),
        "进入深度研究": ("待深度尽调", "deep_research_candidate"),
        "暂不进入估值": ("暂缓跟踪", "paused"),
        "等待更多财务或项目数据": ("等待资料", "pending_data"),
    }
    return mapping.get(research_action, ("等待资料", "pending_data"))


def suggest_next_review_date(watchlist_status: str, project_status: str | None = None) -> str:
    if watchlist_status in {"archived", "rejected"} or project_status in {"已放弃", "已归档"}:
        return ""
    days = {
        "active": 30,
        "pending_data": 14,
        "deep_research_candidate": 7,
        "paused": 60,
        "investment_decision_candidate": 7,
    }.get(watchlist_status, 30)
    return (date.today() + timedelta(days=days)).isoformat()


def build_project_card(
    memo_data: dict[str, Any],
    manual_inputs: dict[str, Any],
    target_name: str,
    project_status: str,
    watchlist_status: str,
    research_action: str,
    next_review_date: str,
    target_profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    snapshot = memo_data.get("project_snapshot", {})
    founder = memo_data.get("founder_team_review", {})
    business = memo_data.get("business_model_review", {})
    technology = memo_data.get("technology_review", {})
    product_customer = memo_data.get("product_customer_review", {})
    market = memo_data.get("market_competition_review", {})
    financial = memo_data.get("financial_review", {})
    financing = memo_data.get("financing_valuation_review", {})
    valuation = memo_data.get("valuation_summary", {})
    risk = memo_data.get("risk_summary", {})
    return {
        "target_name": target_name,
        "company_name": first_value(manual_inputs.get("company_name"), snapshot.get("公司名称")),
        "project_name": first_value(manual_inputs.get("project_name"), snapshot.get("项目名称"), target_name),
        "industry": first_value(manual_inputs.get("industry"), target_profile_value(target_profile, "industry"), snapshot.get("所属行业")),
        "rachel_ecosystem": first_value(manual_inputs.get("rachel_ecosystem"), target_profile_value(target_profile, "rachel_ecosystem"), snapshot.get("所属 Rachel 战略生态")),
        "target_type": first_value(manual_inputs.get("target_type"), target_profile_value(target_profile, "target_type"), snapshot.get("标的类型")),
        "project_stage": first_value(manual_inputs.get("project_stage"), snapshot.get("项目阶段")),
        "location": first_value(manual_inputs.get("location"), snapshot.get("地区")),
        "one_sentence_summary": first_value(manual_inputs.get("one_sentence_summary"), snapshot.get("一句话摘要")),
        "founder_team_summary": summarize_dict(founder, ["创始人 / 联合创始人", "核心高管", "团队完整度", "团队风险"]),
        "business_model_summary": summarize_dict(business, ["收入来源", "客户类型", "付费模式", "商业模式风险"]),
        "technology_summary": summarize_dict(technology, ["核心技术", "技术成熟度", "技术壁垒", "技术风险"]),
        "product_customer_summary": summarize_dict(product_customer, ["主要产品", "已签客户", "订单情况", "客户验证强度"]),
        "market_summary": summarize_dict(market, ["市场规模", "市场增速", "竞争格局", "市场空间可信度"]),
        "financial_summary": summarize_dict(financial, ["历史收入", "预测收入", "EBITDA", "现金流", "财务数据可信度"]),
        "financing_summary": summarize_dict(financing, ["本轮融资金额", "投前估值", "投后估值", "出让股权比例"]),
        "valuation_summary": summarize_dict(valuation, ["基础估值区间", "多模型综合区间", "综合置信度", "模型分歧度"]),
        "risk_summary": summarize_risks(risk),
        "memo_completeness": memo_data.get("memo_completeness", ""),
        "valuation_confidence": first_value(financing.get("综合置信度"), valuation.get("综合置信度")),
        "research_action": research_action,
        "project_status": project_status,
        "watchlist_status": watchlist_status,
        "next_review_date": next_review_date,
        "source_files": listify(manual_inputs.get("source_files")),
        "linked_memos": listify(manual_inputs.get("linked_memos")),
        "linked_questions": listify(manual_inputs.get("linked_questions")),
        "tags": dedupe(["一级市场项目", "估值驾驶舱", "项目观察池", str(first_value(snapshot.get("所属行业"), ""))]),
    }


def build_tracking_tasks(
    memo_data: dict[str, Any],
    data_gaps: list[str],
    questions_for_company: list[str],
    risk_flags: list[str],
    project_status: str,
    watchlist_status: str,
    next_review_date: str,
) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    due = next_review_date or (date.today() + timedelta(days=14)).isoformat()
    for gap in data_gaps[:10]:
        tasks.append(task(f"补充并核验：{gap}", "资料补充", "高", due, "V0.8 数据缺口"))
    for question in questions_for_company[:12]:
        tasks.append(task(question, category_from_question(question), priority_from_question(question), due, "V0.8 尽调问题"))
    valuation_confidence = str(memo_data.get("valuation_summary", {}).get("综合置信度") or memo_data.get("financing_valuation_review", {}).get("综合置信度") or "")
    if valuation_confidence in {"低", "仅供框架参考", ""}:
        tasks.extend(
            [
                task("补充财务模型、关键假设和可比公司清单。", "估值复核", "高", due, "估值置信度"),
                task("复核收入、利润、现金流、折现率和估值折扣假设。", "估值复核", "高", due, "估值置信度"),
            ]
        )
    if not memo_data.get("founder_team_review", {}).get("创始人 / 联合创始人"):
        tasks.append(task("补充创始团队完整履历、股权分配和关键人稳定性说明。", "团队尽调", "高", due, "团队信息缺失"))
    product_summary = " ".join(str(value) for value in memo_data.get("product_customer_review", {}).values())
    if "合同" not in product_summary and "客户" not in product_summary:
        tasks.append(task("补充已签客户、合同、订单和客户集中度资料。", "客户尽调", "高", due, "客户合同信息缺失"))
    financing_summary = memo_data.get("financing_valuation_review", {})
    if not first_value(financing_summary.get("退出路径"), financing_summary.get("预计退出时间")):
        tasks.append(task("补充退出路径、退出时间和可比退出案例。", "退出路径", "中", due, "退出路径不清楚"))
    if project_status in {"待深度尽调", "深度尽调中"} or watchlist_status == "deep_research_candidate":
        tasks.extend(
            [
                task("安排管理层访谈。", "团队尽调", "高", due, "深度研究"),
                task("补充财务预测模型。", "财务尽调", "高", due, "深度研究"),
                task("核验客户合同。", "客户尽调", "高", due, "深度研究"),
                task("建立可比公司清单。", "产业研究", "中", due, "深度研究"),
                task("复核估值假设。", "估值复核", "高", due, "深度研究"),
                task("准备内部讨论材料。", "内部复盘", "中", due, "深度研究"),
            ]
        )
    for risk in risk_flags[:6]:
        tasks.append(task(f"跟踪风险标记：{risk}", "内部复盘", "中", due, "风险标记"))
    return dedupe_tasks(tasks)


def task(task_name: str, category: str, priority: str, due_date: str, source: str) -> dict[str, Any]:
    return {
        "task": task_name,
        "category": category,
        "priority": priority if priority in {"高", "中", "低"} else "中",
        "due_date": due_date,
        "status": "todo",
        "source": source,
    }


def normalize_tasks(rows: list[dict[str, Any]], default_due_date: str) -> list[dict[str, Any]]:
    normalized = []
    for row in rows:
        normalized.append(
            {
                "task": first_value(row.get("task"), row.get("任务"), ""),
                "category": first_value(row.get("category"), row.get("分类"), "资料补充"),
                "priority": first_value(row.get("priority"), row.get("优先级"), "中"),
                "due_date": first_value(row.get("due_date"), row.get("截止日期"), default_due_date),
                "status": first_value(row.get("status"), row.get("状态"), "todo"),
                "source": first_value(row.get("source"), row.get("来源"), "用户编辑"),
            }
        )
    return normalized


def risk_flags_from_memo(memo_data: dict[str, Any]) -> list[str]:
    risks = []
    for label, value in memo_data.get("risk_summary", {}).items():
        if has_value(value):
            risks.append(f"{label}: {value}")
    for item in memo_data.get("valuation_summary", {}).get("主要分歧来源", []):
        if has_value(item):
            risks.append(str(item))
    return dedupe(risks)


def category_from_question(question: str) -> str:
    if any(keyword in question for keyword in ["创始", "团队", "管理层"]):
        return "团队尽调"
    if any(keyword in question for keyword in ["技术", "专利", "测试"]):
        return "技术尽调"
    if any(keyword in question for keyword in ["客户", "订单", "合同", "复购"]):
        return "客户尽调"
    if any(keyword in question for keyword in ["财务", "收入", "现金流", "CAPEX", "利润"]):
        return "财务尽调"
    if any(keyword in question for keyword in ["合规", "法务", "诉讼", "资质"]):
        return "法务合规"
    if any(keyword in question for keyword in ["退出", "IPO", "并购"]):
        return "退出路径"
    if any(keyword in question for keyword in ["估值", "可比"]):
        return "估值复核"
    return "资料补充"


def priority_from_question(question: str) -> str:
    if any(keyword in question for keyword in ["估值", "融资", "现金流", "合同", "创始", "核心"]):
        return "高"
    return "中"


def summarize_dict(values: dict[str, Any], keys: list[str]) -> str:
    parts = []
    for key in keys:
        value = values.get(key)
        if isinstance(value, list):
            display = "、".join(str(item) for item in value if has_value(item))
        else:
            display = str(value) if has_value(value) else ""
        if display:
            parts.append(f"{key}: {display}")
    return "；".join(parts)


def summarize_risks(risk: dict[str, Any]) -> str:
    return "；".join(f"{key}: {value}" for key, value in risk.items() if has_value(value)) or "待补充"


def decision_readiness(project_status: str, watchlist_status: str, memo_data: dict[str, Any]) -> str:
    confidence = str(memo_data.get("valuation_summary", {}).get("综合置信度") or memo_data.get("financing_valuation_review", {}).get("综合置信度") or "")
    if project_status in {"已进入投资决策"} or watchlist_status == "investment_decision_candidate":
        return "高"
    if project_status in {"待深度尽调", "深度尽调中"} and confidence in {"高", "中"}:
        return "中"
    if project_status in {"新建观察", "等待资料"}:
        return "低"
    return "不足"


def suggested_next_gate(project_status: str, watchlist_status: str) -> str:
    if project_status in {"已进入投资决策"} or watchlist_status == "investment_decision_candidate":
        return "投资委员会工作流"
    if project_status in {"待深度尽调", "深度尽调中"}:
        return "深度尽调闸门"
    if project_status == "等待资料":
        return "资料补充闸门"
    if project_status == "新建观察":
        return "观察池复查闸门"
    return "暂不进入下一闸门"


def safe_research_action(value: str) -> str:
    return value if value in ALLOWED_RESEARCH_ACTIONS else "需要补充数据"


def safe_project_status(value: str) -> str:
    return value if value in PROJECT_STATUS_OPTIONS else "等待资料"


def safe_watchlist_status(value: str) -> str:
    return value if value in WATCHLIST_STATUS_OPTIONS else "pending_data"


def build_warnings(memo_data: dict[str, Any], research_action: str, watchlist_status: str) -> list[str]:
    warnings = [
        "本记录仅用于 Rachel Capital OS 内部研究观察，不构成投资建议、投资邀约、买卖依据、目标价或收益承诺。",
        "项目状态、观察池状态和研究动作均需人工复核。",
    ]
    if not memo_data:
        warnings.append("缺少 V0.8 投资备忘录整合结果，当前记录主要来自手动输入。")
    if research_action == "暂不进入估值" and watchlist_status != "paused":
        warnings.append("V0.8 研究动作建议为暂不进入估值，当前观察池纳入属于用户手动覆盖。")
    return warnings


def first_value(*values: Any) -> str:
    for value in values:
        if has_value(value):
            return str(value)
    return ""


def target_profile_value(target_profile: dict[str, Any] | None, key: str) -> str:
    payload = (target_profile or {}).get(key, {})
    if isinstance(payload, dict) and has_value(payload.get("confirmed_value")):
        return str(payload.get("confirmed_value"))
    return ""


def has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip()) and value.strip() not in {"无", "缺失", "待补充", "未披露"}
    if isinstance(value, (list, dict)):
        return bool(value)
    return True


def listify(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if has_value(item)]
    if isinstance(value, dict):
        return [f"{key}: {item}" for key, item in value.items() if has_value(item)]
    if isinstance(value, str):
        return [value] if has_value(value) else []
    return [str(value)]


def dedupe(items: list[str]) -> list[str]:
    seen = set()
    result = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result


def dedupe_tasks(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    result = []
    for item in tasks:
        key = (item.get("task"), item.get("category"))
        if item.get("task") and key not in seen:
            seen.add(key)
            result.append(item)
    return result
