from __future__ import annotations

from datetime import date, timedelta
from typing import Any


DECISION_STAGES = [
    "初筛",
    "观察池复查",
    "深度尽调立项",
    "投委会预审",
    "投委会讨论",
    "投资决策候选",
    "暂缓",
    "放弃",
    "归档",
]

PROCESS_ACTIONS = [
    "继续观察",
    "补充资料后复查",
    "启动深度尽调",
    "提交投委会预审",
    "进入投资决策候选",
    "暂缓",
    "归档",
    "人工风险复核",
]

GATE_CATEGORIES = {
    "项目资料完整性": [
        "是否有 BP / 项目资料",
        "是否有财务模型",
        "是否有融资条款",
        "是否有客户资料",
        "是否有团队资料",
        "是否有技术资料",
        "是否有法律合规资料",
    ],
    "团队闸门": [
        "创始团队履历是否清晰",
        "技术负责人是否明确",
        "商业负责人是否明确",
        "财务负责人是否明确",
        "是否存在关键人依赖",
        "团队是否具备产业落地能力",
    ],
    "技术闸门": [
        "核心技术是否清楚",
        "技术成熟度是否明确",
        "是否有专利 / 测试 / 认证",
        "是否已中试 / 量产 / 规模化",
        "关键技术依赖是否可控",
        "技术替代对象是否明确",
    ],
    "产品与客户闸门": [
        "产品是否清楚",
        "客户画像是否清楚",
        "是否有已签客户",
        "是否有真实订单",
        "是否存在大客户依赖",
        "客户验证是否充分",
    ],
    "市场与竞争闸门": [
        "市场空间是否可信",
        "竞争格局是否清楚",
        "国产替代 / 产业趋势逻辑是否成立",
        "可比公司是否明确",
        "竞争优势是否可持续",
    ],
    "财务闸门": [
        "历史收入是否披露",
        "预测收入是否有依据",
        "毛利率是否可信",
        "现金流是否可解释",
        "CAPEX 是否明确",
        "产能利用率是否合理",
        "回收期 / IRR 是否可复核",
    ],
    "估值闸门": [
        "是否有投前 / 投后估值",
        "是否有融资金额和出让比例",
        "是否完成基础估值计算",
        "是否完成多模型估值对比",
        "模型分歧是否可解释",
        "估值置信度是否达到中以上",
        "是否存在估值过高风险",
    ],
    "风险闸门": [
        "技术风险是否可识别",
        "市场风险是否可识别",
        "客户风险是否可识别",
        "政策风险是否可识别",
        "融资风险是否可识别",
        "团队风险是否可识别",
        "退出风险是否可识别",
        "是否存在一票否决风险",
    ],
    "退出路径闸门": [
        "是否有明确退出路径",
        "是否可能 IPO",
        "是否可能并购",
        "是否可能分红回收",
        "是否有可比退出案例",
        "退出时间是否合理",
    ],
    "决策流程闸门": [
        "是否完成项目卡片",
        "是否完成投资备忘录草稿",
        "是否完成尽调问题清单",
        "是否完成项目跟踪任务",
        "是否需要管理层访谈",
        "是否需要外部专家意见",
        "是否需要法律 / 财务 / 技术专项尽调",
    ],
}


def build_investment_committee_package(
    tracking_record: dict[str, Any] | None,
    manual_inputs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    tracking_record = tracking_record or {}
    manual_inputs = manual_inputs or {}
    target_name = first_value(manual_inputs.get("target_name"), tracking_record.get("target_name"), "未命名项目")
    decision_stage = safe_choice(
        manual_inputs.get("decision_stage"),
        DECISION_STAGES,
        default_decision_stage(tracking_record.get("project_status", "")),
    )
    readiness, readiness_reason = decision_readiness(tracking_record)
    gate_checklist = build_gate_checklist(tracking_record)
    red_flags = detect_red_flags(tracking_record, gate_checklist)
    suggested_process_action = safe_choice(
        manual_inputs.get("process_action"),
        PROCESS_ACTIONS,
        suggested_action(readiness, red_flags, tracking_record),
    )
    status_update = status_update_from_action(suggested_process_action, tracking_record)
    manual_review = build_manual_review(manual_inputs, suggested_process_action)
    committee_memo = build_committee_memo(
        tracking_record,
        gate_checklist,
        red_flags,
        suggested_process_action,
        manual_review,
    )
    decision_record = build_decision_record(
        decision_stage,
        suggested_process_action,
        status_update,
        manual_review,
        committee_memo,
    )
    follow_up_tasks = build_follow_up_tasks(tracking_record, committee_memo, manual_review, status_update)
    warnings = build_warnings(tracking_record, readiness, red_flags, suggested_process_action)
    today = date.today().isoformat()

    return {
        "target_name": target_name,
        "committee_date": manual_review.get("review_date") or today,
        "decision_stage": decision_stage,
        "decision_readiness": readiness,
        "decision_readiness_reason": readiness_reason,
        "gate_checklist": gate_checklist,
        "red_flags": red_flags,
        "committee_memo": committee_memo,
        "manual_review": manual_review,
        "decision_record": decision_record,
        "next_project_status": status_update["next_project_status"],
        "next_watchlist_status": status_update["next_watchlist_status"],
        "next_review_date": status_update["next_review_date"],
        "follow_up_tasks": follow_up_tasks,
        "warnings": warnings,
        "source_tracking_record": tracking_record,
        "for_v1_1_post_decision_tracking": {
            "target_name": target_name,
            "process_action": suggested_process_action,
            "next_project_status": status_update["next_project_status"],
            "next_watchlist_status": status_update["next_watchlist_status"],
            "next_review_date": status_update["next_review_date"],
            "follow_up_tasks": follow_up_tasks,
            "decision_log_path": "",
            "committee_memo_path": "",
            "project_card_path": "",
            "watchlist_path": "",
        },
    }


def default_decision_stage(project_status: str) -> str:
    mapping = {
        "新建观察": "初筛",
        "等待资料": "观察池复查",
        "待深度尽调": "深度尽调立项",
        "深度尽调中": "投委会预审",
        "已进入投资决策": "投资决策候选",
        "暂缓跟踪": "暂缓",
        "已放弃": "放弃",
        "已归档": "归档",
    }
    return mapping.get(project_status, "观察池复查")


def decision_readiness(tracking_record: dict[str, Any]) -> tuple[str, str]:
    if not tracking_record:
        return "不足", "缺少项目跟踪记录，无法形成稳定的投委会流程输入。"

    card = tracking_record.get("project_card", {})
    valuation = tracking_record.get("valuation_summary", {})
    data_gaps = listify(tracking_record.get("data_gaps"))
    questions = listify(tracking_record.get("questions_for_company"))
    risks = listify(tracking_record.get("risk_flags"))
    tasks = tracking_record.get("tracking_tasks", [])
    has_card = bool(card)
    has_memo = has_value(tracking_record.get("source_memo")) or has_value(card.get("linked_memos"))
    has_valuation = any(has_value(value) for value in flatten_values(valuation))
    has_questions = bool(questions)
    has_risks = bool(risks) or has_value(card.get("risk_summary"))
    has_tasks = bool(tasks)
    gap_count = len(data_gaps)

    if has_card and has_memo and has_valuation and has_questions and has_risks and has_tasks and gap_count <= 1:
        return "高", "项目卡片、Memo、估值摘要、风险清单、尽调问题和跟踪任务较完整，主要缺口较少。"
    if has_memo and has_valuation and has_risks and has_questions:
        return "中", "已具备 Memo、估值摘要、主要风险和尽调问题，但仍有部分数据缺口。"
    if has_card or has_value(tracking_record.get("target_name")):
        return "低", "已有项目卡片或基础项目记录，但财务、估值或尽调结果仍不完整。"
    return "不足", "缺少项目摘要、财务数据、估值结果和尽调结论。"


def build_gate_checklist(tracking_record: dict[str, Any]) -> dict[str, list[dict[str, str]]]:
    text = searchable_text(tracking_record)
    return {
        category: [check_item(item, text, tracking_record) for item in items]
        for category, items in GATE_CATEGORIES.items()
    }


def check_item(item: str, text: str, tracking_record: dict[str, Any]) -> dict[str, str]:
    keywords = gate_keywords(item)
    evidence = evidence_from_keywords(text, keywords)
    missing_items = " ".join(listify(tracking_record.get("data_gaps")) + listify(tracking_record.get("questions_for_company")))
    if evidence:
        status = "通过"
        risk_level = "低"
        notes = "已在项目记录中识别到相关信息，仍需人工复核。"
    elif any(keyword in missing_items for keyword in keywords):
        status = "待补充"
        risk_level = "中"
        notes = "该项出现在数据缺口或追问清单中。"
    elif "是否需要" in item:
        status = "待补充"
        risk_level = "中"
        notes = "需由人工复核决定是否启动专项工作。"
    else:
        status = "待补充"
        risk_level = "中"
        notes = "当前记录未识别到充分证据。"
    return {
        "item": item,
        "status": status,
        "evidence": evidence or "待补充",
        "risk_level": risk_level,
        "notes": notes,
    }


def gate_keywords(item: str) -> list[str]:
    mapping = {
        "BP": ["BP", "项目资料", "商业计划书", "项目摘要"],
        "财务模型": ["财务模型", "预测收入", "历史收入", "现金流", "CAPEX"],
        "融资条款": ["融资", "投前", "投后", "出让股权", "融资金额"],
        "客户": ["客户", "订单", "合同", "已签客户"],
        "团队": ["创始", "团队", "核心高管", "技术负责人"],
        "技术": ["技术", "专利", "认证", "量产", "中试"],
        "法律": ["法律", "合规", "诉讼", "监管"],
        "创始": ["创始", "联合创始", "团队履历"],
        "商业负责人": ["商业负责人", "核心高管"],
        "财务负责人": ["财务负责人", "CFO"],
        "关键人": ["关键人", "依赖"],
        "产业落地": ["产业经验", "落地", "量产", "客户"],
        "核心技术": ["核心技术", "技术壁垒"],
        "成熟度": ["技术成熟度", "中试", "量产"],
        "专利": ["专利", "测试", "认证"],
        "产品": ["产品", "平台", "服务"],
        "市场": ["市场", "竞争", "国产替代", "产业趋势"],
        "可比": ["可比", "同业", "交易案例"],
        "历史收入": ["历史收入"],
        "预测收入": ["预测收入"],
        "毛利率": ["毛利率"],
        "现金流": ["现金流"],
        "CAPEX": ["CAPEX", "项目总投资"],
        "产能": ["产能", "利用率"],
        "IRR": ["IRR", "回收期"],
        "基础估值": ["基础估值", "估值摘要"],
        "多模型": ["多模型", "综合区间"],
        "估值置信度": ["估值置信度", "综合置信度"],
        "估值过高": ["估值过高", "分歧度", "明显偏离"],
        "风险": ["风险"],
        "退出": ["退出", "IPO", "并购", "分红"],
        "项目卡片": ["项目卡片", "project_card"],
        "投资备忘录": ["投资备忘录", "source_memo", "Memo"],
        "尽调问题": ["尽调问题", "追问"],
        "跟踪任务": ["tracking_tasks", "跟踪任务"],
        "管理层访谈": ["管理层访谈"],
        "外部专家": ["外部专家", "专家"],
        "专项尽调": ["法律", "财务尽调", "技术尽调"],
    }
    for key, keywords in mapping.items():
        if key in item:
            return keywords
    return [item]


def detect_red_flags(tracking_record: dict[str, Any], gate_checklist: dict[str, list[dict[str, str]]]) -> list[dict[str, str]]:
    text = searchable_text(tracking_record)
    flags = []
    rules = [
        ("创始团队履历严重缺失", ["创始团队缺失", "团队信息缺失", "创始人", "团队"], "团队闸门"),
        ("财务数据完全缺失", ["财务数据缺失", "历史收入缺失", "预测收入缺失", "财务模型缺失"], "财务闸门"),
        ("客户合同无法验证", ["客户合同无法验证", "合同缺失", "订单缺失"], "产品与客户闸门"),
        ("核心技术无法验证", ["核心技术无法验证", "技术资料缺失", "专利缺失"], "技术闸门"),
        ("法律合规风险重大", ["重大合规", "法律风险", "监管风险", "诉讼"], "风险闸门"),
        ("项目方估值明显脱离可比区间", ["估值过高", "明显偏离", "模型分歧", "可比区间"], "估值闸门"),
        ("退出路径完全不清楚", ["退出路径缺失", "退出路径不清楚"], "退出路径闸门"),
        ("数据主要来自系统推断且无法验证", ["系统推断", "无法验证", "低置信度"], "项目资料完整性"),
        ("明确存在重大债务、诉讼、环保或监管风险", ["重大债务", "诉讼", "环保", "监管风险"], "风险闸门"),
    ]
    for label, keywords, category in rules:
        if any(keyword in text for keyword in keywords):
            flags.append({"flag": label, "risk_level": "高", "evidence": evidence_from_keywords(text, keywords) or "项目记录中存在相关风险提示", "suggested_process_action": "人工风险复核", "category": category})

    failed_gate_count = sum(1 for rows in gate_checklist.values() for item in rows if item["status"] == "不通过")
    if failed_gate_count:
        flags.append({"flag": "存在未通过的关键闸门项", "risk_level": "高", "evidence": f"{failed_gate_count} 个闸门项未通过", "suggested_process_action": "人工风险复核", "category": "决策流程闸门"})
    return dedupe_flags(flags)


def build_committee_memo(
    tracking_record: dict[str, Any],
    gate_checklist: dict[str, list[dict[str, str]]],
    red_flags: list[dict[str, str]],
    suggested_process_action: str,
    manual_review: dict[str, Any],
) -> dict[str, Any]:
    card = tracking_record.get("project_card", {})
    data_gaps = listify(tracking_record.get("data_gaps"))
    questions = listify(tracking_record.get("questions_for_company"))
    risks = listify(tracking_record.get("risk_flags"))
    return {
        "project_snapshot": card or {"target_name": tracking_record.get("target_name", "未命名项目")},
        "investment_thesis": first_value(card.get("one_sentence_summary"), card.get("business_model_summary"), "待人工补充项目核心逻辑。"),
        "key_value_drivers": key_value_drivers(card),
        "valuation_summary": tracking_record.get("valuation_summary", {}),
        "major_risks": risks,
        "red_flags": red_flags,
        "due_diligence_status": due_diligence_status(gate_checklist, tracking_record),
        "data_gaps": data_gaps,
        "decision_questions": questions[:12] or questions_from_gates(gate_checklist),
        "suggested_process_action": suggested_process_action,
        "next_steps": next_steps_from_action(suggested_process_action, data_gaps, questions, manual_review),
    }


def build_manual_review(manual_inputs: dict[str, Any], process_action: str) -> dict[str, Any]:
    return {
        "reviewer": manual_inputs.get("reviewer", ""),
        "review_date": manual_inputs.get("review_date") or date.today().isoformat(),
        "core_judgment": manual_inputs.get("core_judgment", ""),
        "main_attraction": manual_inputs.get("main_attraction", ""),
        "main_risk": manual_inputs.get("main_risk", ""),
        "required_data": listify(manual_inputs.get("required_data")),
        "needs_external_expert": bool(manual_inputs.get("needs_external_expert", False)),
        "needs_financial_due_diligence": bool(manual_inputs.get("needs_financial_due_diligence", False)),
        "needs_legal_due_diligence": bool(manual_inputs.get("needs_legal_due_diligence", False)),
        "needs_technical_due_diligence": bool(manual_inputs.get("needs_technical_due_diligence", False)),
        "process_action": safe_choice(manual_inputs.get("process_action"), PROCESS_ACTIONS, process_action),
        "notes": manual_inputs.get("notes", ""),
    }


def build_decision_record(
    decision_stage: str,
    process_action: str,
    status_update: dict[str, str],
    manual_review: dict[str, Any],
    committee_memo: dict[str, Any],
) -> dict[str, Any]:
    return {
        "decision_date": manual_review.get("review_date") or date.today().isoformat(),
        "decision_stage": decision_stage,
        "process_action": process_action,
        "decision_reason": manual_review.get("core_judgment") or "根据决策闸门、数据缺口、风险提示和人工复核意见形成流程动作。",
        "required_follow_up": dedupe(listify(manual_review.get("required_data")) + listify(committee_memo.get("data_gaps"))[:8]),
        "next_project_status": status_update["next_project_status"],
        "next_watchlist_status": status_update["next_watchlist_status"],
        "next_review_date": status_update["next_review_date"],
        "manual_reviewer": manual_review.get("reviewer", ""),
        "notes": manual_review.get("notes", ""),
    }


def status_update_from_action(process_action: str, tracking_record: dict[str, Any] | None = None) -> dict[str, str]:
    tracking_record = tracking_record or {}
    mapping = {
        "继续观察": ("初步解析完成" if tracking_record.get("project_status") == "初步解析完成" else "新建观察", "active", 30),
        "补充资料后复查": ("等待资料", "pending_data", 14),
        "启动深度尽调": ("深度尽调中", "deep_research_candidate", 7),
        "提交投委会预审": ("深度尽调中", "investment_decision_candidate", 7),
        "进入投资决策候选": ("已进入投资决策", "investment_decision_candidate", 7),
        "暂缓": ("暂缓跟踪", "paused", 60),
        "归档": ("已归档", "archived", None),
        "人工风险复核": ("待深度尽调", "deep_research_candidate", 7),
    }
    project_status, watchlist_status, days = mapping.get(process_action, mapping["继续观察"])
    return {
        "next_project_status": project_status,
        "next_watchlist_status": watchlist_status,
        "next_review_date": "" if days is None else (date.today() + timedelta(days=days)).isoformat(),
    }


def suggested_action(readiness: str, red_flags: list[dict[str, str]], tracking_record: dict[str, Any]) -> str:
    if red_flags:
        return "人工风险复核"
    if tracking_record.get("project_status") in {"已放弃", "已归档"}:
        return "归档"
    if readiness == "高":
        return "进入投资决策候选"
    if readiness == "中":
        return "提交投委会预审" if tracking_record.get("project_status") in {"深度尽调中", "已进入投资决策"} else "启动深度尽调"
    if readiness == "低":
        return "补充资料后复查"
    return "继续观察"


def build_follow_up_tasks(
    tracking_record: dict[str, Any],
    committee_memo: dict[str, Any],
    manual_review: dict[str, Any],
    status_update: dict[str, str],
) -> list[dict[str, str]]:
    due = status_update.get("next_review_date") or date.today().isoformat()
    tasks = []
    for item in listify(manual_review.get("required_data"))[:8]:
        tasks.append(task(f"补充并复核：{item}", "资料补充", "高", due, "人工复核"))
    for item in listify(committee_memo.get("data_gaps"))[:8]:
        tasks.append(task(f"关闭数据缺口：{item}", "资料补充", "高", due, "决策闸门"))
    for question in listify(committee_memo.get("decision_questions"))[:8]:
        tasks.append(task(question, "投委会问题", "中", due, "投委会 Memo"))
    if manual_review.get("needs_external_expert"):
        tasks.append(task("安排外部专家访谈并形成纪要。", "外部专家", "高", due, "人工复核"))
    if manual_review.get("needs_financial_due_diligence"):
        tasks.append(task("启动财务专项尽调并复核预测模型。", "财务尽调", "高", due, "人工复核"))
    if manual_review.get("needs_legal_due_diligence"):
        tasks.append(task("启动法律合规专项核查。", "法律尽调", "高", due, "人工复核"))
    if manual_review.get("needs_technical_due_diligence"):
        tasks.append(task("启动技术专项尽调并核验核心技术。", "技术尽调", "高", due, "人工复核"))
    return dedupe_tasks(tasks)


def build_warnings(
    tracking_record: dict[str, Any],
    readiness: str,
    red_flags: list[dict[str, str]],
    process_action: str,
) -> list[str]:
    warnings = [
        "本结果仅用于 Rachel Capital OS 内部流程管理，所有流程动作均需人工复核。",
    ]
    if not tracking_record:
        warnings.append("缺少 V0.9 项目跟踪记录，当前结果主要来自手动输入。")
    if tracking_record.get("project_status") in {"已放弃", "已归档"} and process_action != "归档":
        warnings.append("当前项目状态为已放弃或已归档，本次进入流程属于用户手动覆盖。")
    if readiness in {"低", "不足"}:
        warnings.append("决策准备度偏低，建议先补充关键资料和尽调结论。")
    if red_flags:
        warnings.append("系统识别到一票否决风险，请人工复核。")
    return warnings


def due_diligence_status(gate_checklist: dict[str, list[dict[str, str]]], tracking_record: dict[str, Any]) -> dict[str, str]:
    status = {}
    for category, rows in gate_checklist.items():
        passed = sum(1 for row in rows if row["status"] == "通过")
        total = len(rows)
        status[category] = f"{passed}/{total} 已具备证据"
    status["跟踪任务数量"] = str(len(tracking_record.get("tracking_tasks", [])))
    status["待补充数据数量"] = str(len(listify(tracking_record.get("data_gaps"))))
    return status


def key_value_drivers(card: dict[str, Any]) -> list[str]:
    drivers = []
    for key in ["technology_summary", "product_customer_summary", "market_summary", "financial_summary", "business_model_summary"]:
        value = card.get(key)
        if has_value(value):
            drivers.append(str(value))
    return drivers[:6] or ["待人工补充核心价值驱动因素。"]


def questions_from_gates(gate_checklist: dict[str, list[dict[str, str]]]) -> list[str]:
    questions = []
    for category, rows in gate_checklist.items():
        for row in rows:
            if row["status"] == "待补充":
                questions.append(f"{category}：{row['item']}的证据是否充分？")
    return questions[:12]


def next_steps_from_action(action: str, data_gaps: list[str], questions: list[str], manual_review: dict[str, Any]) -> list[str]:
    steps = {
        "继续观察": ["保留在观察池，按期复查项目资料和行业变化。"],
        "补充资料后复查": ["向项目方补充关键资料后重新生成决策闸门检查表。"],
        "启动深度尽调": ["安排管理层访谈，并启动财务、客户、技术和法务核验。"],
        "提交投委会预审": ["整理投委会预审材料，并确认关键问题清单。"],
        "进入投资决策候选": ["进入投资决策候选池，安排下一轮投委会讨论材料。"],
        "暂缓": ["记录暂缓原因，并设置下次复查节点。"],
        "归档": ["归档当前项目资料，并保留决策日志。"],
        "人工风险复核": ["优先复核一票否决风险，形成专项风险判断。"],
    }.get(action, [])
    steps.extend([f"补充：{item}" for item in data_gaps[:5]])
    steps.extend([f"讨论：{item}" for item in questions[:5]])
    if manual_review.get("needs_external_expert"):
        steps.append("安排外部专家意见。")
    return dedupe(steps)


def evidence_from_keywords(text: str, keywords: list[str]) -> str:
    for keyword in keywords:
        if keyword and keyword in text:
            return f"识别到关键词：{keyword}"
    return ""


def searchable_text(payload: Any) -> str:
    if isinstance(payload, dict):
        return " ".join(f"{key} {searchable_text(value)}" for key, value in payload.items())
    if isinstance(payload, list):
        return " ".join(searchable_text(item) for item in payload)
    return str(payload or "")


def first_value(*values: Any) -> str:
    for value in values:
        if has_value(value):
            return str(value)
    return ""


def has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (list, dict)):
        return bool(value)
    text = str(value).strip()
    return bool(text) and text not in {"无", "缺失", "待补充", "未披露", "None"}


def listify(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if has_value(item)]
    if isinstance(value, dict):
        return [f"{key}: {item}" for key, item in value.items() if has_value(item)]
    if isinstance(value, str):
        return [item.strip() for item in value.replace("；", "\n").replace("、", "\n").splitlines() if item.strip()]
    return [str(value)]


def flatten_values(value: Any) -> list[Any]:
    if isinstance(value, dict):
        result = []
        for item in value.values():
            result.extend(flatten_values(item))
        return result
    if isinstance(value, list):
        result = []
        for item in value:
            result.extend(flatten_values(item))
        return result
    return [value]


def safe_choice(value: Any, options: list[str], fallback: str) -> str:
    text = str(value or "").strip()
    return text if text in options else fallback


def task(name: str, category: str, priority: str, due_date: str, source: str) -> dict[str, str]:
    return {
        "task": name,
        "category": category,
        "priority": priority,
        "due_date": due_date,
        "status": "todo",
        "source": source,
    }


def dedupe(items: list[str]) -> list[str]:
    seen = set()
    result = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result


def dedupe_tasks(tasks: list[dict[str, str]]) -> list[dict[str, str]]:
    seen = set()
    result = []
    for item in tasks:
        key = item.get("task", "")
        if key and key not in seen:
            seen.add(key)
            result.append(item)
    return result


def dedupe_flags(flags: list[dict[str, str]]) -> list[dict[str, str]]:
    seen = set()
    result = []
    for flag in flags:
        key = flag.get("flag", "")
        if key and key not in seen:
            seen.add(key)
            result.append(flag)
    return result
