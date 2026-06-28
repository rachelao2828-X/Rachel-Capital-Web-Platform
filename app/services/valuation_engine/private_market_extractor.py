from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from app.services.valuation_engine.model_registry import dedupe


MISSING = "缺失"
DISCLOSED = "文件明确披露"
INFERRED = "系统推断"
CONFIRM = "系统推断"


def extract_private_market_document(parsed_document: dict[str, Any]) -> dict[str, Any]:
    text = normalize(parsed_document.get("raw_text", ""))
    founder_team = build_founder_team(text)
    project_summary = {
        "project_name": first_match(text, [r"(?:项目名称|项目名)[:：]\s*([^\n]{2,80})"]) or guess_project_name(parsed_document, text),
        "company_name": first_match(text, [r"(?:公司名称|企业名称|主体名称)[:：]\s*([^\n]{2,80})"]),
        "one_sentence_summary": guess_summary(text),
        "industry": guess_industry(text),
        "location": first_match(text, [r"(?:所在地|项目地点|注册地址|建设地点|生产基地)[:：]\s*([^\n]{2,80})"]),
        "business_model": guess_business_model(text),
        "target_type_guess": guess_target_type(text),
        "rachel_ecosystem_guess": guess_ecosystem(text),
        "document_date": first_match(text, [r"(?:资料日期|日期|更新时间)[:：]?\s*(20\d{2}[-./年]\d{1,2}[-./月]?\d{0,2})"]),
        "source_file_type": parsed_document.get("file_type", ""),
    }
    commercial_model = {
        "revenue_sources": snippet_after(text, ["收入来源", "收入模式", "盈利模式", "商业模式"]),
        "customer_type": snippet_after(text, ["客户类型", "目标客户", "客户画像"]),
        "payment_model": snippet_after(text, ["付费模式", "收费模式", "定价模式"]),
        "delivery_model": snippet_after(text, ["交付方式", "交付模式"]),
        "is_project_based": yes_no_by_keywords(text, ["项目制", "定制项目"]),
        "is_productized": yes_no_by_keywords(text, ["产品化", "标准化产品"]),
        "is_platform_based": yes_no_by_keywords(text, ["平台型", "平台模式"]),
        "is_asset_or_resource_driven": yes_no_by_keywords(text, ["资产驱动", "资源驱动", "牌照", "产能"]),
        "depends_on_government_or_key_customers": yes_no_by_keywords(text, ["政府订单", "大客户", "客户集中"]),
    }
    product_and_customers = {
        "products": keyword_items(text, ["产品", "平台", "系统", "设备", "服务"]),
        "product_form": snippet_after(text, ["产品形态", "产品形式"]),
        "customer_type": commercial_model["customer_type"],
        "signed_customers": keyword_items(text, ["已签客户", "签约客户", "客户"]),
        "intended_customers": keyword_items(text, ["意向客户", "潜在客户"]),
        "orders": keyword_items(text, ["订单", "在手订单"]),
        "contracts": keyword_items(text, ["合同", "协议", "意向书"]),
        "customer_concentration": snippet_after(text, ["客户集中度", "大客户占比"]),
        "repurchase": snippet_after(text, ["复购", "续费", "留存"]),
        "channels": snippet_after(text, ["渠道", "经销", "直销"]),
    }
    financing_info = {
        "is_fundraising": guess_is_fundraising(text),
        "financing_stage": first_match(text, [r"(?:融资轮次|本轮融资|融资阶段)[:：]\s*([^\n]{2,40})"]),
        "pre_money_valuation": first_match(text, [r"(?:投前估值|Pre-money)[:：]?\s*([^\n，。；;]{2,50})"]),
        "post_money_valuation": first_match(text, [r"(?:投后估值|Post-money)[:：]?\s*([^\n，。；;]{2,50})"]),
        "financing_amount": first_match(text, [r"(?:融资金额|拟融资|募集资金|本轮融资金额)[:：]?\s*([^\n，。；;]{2,50})"]),
        "equity_offered": first_match(text, [r"(?:出让股权|释放股权|股权比例)[:：]?\s*([^\n，。；;]{1,40})"]),
        "previous_round": first_match(text, [r"(?:上一轮|上轮融资|历史融资)[:：]\s*([^\n]{2,100})"]),
        "previous_investors": first_match(text, [r"(?:上一轮投资人|历史投资人|现有投资人)[:：]\s*([^\n]{2,120})"]),
        "use_of_proceeds": snippet_after(text, ["资金用途", "募集资金用途", "融资用途"]),
        "special_terms": snippet_after(text, ["对赌", "特殊条款", "回购条款"]),
    }
    operating_data = {
        "products": product_and_customers["products"],
        "customers": product_and_customers["signed_customers"] or product_and_customers["intended_customers"],
        "orders_or_contracts": dedupe(product_and_customers["orders"] + product_and_customers["contracts"]),
        "capacity": first_match(text, [r"(?:产能|设计产能|规划产能)[:：]?\s*([^\n，。；;]{2,80})"]),
        "capacity_utilization": first_match(text, [r"(?:产能利用率|上架率|负荷率|利用率)[:：]?\s*([^\n，。；;]{1,40})"]),
        "construction_period": first_match(text, [r"(?:建设周期|建设期|建设时间)[:：]?\s*([^\n，。；;]{2,60})"]),
        "revenue_model": guess_revenue_model(text),
    }
    financial_data = {
        "historical_revenue": first_match(text, [r"(?:历史收入|营业收入|收入)[:：]?\s*([^\n，。；;]{2,60})"]),
        "forecast_revenue": first_match(text, [r"(?:预计收入|预测收入|未来收入)[:：]?\s*([^\n，。；;]{2,60})"]),
        "gross_margin": first_match(text, [r"(?:毛利率|综合毛利率)[:：]?\s*([0-9.]+%?)"]),
        "net_margin": first_match(text, [r"(?:净利率|净利润率)[:：]?\s*([0-9.]+%?)"]),
        "ebitda": first_match(text, [r"(?:EBITDA)[:：]?\s*([^\n，。；;]{2,60})"]),
        "capex": first_match(text, [r"(?:资本开支|CAPEX|总投资|项目投资)[:：]?\s*([^\n，。；;]{2,60})"]),
        "opex": first_match(text, [r"(?:运营成本|OPEX|期间费用)[:：]?\s*([^\n，。；;]{2,60})"]),
        "cash_flow": first_match(text, [r"(?:现金流|经营性现金流|自由现金流)[:：]?\s*([^\n，。；;]{2,60})"]),
        "payback_period": first_match(text, [r"(?:回收期|投资回收期)[:：]?\s*([^\n，。；;]{2,40})"]),
        "break_even_time": first_match(text, [r"(?:盈亏平衡|break.?even)[:：]?\s*([^\n，。；;]{2,60})"]),
    }
    technology_and_barriers = {
        "core_technology": snippet_after(text, ["核心技术", "技术路线", "自主研发"]),
        "patents": first_match(text, [r"(?:专利|知识产权)[:：]?\s*([^\n]{2,100})"]),
        "technical_maturity": guess_technical_maturity(text),
        "competitive_advantage": snippet_after(text, ["竞争优势", "核心壁垒", "护城河", "技术壁垒"]),
        "key_dependencies": keyword_items(text, ["供应商", "原材料", "芯片", "设备", "牌照", "关键依赖"]),
    }
    market_and_competition = {
        "market_size": first_match(text, [r"(?:TAM|SAM|SOM|市场规模|市场空间)[:：]?\s*([^\n]{2,100})"]),
        "market_growth": first_match(text, [r"(?:市场增速|复合增长率|CAGR|行业景气度)[:：]?\s*([^\n]{2,80})"]),
        "competitors": keyword_items(text, ["竞争对手", "竞品", "同业", "竞争格局"]),
        "comparable_listed_companies": keyword_items(text, ["上市公司", "可比公司"]),
        "comparable_private_companies": keyword_items(text, ["未上市", "创业公司", "独角兽"]),
    }
    capacity_and_cost = {
        "designed_capacity": first_match(text, [r"(?:设计产能|规划产能)[:：]?\s*([^\n，。；;]{2,80})"]),
        "current_capacity": first_match(text, [r"(?:当前产能|现有产能)[:：]?\s*([^\n，。；;]{2,80})"]),
        "capacity_expansion_plan": snippet_after(text, ["产能爬坡", "在建产能", "扩产计划", "产能规划"]),
        "unit_price": first_match(text, [r"(?:单位售价|单价|ASP)[:：]?\s*([^\n，。；;]{2,60})"]),
        "unit_cost": first_match(text, [r"(?:单位成本|单耗成本)[:：]?\s*([^\n，。；;]{2,60})"]),
        "raw_material_cost": first_match(text, [r"(?:原材料成本|材料成本)[:：]?\s*([^\n，。；;]{2,60})"]),
        "energy_cost": first_match(text, [r"(?:能耗成本|电费|能源成本)[:：]?\s*([^\n，。；;]{2,60})"]),
        "labor_cost": first_match(text, [r"(?:人工成本|人员成本|薪酬成本)[:：]?\s*([^\n，。；;]{2,60})"]),
        "depreciation": first_match(text, [r"(?:折旧|设备折旧)[:：]?\s*([^\n，。；;]{2,60})"]),
        "maintenance_cost": first_match(text, [r"(?:运维成本|维护成本)[:：]?\s*([^\n，。；;]{2,60})"]),
        "environmental_cost": first_match(text, [r"(?:环保成本|环保投入)[:：]?\s*([^\n，。；;]{2,60})"]),
        "compliance_cost": first_match(text, [r"(?:合规成本|认证成本)[:：]?\s*([^\n，。；;]{2,60})"]),
    }
    capacity_data = {
        "designed_capacity": capacity_and_cost["designed_capacity"],
        "current_capacity": capacity_and_cost["current_capacity"],
        "capacity_expansion_plan": capacity_and_cost["capacity_expansion_plan"],
        "capacity_utilization": operating_data["capacity_utilization"],
        "construction_period": operating_data["construction_period"],
        "unit_price": capacity_and_cost["unit_price"],
        "unit_cost": capacity_and_cost["unit_cost"],
        "production_base": first_match(text, [r"(?:生产基地|建设地点|项目地点)[:：]?\s*([^\n，。；;]{2,80})"]),
        "equipment_investment": first_match(text, [r"(?:设备投入|设备投资)[:：]?\s*([^\n，。；;]{2,80})"]),
        "production_lines": first_match(text, [r"(?:产线数量|生产线)[:：]?\s*([^\n，。；;]{2,60})"]),
    }
    cost_structure = {
        "capex": financial_data["capex"],
        "opex": financial_data["opex"],
        "raw_material_cost": capacity_and_cost["raw_material_cost"],
        "energy_cost": capacity_and_cost["energy_cost"],
        "labor_cost": capacity_and_cost["labor_cost"],
        "depreciation": capacity_and_cost["depreciation"],
        "maintenance_cost": capacity_and_cost["maintenance_cost"],
        "environmental_cost": capacity_and_cost["environmental_cost"],
        "compliance_cost": capacity_and_cost["compliance_cost"],
        "unit_economics": snippet_after(text, ["单位经济模型", "单位经济", "单台毛利", "单柜收入"]),
    }
    exit_path = {
        "ipo": snippet_after(text, ["IPO", "上市计划", "上市路径"]),
        "ma": snippet_after(text, ["并购退出", "收购退出", "产业并购"]),
        "dividend_recovery": snippet_after(text, ["分红回收", "分红", "回购"]),
        "asset_sale": snippet_after(text, ["资产出售", "资产转让"]),
        "equity_transfer": snippet_after(text, ["股权转让", "老股转让"]),
        "strategic_acquisition": snippet_after(text, ["产业方收购", "战略收购"]),
        "expected_exit_time": first_match(text, [r"(?:退出时间|退出预期|上市时间)[:：]?\s*([^\n，。；;]{2,60})"]),
        "comparable_exit_cases": keyword_items(text, ["退出案例", "并购案例", "上市案例"]),
    }
    risk_factors = {
        "technology_risk": risk_snippet(text, "技术"),
        "market_risk": risk_snippet(text, "市场"),
        "customer_risk": risk_snippet(text, "客户"),
        "policy_risk": risk_snippet(text, "政策"),
        "financing_risk": risk_snippet(text, "融资"),
        "execution_risk": risk_snippet(text, "执行") or risk_snippet(text, "产能"),
        "team_risk": team_risk_summary(founder_team),
        "key_person_risk": founder_team["key_person_dependency"],
        "data_reliability_risk": "资料多为项目方披露，关键经营、财务、订单和团队履历需交叉验证。",
        "compliance_risk": risk_snippet(text, "合规") or risk_snippet(text, "环保"),
    }
    valuation_readiness = build_valuation_readiness(
        project_summary,
        founder_team,
        commercial_model,
        product_and_customers,
        financing_info,
        operating_data,
        financial_data,
        technology_and_barriers,
        market_and_competition,
        capacity_data,
        cost_structure,
        exit_path,
        risk_factors,
    )
    extraction = {
        "project_basic_info": project_summary,
        "founder_team": founder_team,
        "business_model": commercial_model,
        "technology_route": technology_and_barriers,
        "products_and_customers": product_and_customers,
        "market_space": market_and_competition,
        "financial_data": financial_data,
        "financing_info": financing_info,
        "capacity_data": capacity_data,
        "cost_structure": cost_structure,
        "exit_path": exit_path,
        "risk_factors": risk_factors,
        "valuation_readiness": valuation_readiness,
    }
    extraction["field_assessments"] = build_field_assessments(extraction, text)
    extraction["raw_excerpt"] = build_excerpt(text)
    return extraction


def build_founder_team(text: str) -> dict[str, Any]:
    founders = keyword_items(text, ["创始人", "创始团队"], limit=6)
    co_founders = keyword_items(text, ["联合创始人", "合伙人"], limit=6)
    executives = keyword_items(text, ["核心高管", "管理团队", "CEO", "CTO", "CFO", "COO"], limit=8)
    technical_lead = first_match(text, [r"(?:技术负责人|CTO|首席科学家)[:：]?\s*([^\n，。；;]{2,50})"])
    business_lead = first_match(text, [r"(?:商业负责人|销售负责人|业务负责人|COO)[:：]?\s*([^\n，。；;]{2,50})"])
    finance_lead = first_match(text, [r"(?:财务负责人|CFO|财务总监)[:：]?\s*([^\n，。；;]{2,50})"])
    team_gaps = []
    if not technical_lead and not any("CTO" in item or "技术" in item for item in executives):
        team_gaps.append("技术负责人信息待确认")
    if not business_lead and not any("销售" in item or "商业" in item or "业务" in item for item in executives):
        team_gaps.append("商业化负责人信息待确认")
    if not finance_lead:
        team_gaps.append("财务与资本市场负责人信息待确认")
    key_dependency = "存在潜在关键人依赖，需核验核心创始人持股、分工和团队稳定性。" if founders and not co_founders else "关键人依赖需结合股权结构和核心人员稳定性进一步确认。"
    risks = []
    if team_gaps:
        risks.append("团队结构缺口：" + "、".join(team_gaps))
    if not founders and not executives:
        risks.append("创始团队披露不足，团队履历无法验证。")
    if key_dependency:
        risks.append(key_dependency)
    return {
        "founders": founders,
        "co_founders": co_founders,
        "core_executives": executives,
        "technical_lead": technical_lead,
        "business_lead": business_lead,
        "finance_lead": finance_lead,
        "advisors_or_board": keyword_items(text, ["董事", "顾问", "董事会", "科学顾问"], limit=6),
        "education_background": snippet_after(text, ["高校", "博士", "硕士", "本科", "教育背景"]),
        "industry_experience": snippet_after(text, ["产业经验", "行业经验", "从业"]),
        "entrepreneurial_experience": snippet_after(text, ["创业经历", "连续创业", "创办"]),
        "research_background": snippet_after(text, ["科研院所", "论文", "专利", "研究员", "教授"]),
        "big_company_background": snippet_after(text, ["大厂", "华为", "阿里", "腾讯", "字节", "百度", "微软", "谷歌"]),
        "industrial_resource_background": snippet_after(text, ["产业资源", "客户资源", "渠道资源", "供应链资源"]),
        "fundraising_experience": snippet_after(text, ["融资经验", "资本市场", "投资人"]),
        "team_completeness": team_completeness(team_gaps, founders, executives),
        "team_gaps": team_gaps,
        "key_person_dependency": key_dependency,
        "team_risks": risks,
    }


def build_valuation_readiness(*sections: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for section in sections:
        merged.update(section)

    target_type = str(merged.get("target_type_guess") or "")
    recommended_models = models_for_target_type(target_type)
    usable_data: list[str] = []
    missing_data: list[str] = []
    questions: list[str] = []
    required_fields = {
        "项目名称": merged.get("project_name"),
        "创始团队": merged.get("founders") or merged.get("core_executives"),
        "行业": merged.get("industry"),
        "商业模式": merged.get("business_model") or merged.get("revenue_sources"),
        "产品与客户": merged.get("products") or merged.get("customers"),
        "融资金额": merged.get("financing_amount"),
        "收入": merged.get("historical_revenue") or merged.get("forecast_revenue"),
        "毛利率": merged.get("gross_margin"),
        "产能": merged.get("designed_capacity") or merged.get("current_capacity") or merged.get("capacity"),
        "市场空间": merged.get("market_size"),
        "退出路径": merged.get("ipo") or merged.get("ma") or merged.get("dividend_recovery") or merged.get("asset_sale"),
    }
    for label, value in required_fields.items():
        if has_value(value):
            usable_data.append(label)
        else:
            missing_data.append(label)
            questions.append(f"请补充或确认：{label}。")

    if merged.get("team_gaps"):
        questions.append("请补充创始团队分工、履历证明、股权结构、核心人员稳定性与关键人依赖情况。")
    unavailable_models = unavailable_models_for_missing(missing_data)
    data_confidence_level = level_from_missing(missing_data)
    valuation_confidence_level = valuation_level(data_confidence_level, merged.get("team_gaps", []))
    return {
        "recommended_models": recommended_models,
        "usable_data": usable_data,
        "missing_data": missing_data,
        "questions_for_company": dedupe(questions),
        "data_confidence_level": data_confidence_level,
        "valuation_confidence_level": valuation_confidence_level,
        "ready_for_preliminary_valuation": valuation_confidence_level in {"高", "中"} and len(missing_data) <= 6,
        "unavailable_models": unavailable_models,
    }


def models_for_target_type(target_type: str) -> list[str]:
    if target_type == "一级市场融资标的":
        return ["可比融资交易法", "可比上市公司法", "融资轮次估值锚", "收入倍数", "利润倍数", "订单倍数", "IPO / 并购退出倒推", "退出路径折扣"]
    if target_type == "项目公司 / SPV":
        return ["DCF", "IRR", "投资回收期", "项目现金流模型", "合同现金流法", "产能价值法", "利用率敏感性分析", "融资结构敏感性分析"]
    if target_type == "资产型项目":
        return ["资产重估法", "重置成本法", "单位产能估值", "资源储量估值", "合同现金流估值", "可交易资产比较法"]
    return ["可比上市公司法", "可比融资交易法", "收入倍数", "ARR倍数", "二级市场映射法", "流动性折扣", "上市概率折扣"]


def unavailable_models_for_missing(missing_data: list[str]) -> list[str]:
    unavailable = []
    if "收入" in missing_data:
        unavailable.extend(["收入倍数", "ARR倍数"])
    if "产能" in missing_data:
        unavailable.extend(["产能价值法", "利用率敏感性分析"])
    if "退出路径" in missing_data:
        unavailable.extend(["IPO / 并购退出倒推", "退出路径折扣"])
    if "市场空间" in missing_data:
        unavailable.append("二级市场映射法")
    return dedupe(unavailable)


def build_field_assessments(extraction: dict[str, Any], text: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    inferred_fields = {
        "one_sentence_summary",
        "target_type_guess",
        "rachel_ecosystem_guess",
        "source_file_type",
        "recommended_models",
        "missing_data",
        "questions_for_company",
        "data_confidence_level",
        "valuation_confidence_level",
        "ready_for_preliminary_valuation",
        "unavailable_models",
        "team_completeness",
        "team_gaps",
        "key_person_dependency",
        "team_risks",
    }
    for section_name, section in extraction.items():
        if section_name in {"field_assessments", "raw_excerpt"} or not isinstance(section, dict):
            continue
        for field, value in section.items():
            display = display_value(value)
            if not display:
                source = MISSING
                confidence = "缺失"
                needs_confirmation = True
            elif field in inferred_fields:
                source = INFERRED
                confidence = "中"
                needs_confirmation = True
            elif display and display in text:
                source = DISCLOSED
                confidence = "高"
                needs_confirmation = False
            else:
                source = CONFIRM
                confidence = "低"
                needs_confirmation = True
            rows.append(
                {
                    "分组": section_name,
                    "字段": field,
                    "提取结果": display or "未披露",
                    "来源": source,
                    "可信度": confidence,
                    "是否需要确认": "是" if needs_confirmation else "否",
                }
            )
    return rows


def normalize(text: str) -> str:
    return re.sub(r"[ \t]+", " ", text or "").strip()


def first_match(text: str, patterns: list[str]) -> str:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return clean(match.group(1))
    return ""


def guess_project_name(parsed_document: dict[str, Any], text: str) -> str:
    name = Path(str(parsed_document.get("file_name") or "未命名项目")).stem
    name = re.sub(r"[_\-\s]*(项目资料解析|商业计划书|BP|可研报告)$", "", name, flags=re.IGNORECASE).strip()
    if name:
        return name[:60]
    first_line = next((line.strip() for line in text.splitlines() if len(line.strip()) >= 3), "")
    return clean(first_line[:40]) or "未命名项目"


def guess_summary(text: str) -> str:
    for line in text.splitlines():
        cleaned = clean(line)
        if 12 <= len(cleaned) <= 140 and any(keyword in cleaned for keyword in ["项目", "公司", "平台", "产品", "服务", "建设"]):
            return cleaned
    return clean(text[:120])


def guess_industry(text: str) -> str:
    mapping = [
        ("AI基础设施", ["算力", "AI", "大模型", "数据中心", "GPU"]),
        ("半导体", ["半导体", "芯片", "晶圆", "封装", "设备"]),
        ("机器人", ["机器人", "具身智能", "自动化"]),
        ("高端材料", ["材料", "复合材料", "碳纤维", "陶瓷"]),
        ("医疗科技", ["医疗", "药", "器械", "诊断"]),
        ("新能源 / 绿色资产", ["储能", "光伏", "风电", "绿色", "碳"]),
    ]
    return keyword_mapping(text, mapping, "待确认")


def guess_ecosystem(text: str) -> str:
    mapping = [
        ("AI基础设施生态", ["算力", "AI", "大模型", "数据中心", "GPU"]),
        ("半导体生态", ["半导体", "芯片", "晶圆", "封装"]),
        ("华为生态", ["华为", "鸿蒙", "昇腾", "鲲鹏"]),
        ("机器人生态", ["机器人", "具身智能"]),
        ("高端材料生态", ["材料", "碳纤维", "陶瓷"]),
        ("医疗科技生态", ["医疗", "药", "器械", "诊断"]),
    ]
    return keyword_mapping(text, mapping, "其他")


def guess_target_type(text: str) -> str:
    if any(keyword in text for keyword in ["SPV", "项目公司", "建设期", "项目总投资", "IRR", "回收期"]):
        return "项目公司 / SPV"
    if any(keyword in text for keyword in ["资产", "资源储量", "重置成本", "租金", "长期合同"]):
        return "资产型项目"
    if any(keyword in text for keyword in ["融资", "投前估值", "投后估值", "Pre-IPO", "出让股权", "老股"]):
        return "一级市场融资标的"
    return "未上市成长公司"


def guess_is_fundraising(text: str) -> bool | None:
    if any(keyword in text for keyword in ["拟融资", "本轮融资", "融资金额", "出让股权", "投前估值", "投后估值"]):
        return True
    if any(keyword in text for keyword in ["暂无融资计划", "不融资"]):
        return False
    return None


def guess_business_model(text: str) -> str:
    if "订阅" in text or "SaaS" in text or "ARR" in text:
        return "订阅 / SaaS 收入模式"
    if any(keyword in text for keyword in ["销售", "经销", "订单"]):
        return "产品销售 / 订单交付模式"
    if any(keyword in text for keyword in ["合同", "租赁", "服务费"]):
        return "合同现金流 / 服务费模式"
    return snippet_after(text, ["商业模式", "盈利模式", "收入模式"])


def guess_revenue_model(text: str) -> str:
    return snippet_after(text, ["收入模式", "盈利模式", "收费模式"]) or guess_business_model(text)


def guess_technical_maturity(text: str) -> str:
    if any(keyword in text for keyword in ["量产", "规模化交付", "已投产"]):
        return "已量产 / 已交付，需核验客户与产能数据"
    if any(keyword in text for keyword in ["中试", "试生产", "样机"]):
        return "中试或样机阶段，需核验技术成熟度"
    if any(keyword in text for keyword in ["研发", "实验室", "概念验证"]):
        return "研发阶段，技术成熟度需重点确认"
    return ""


def team_completeness(team_gaps: list[str], founders: list[str], executives: list[str]) -> str:
    if not founders and not executives:
        return "低：创始团队与核心高管披露不足"
    if team_gaps:
        return "中：团队已部分披露，但存在结构缺口"
    return "较高：创始团队、技术、商业和财务角色披露相对完整，仍需核验"


def team_risk_summary(founder_team: dict[str, Any]) -> str:
    risks = founder_team.get("team_risks", [])
    return "；".join(risks) if risks else "团队风险暂未充分披露，需核验核心人员稳定性。"


def keyword_items(text: str, keywords: list[str], limit: int = 5) -> list[str]:
    items: list[str] = []
    for line in text.splitlines():
        cleaned = clean(line)
        if 6 <= len(cleaned) <= 120 and any(keyword in cleaned for keyword in keywords):
            items.append(cleaned)
        if len(items) >= limit:
            break
    return dedupe(items)


def snippet_after(text: str, keywords: list[str], length: int = 110) -> str:
    for keyword in keywords:
        index = text.find(keyword)
        if index >= 0:
            return clean(text[index : index + length])
    return ""


def risk_snippet(text: str, risk_type: str) -> str:
    for line in text.splitlines():
        cleaned = clean(line)
        if "风险" in cleaned and risk_type in cleaned:
            return cleaned[:120]
    return ""


def keyword_mapping(text: str, mapping: list[tuple[str, list[str]]], fallback: str) -> str:
    for label, keywords in mapping:
        if any(keyword in text for keyword in keywords):
            return label
    return fallback


def yes_no_by_keywords(text: str, keywords: list[str]) -> str:
    return "是，需核验" if any(keyword in text for keyword in keywords) else ""


def build_excerpt(text: str) -> str:
    lines = [clean(line) for line in text.splitlines() if len(clean(line)) >= 20]
    return "\n".join(lines[:12])[:1800]


def level_from_missing(missing_data: list[str]) -> str:
    if len(missing_data) <= 3:
        return "高"
    if len(missing_data) <= 6:
        return "中"
    return "低"


def valuation_level(data_level: str, team_gaps: list[str]) -> str:
    if data_level == "高" and not team_gaps:
        return "高"
    if data_level in {"高", "中"}:
        return "中"
    return "低"


def has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, list):
        return bool(value)
    if isinstance(value, bool):
        return True
    return bool(str(value).strip())


def display_value(value: Any) -> str:
    if isinstance(value, list):
        return "、".join(str(item) for item in value) if value else ""
    if value is None:
        return ""
    return str(value)


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip(" -:：\t\r\n")
