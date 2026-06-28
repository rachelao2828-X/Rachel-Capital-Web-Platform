from datetime import date

import pytest

from app.services.valuation_engine.document_parser import parse_uploaded_document
from app.services.valuation_engine.financial_model_parser import parse_financial_model
from app.services.valuation_engine.listed import ListedCompanyProfile, analyze_listed_company
from app.services.valuation_engine.memo_writer import (
    write_basic_valuation_calculation_report,
    write_assumption_confirmation_report,
    write_due_diligence_questions,
    write_listed_memo,
    write_multi_model_valuation_report,
    write_private_market_project_card,
    write_private_market_investment_memo,
    write_private_market_document_analysis,
    write_private_market_document_valuation_framework,
    write_private_market_financial_model_analysis,
    write_private_market_memo,
    write_project_tracking_tasks,
    write_target_profile_confirmation_report,
    update_private_market_project_watchlist,
)
from app.services.valuation_engine.assumption_manager import (
    ASSUMPTION_GROUP_LABELS,
    build_assumption_table,
    finalize_assumption_data,
)
from app.services.valuation_engine.private_market import PrivateMarketProfile, analyze_private_market
from app.services.valuation_engine.investment_memo_builder import build_private_market_investment_memo
from app.services.valuation_engine.private_market_autofill import (
    build_private_market_autofill_from_document,
    build_private_market_autofill_from_financial_model,
)
from app.services.valuation_engine.private_market_extractor import extract_private_market_document
from app.services.valuation_engine.target_profile_detector import build_target_profile
from app.services.valuation_engine.multi_model_valuation import run_multi_model_comparison
from app.services.valuation_engine.project_tracker import build_project_tracking_record, suggest_next_review_date
from app.services.valuation_engine.valuation_calculator import run_basic_private_market_valuation


def listed_profile(**overrides) -> ListedCompanyProfile:
    base = {
        "stock_name": "测试公司",
        "ticker": "000000.SZ",
        "market": "A股",
        "industry": "测试行业",
        "ecosystem": "AI基础设施生态",
        "is_profitable": True,
        "revenue_growth_status": "稳定增长",
        "profit_growth_status": "稳定增长",
        "asset_attribute": "轻资产",
        "cash_flow_stability": "一般",
        "is_strong_cycle": False,
        "is_sotp_suitable": False,
        "is_turnaround": False,
    }
    base.update(overrides)
    return ListedCompanyProfile(**base)


def private_profile(**overrides) -> PrivateMarketProfile:
    base = {
        "target_name": "测试标的",
        "initial_type": "不确定，让系统判断",
        "industry": "测试行业",
        "ecosystem": "AI基础设施生态",
        "is_financing_or_transfer": False,
        "is_complete_company": True,
        "is_single_project_spv": False,
        "is_asset_or_contract_based": False,
        "has_revenue": True,
        "is_profitable": False,
        "revenue_growth_status": "高增长",
        "cash_flow_stable": False,
        "exit_path": "IPO",
    }
    base.update(overrides)
    return PrivateMarketProfile(**base)


def confirmed_target_profile(**overrides) -> dict:
    profile = {
        "target_name": {"detected_value": "测试项目", "confirmed_value": "确认项目", "source": "用户确认", "source_location": "", "confidence": "高", "needs_confirmation": False, "notes": ""},
        "target_type": {"detected_value": "一级市场融资标的", "confirmed_value": "项目公司 / SPV", "source": "用户确认", "source_location": "", "confidence": "高", "needs_confirmation": False, "notes": ""},
        "industry": {"detected_value": "AI基础设施 / 算力 / 数据中心", "confirmed_value": "绿色算力 / IDC", "source": "用户确认", "source_location": "", "confidence": "高", "needs_confirmation": False, "notes": ""},
        "rachel_ecosystem": {"detected_value": "AI基础设施生态", "confirmed_value": "AI基础设施生态", "source": "用户确认", "source_location": "", "confidence": "高", "needs_confirmation": False, "notes": ""},
        "is_financing_or_secondary_transfer": {"detected_value": True, "confirmed_value": True, "source": "用户确认", "source_location": "", "confidence": "高", "needs_confirmation": False, "notes": ""},
        "is_complete_company": {"detected_value": False, "confirmed_value": False, "source": "用户确认", "source_location": "", "confidence": "高", "needs_confirmation": False, "notes": ""},
        "is_single_project_spv": {"detected_value": True, "confirmed_value": True, "source": "用户确认", "source_location": "", "confidence": "高", "needs_confirmation": False, "notes": ""},
        "is_asset_based": {"detected_value": True, "confirmed_value": True, "source": "用户确认", "source_location": "", "confidence": "高", "needs_confirmation": False, "notes": ""},
        "has_revenue": {"detected_value": True, "confirmed_value": True, "source": "用户确认", "source_location": "", "confidence": "高", "needs_confirmation": False, "notes": ""},
        "is_profitable": {"detected_value": True, "confirmed_value": True, "source": "用户确认", "source_location": "", "confidence": "高", "needs_confirmation": False, "notes": ""},
        "revenue_growth_status": {"detected_value": "高增长", "confirmed_value": "稳定增长", "source": "用户确认", "source_location": "", "confidence": "高", "needs_confirmation": False, "notes": ""},
        "cash_flow_stability": {"detected_value": True, "confirmed_value": True, "source": "用户确认", "source_location": "", "confidence": "高", "needs_confirmation": False, "notes": ""},
        "exit_path": {"detected_value": "IPO", "confirmed_value": "并购", "source": "用户确认", "source_location": "", "confidence": "高", "needs_confirmation": False, "notes": ""},
        "classification_reason": "测试判断理由",
        "warnings": [],
    }
    profile.update(overrides)
    return profile


def models(result) -> set[str]:
    return set(result.primary_models + result.auxiliary_models + result.reference_models)


def test_china_shipbuilding_listed_cycle_models() -> None:
    result = analyze_listed_company(
        listed_profile(
            stock_name="中国船舶",
            ticker="600150.SH",
            industry="高端制造",
            ecosystem="船舶与国防生态",
            asset_attribute="重资产",
            revenue_growth_status="周期波动",
            profit_growth_status="周期波动",
            is_strong_cycle=True,
            is_sotp_suitable=True,
        )
    )

    assert {"PB", "周期归一化PE", "EV/EBITDA", "SOTP", "历史周期分位"}.issubset(models(result))


def test_hengrui_listed_stable_profit_models() -> None:
    result = analyze_listed_company(
        listed_profile(
            stock_name="恒瑞医药",
            ticker="600276.SH",
            industry="创新药",
            ecosystem="医疗科技生态",
            is_profitable=True,
            revenue_growth_status="稳定增长",
            profit_growth_status="稳定增长",
            asset_attribute="轻资产",
            cash_flow_stability="稳定",
        )
    )

    assert {"PE", "PEG", "DCF", "EV/EBITDA", "同业比较"}.issubset(models(result))


def test_cambricon_listed_growth_profit_volatility_models() -> None:
    result = analyze_listed_company(
        listed_profile(
            stock_name="寒武纪",
            ticker="688256.SH",
            industry="AI芯片",
            ecosystem="半导体生态",
            is_profitable=False,
            revenue_growth_status="高增长",
            profit_growth_status="亏损",
            asset_attribute="平台型",
            cash_flow_stability="不稳定",
        )
    )

    assert {"PS", "EV/Sales", "远期 PE", "情景估值", "同业比较"}.issubset(models(result))


def test_openai_secondary_transaction_private_market() -> None:
    result = analyze_private_market(
        private_profile(
            target_name="OpenAI 老股交易",
            initial_type="一级市场融资标的",
            is_financing_or_transfer=True,
            is_complete_company=True,
            ecosystem="AI基础设施生态",
            exit_path="IPO",
        )
    )

    assert result.classification.primary_type == "一级市场融资标的"
    assert "未上市成长公司" in result.classification.secondary_types
    assert {"可比融资交易法", "可比上市公司法", "收入倍数", "二级市场映射法", "流动性折扣"}.issubset(models(result))


def test_fluorite_recycling_project_private_market() -> None:
    result = analyze_private_market(
        private_profile(
            target_name="氟化钙污泥回收项目",
            initial_type="项目公司 / SPV",
            is_financing_or_transfer=True,
            is_complete_company=False,
            is_single_project_spv=True,
            ecosystem="高端材料生态",
            exit_path="分红回收",
        )
    )

    assert result.classification.primary_type == "项目公司 / SPV"
    assert "一级市场融资标的" in result.classification.secondary_types
    assert {"DCF", "IRR", "投资回收期", "项目现金流模型", "合同现金流法"}.issubset(models(result))


def test_xinyi_green_compute_center_private_market() -> None:
    result = analyze_private_market(
        private_profile(
            target_name="信宜绿色算力中心",
            initial_type="项目公司 / SPV",
            is_complete_company=False,
            is_single_project_spv=True,
            is_asset_or_contract_based=True,
            cash_flow_stable=True,
            ecosystem="AI基础设施生态",
            exit_path="分红回收",
        )
    )

    assert result.classification.primary_type == "项目公司 / SPV"
    assert "资产型项目" in result.classification.secondary_types
    assert {"DCF", "IRR", "项目现金流模型", "产能价值法", "利用率敏感性", "融资结构敏感性"}.issubset(models(result))


def test_write_listed_memo_path(tmp_path) -> None:
    profile = listed_profile(stock_name="中国船舶", ticker="600150.SH")
    result = analyze_listed_company(profile)

    output = write_listed_memo(profile, result, tmp_path, created=date(2026, 6, 28))

    assert output == tmp_path / "15_估值引擎" / "估值历史" / "已上市公司" / "中国船舶_2026-06-28_已上市公司估值框架.md"
    content = output.read_text(encoding="utf-8")
    assert "type: listed_company_valuation" in content
    assert "target_type: 已上市公司" in content
    assert "public: false" in content


def test_write_private_market_memo_path(tmp_path) -> None:
    profile = private_profile(target_name="信宜绿色算力中心", is_single_project_spv=True, is_complete_company=False)
    result = analyze_private_market(profile)

    output = write_private_market_memo(profile, result, tmp_path, created=date(2026, 6, 28))

    assert output == tmp_path / "15_估值引擎" / "估值历史" / "未上市一级市场" / "信宜绿色算力中心_2026-06-28_未上市一级市场估值框架.md"
    content = output.read_text(encoding="utf-8")
    assert "type: private_market_valuation" in content
    assert "public: false" in content
    assert "target_type: 项目公司 / SPV" in content


def test_extract_private_market_document_recommends_financing_models() -> None:
    parsed = {
        "file_name": "测试AI公司商业计划书.pdf",
        "file_path": "/tmp/测试AI公司商业计划书.pdf",
        "file_type": "pdf",
        "pages": [{"page_number": 1, "text": "项目名称：测试AI公司\n本轮融资金额：人民币5000万元\n投前估值：人民币5亿元\n核心技术：大模型推理平台\n营业收入：2025年收入3000万元"}],
        "raw_text": "项目名称：测试AI公司\n创始人：张三，前华为AI架构师\n技术负责人：李四\n本轮融资金额：人民币5000万元\n投前估值：人民币5亿元\n核心技术：大模型推理平台\n营业收入：2025年收入3000万元",
        "tables": [],
        "warnings": [],
    }

    extraction = extract_private_market_document(parsed)

    assert extraction["project_basic_info"]["project_name"] == "测试AI公司"
    assert extraction["project_basic_info"]["target_type_guess"] == "一级市场融资标的"
    assert "founder_team" in extraction
    assert "business_model" in extraction
    assert "technology_route" in extraction
    assert "products_and_customers" in extraction
    assert "market_space" in extraction
    assert "capacity_data" in extraction
    assert "cost_structure" in extraction
    assert extraction["founder_team"]["founders"]
    assert "可比融资交易法" in extraction["valuation_readiness"]["recommended_models"]
    assert any(row["来源"] == "文件明确披露" for row in extraction["field_assessments"])
    assert all("是否需要确认" in row for row in extraction["field_assessments"])


def test_private_market_document_autofill_project_fields() -> None:
    parsed = {
        "file_name": "信宜绿色算力中心BP.pdf",
        "file_path": "/tmp/信宜绿色算力中心BP.pdf",
        "file_type": "pdf",
        "raw_text": (
            "项目名称：信宜绿色算力中心\n"
            "项目公司 / SPV\n"
            "项目总投资：10亿元\n"
            "建设周期：18个月\n"
            "预计收入：每年2亿元\n"
            "毛利率：45%\n"
            "现金流：项目投产后稳定\n"
            "回收期：5年\n"
            "本轮融资金额：人民币5000万元\n"
            "IPO上市路径"
        ),
        "pages": [],
        "tables": [],
        "warnings": [],
    }
    extraction = extract_private_market_document(parsed)

    autofill = build_private_market_autofill_from_document(extraction)

    assert autofill["target_name"] == "信宜绿色算力中心"
    assert autofill["initial_type"] == "项目公司 / SPV"
    assert autofill["is_single_project_spv"] is True
    assert autofill["is_complete_company"] is False
    assert autofill["is_financing_or_transfer"] is True
    assert autofill["has_revenue"] is True
    assert autofill["cash_flow_stable"] is True
    assert autofill["exit_path"] == "IPO"
    assert autofill["project_total_investment"] == "10亿元"
    assert autofill["construction_period"] == "18个月"


def test_private_market_financial_model_autofill_project_fields(tmp_path) -> None:
    openpyxl = pytest.importorskip("openpyxl")
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "项目测算"
    sheet.append(["项目", "2026E"])
    sheet.append(["预测收入", "2亿元"])
    sheet.append(["净利润", "3000万元"])
    sheet.append(["项目现金流", "4000万元"])
    sheet.append(["项目总投资", "10亿元"])
    sheet.append(["建设周期", "18个月"])
    sheet.append(["回收期", "5年"])
    sheet.append(["产能利用率", "75%"])
    path = tmp_path / "信宜绿色算力中心财务模型.xlsx"
    workbook.save(path)

    financial_model = parse_financial_model(path)
    autofill = build_private_market_autofill_from_financial_model(financial_model)

    assert autofill["target_name"] == "信宜绿色算力中心"
    assert autofill["initial_type"] == "项目公司 / SPV"
    assert autofill["is_single_project_spv"] is True
    assert autofill["is_complete_company"] is False
    assert autofill["has_revenue"] is True
    assert autofill["is_profitable"] is True
    assert autofill["cash_flow_stable"] is True
    assert autofill["is_asset_or_contract_based"] is True
    assert autofill["expected_revenue"] == "2亿元"
    assert autofill["project_total_investment"] == "10亿元"
    assert autofill["utilization_rate"] == "75%"


def test_write_private_market_document_outputs_public_false(tmp_path) -> None:
    parsed = {
        "file_name": "信宜绿色算力中心BP.pdf",
        "file_path": "/tmp/信宜绿色算力中心BP.pdf",
        "file_type": "pdf",
        "pages": [{"page_number": 1, "text": "项目名称：信宜绿色算力中心\n项目总投资：10亿元\n建设周期：18个月\n产能：规划3000个机柜"}],
        "raw_text": "项目名称：信宜绿色算力中心\n项目总投资：10亿元\n建设周期：18个月\n产能：规划3000个机柜",
        "tables": [],
        "warnings": [],
    }
    extraction = extract_private_market_document(parsed)

    analysis_path = write_private_market_document_analysis(extraction, parsed, tmp_path, created=date(2026, 6, 28))
    framework_path = write_private_market_document_valuation_framework(extraction, parsed, tmp_path, created=date(2026, 6, 28))

    assert analysis_path == tmp_path / "15_估值引擎" / "一级市场项目资料解析" / "信宜绿色算力中心_2026-06-28_项目资料解析.md"
    assert framework_path == tmp_path / "15_估值引擎" / "估值历史" / "未上市一级市场" / "信宜绿色算力中心_2026-06-28_未上市一级市场估值框架.md"
    assert "type: private_market_document_analysis" in analysis_path.read_text(encoding="utf-8")
    assert "public: false" in analysis_path.read_text(encoding="utf-8")
    assert "## 4. 创始团队信息" in analysis_path.read_text(encoding="utf-8")
    assert "## 21. 原始资料关键摘录" in analysis_path.read_text(encoding="utf-8")
    assert "## 10. 创始团队对估值的影响" in framework_path.read_text(encoding="utf-8")
    assert "public: false" in framework_path.read_text(encoding="utf-8")


def test_parse_legacy_ppt_and_doc_warn_without_crashing(tmp_path) -> None:
    ppt = tmp_path / "old_deck.ppt"
    doc = tmp_path / "old_doc.doc"
    ppt.write_bytes(b"legacy ppt")
    doc.write_bytes(b"legacy doc")

    ppt_result = parse_uploaded_document(ppt)
    doc_result = parse_uploaded_document(doc)

    assert ppt_result["file_type"] == "ppt"
    assert ppt_result["extraction_quality"] == "failed"
    assert "PPTX" in " ".join(ppt_result["warnings"])
    assert doc_result["file_type"] == "doc"
    assert doc_result["extraction_quality"] == "failed"
    assert "DOCX" in " ".join(doc_result["warnings"])


def test_parse_docx_extracts_paragraphs_and_tables(tmp_path) -> None:
    docx = pytest.importorskip("docx")
    document = docx.Document()
    document.add_heading("项目名称：DOCX测试项目", level=1)
    document.add_paragraph("创始人：王五，连续创业者。融资金额：人民币3000万元。")
    table = document.add_table(rows=2, cols=2)
    table.cell(0, 0).text = "营业收入"
    table.cell(0, 1).text = "2025年5000万元"
    table.cell(1, 0).text = "毛利率"
    table.cell(1, 1).text = "45%"
    path = tmp_path / "docx_test.docx"
    document.save(path)

    result = parse_uploaded_document(path)

    assert result["file_type"] == "docx"
    assert result["extraction_quality"] in {"medium", "high"}
    assert "DOCX测试项目" in result["raw_text"]
    assert result["paragraphs"]
    assert result["tables"]


def test_parse_pptx_extracts_slides_and_tables(tmp_path) -> None:
    pptx = pytest.importorskip("pptx")
    presentation = pptx.Presentation()
    slide = presentation.slides.add_slide(presentation.slide_layouts[1])
    slide.shapes.title.text = "项目名称：PPTX测试项目"
    slide.placeholders[1].text = "创始团队：赵六，前产业公司高管。本轮融资金额：人民币8000万元。"
    table_shape = slide.shapes.add_table(2, 2, 100000, 2500000, 5000000, 1000000)
    table = table_shape.table
    table.cell(0, 0).text = "收入"
    table.cell(0, 1).text = "1亿元"
    table.cell(1, 0).text = "客户"
    table.cell(1, 1).text = "产业客户"
    path = tmp_path / "pptx_test.pptx"
    presentation.save(path)

    result = parse_uploaded_document(path)

    assert result["file_type"] == "pptx"
    assert result["extraction_quality"] in {"medium", "high"}
    assert "PPTX测试项目" in result["raw_text"]
    assert result["slides"]
    assert result["tables"]


def test_parse_xlsx_financial_model_detects_sections_and_fields(tmp_path) -> None:
    openpyxl = pytest.importorskip("openpyxl")
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "收入预测"
    sheet.append(["项目", "2024A", "2025E", "2026E"])
    sheet.append(["营业收入", 1000, 1500, 2200])
    sheet.append(["毛利率", "45%", "48%", "50%"])
    sheet.append(["CAPEX", 300, 200, 150])
    irr = workbook.create_sheet("IRR回收期")
    irr.append(["IRR", "18%"])
    irr.append(["回收期", "5年"])
    path = tmp_path / "financial_model.xlsx"
    workbook.save(path)

    result = parse_financial_model(path)

    assert result["file_type"] == "xlsx"
    assert result["sheets"]
    assert result["raw_preview"]["收入预测"]
    assert result["detected_financial_sections"]["收入预测表"]
    assert result["extracted_financial_data"]["fields"]["历史收入"]["extraction_result"] != "缺失"
    assert "IRR" in result["extracted_financial_data"]["supported_valuation_models"]


def test_parse_csv_financial_model(tmp_path) -> None:
    path = tmp_path / "financial_model.csv"
    path.write_text("项目,2025E\n预测收入,3000\n自由现金流,500\nIRR,20%\n", encoding="utf-8")

    result = parse_financial_model(path)

    assert result["file_type"] == "csv"
    assert result["sheets"][0]["sheet_name"] == "CSV"
    assert result["raw_preview"]["CSV"]
    assert result["extracted_financial_data"]["fields"]["预测收入"]["extraction_result"] != "缺失"
    assert "DCF" in result["extracted_financial_data"]["supported_valuation_models"]


def test_parse_xls_financial_model_warns_without_crashing(tmp_path) -> None:
    path = tmp_path / "legacy_model.xls"
    path.write_bytes(b"legacy xls")

    result = parse_financial_model(path)

    assert result["file_type"] == "xls"
    assert result["extraction_quality"] == "failed"
    assert "XLSX" in " ".join(result["warnings"])


def test_write_financial_model_analysis_and_framework_supplement(tmp_path) -> None:
    financial_model = {
        "file_name": "测试项目财务模型.xlsx",
        "file_path": "/tmp/测试项目财务模型.xlsx",
        "file_type": "xlsx",
        "parser": "openpyxl",
        "sheets": [{"sheet_name": "收入预测", "max_row": 3, "max_column": 3}],
        "tables": [],
        "raw_preview": {"收入预测": [["项目", "2025E"], ["预测收入", 3000]]},
        "detected_financial_sections": {"收入预测表": [{"sheet_name": "收入预测", "matched_keywords": "收入"}]},
        "extracted_financial_data": {
            "field_assessments": [{"field": "预测收入", "extraction_result": "3000", "source_sheet": "收入预测", "source_position": "R2C1", "confidence": "高", "needs_confirmation": "否"}],
            "revenue_related": {"预测收入": {"extraction_result": "3000"}},
            "gross_profit_and_profit": {},
            "costs_and_expenses": {},
            "cash_flow": {},
            "investment_and_capacity": {},
            "financing_and_returns": {},
            "sensitivity_assumptions": {},
            "missing_financial_data": ["自由现金流"],
            "requires_user_confirmation": [],
            "usable_financial_data": ["预测收入"],
            "supported_valuation_models": ["收入倍数"],
            "recommended_supplemental_materials": ["请补充现金流预测表。"],
        },
        "warnings": [],
        "extraction_quality": "medium",
    }
    parsed = {
        "file_name": "测试项目BP.pdf",
        "file_path": "/tmp/测试项目BP.pdf",
        "file_type": "pdf",
        "raw_text": "项目名称：测试项目",
        "pages": [],
        "tables": [],
        "warnings": [],
    }
    extraction = extract_private_market_document(parsed)

    report = write_private_market_financial_model_analysis(financial_model, tmp_path, "测试项目", created=date(2026, 6, 28))
    framework = write_private_market_document_valuation_framework(extraction, parsed, tmp_path, financial_model, created=date(2026, 6, 28))

    report_content = report.read_text(encoding="utf-8")
    framework_content = framework.read_text(encoding="utf-8")
    assert report == tmp_path / "15_估值引擎" / "一级市场财务模型解析" / "测试项目_2026-06-28_财务模型解析.md"
    assert "type: private_market_financial_model_analysis" in report_content
    assert "public: false" in report_content
    assert "## 11. Excel / 财务模型补充信息" in framework_content
    assert "测试项目财务模型.xlsx" in framework_content


def test_build_assumption_table_groups_and_v0_6_inputs() -> None:
    parsed = {
        "file_name": "测试项目BP.pdf",
        "file_path": "/tmp/测试项目BP.pdf",
        "file_type": "pdf",
        "raw_text": "项目名称：测试项目\n本轮融资金额：1000万元\n预测收入：3000万元\n毛利率：45%\nIPO上市路径",
        "pages": [],
        "tables": [],
        "warnings": [],
    }
    extraction = extract_private_market_document(parsed)
    extraction["_source_file"] = parsed["file_name"]
    financial_model = {
        "file_name": "测试项目财务模型.xlsx",
        "extracted_financial_data": {
            "fields": {
                "预测收入": {"extraction_result": "3000万元", "source_sheet": "收入预测", "source_position": "R2C1", "confidence": "高", "needs_confirmation": "否"},
                "毛利率": {"extraction_result": "45%", "source_sheet": "利润表", "source_position": "R3C1", "confidence": "高", "needs_confirmation": "否"},
                "自由现金流": {"extraction_result": "500万元", "source_sheet": "现金流", "source_position": "R4C1", "confidence": "高", "needs_confirmation": "否"},
                "CAPEX": {"extraction_result": "800万元", "source_sheet": "投资计划", "source_position": "R5C1", "confidence": "高", "needs_confirmation": "否"},
                "IRR": {"extraction_result": "20%", "source_sheet": "IRR", "source_position": "R6C1", "confidence": "高", "needs_confirmation": "否"},
            }
        },
    }

    assumption_data = build_assumption_table(extraction, financial_model)
    finalized = finalize_assumption_data(assumption_data)

    assert set(finalized["assumption_groups"]) == set(ASSUMPTION_GROUP_LABELS)
    assert finalized["target_name"] == "测试项目"
    assert finalized["source_files"]
    assert finalized["readiness_summary"]["valuation_readiness_level"] in {"高", "中"}
    assert "valuation_inputs" in finalized
    assert finalized["valuation_inputs"]["revenue"]["预测收入"]["confirmed_value"] == "3000万元"
    assert finalized["valuation_inputs"]["cash_flow"]["自由现金流"]["confirmed_value"] == "500万元"
    assert finalized["ready_for_valuation_calculation"] is True


def test_build_target_profile_detects_basic_fields_from_sources() -> None:
    document_extraction = {
        "_source_file": "白海数智商业计划书.pdf",
        "project_basic_info": {
            "project_name": "白海数智",
            "industry": "AI基础设施 / 算力 / 数据中心",
        },
        "financing_info": {
            "financing_amount": "3000万元",
            "pre_money_valuation": "1亿元",
        },
        "financial_data": {
            "historical_revenue": "1200万元",
            "net_margin": "12%",
            "cash_flow": "300万元",
        },
        "exit_path": {"ipo": "计划 IPO"},
    }
    financial_extraction = {
        "file_name": "白海数智财务模型.xlsx",
        "extracted_financial_data": {
            "fields": {
                "收入增长率": {"extraction_result": "35%"},
                "净利润": {"extraction_result": "200万元"},
            }
        },
    }

    profile = build_target_profile(document_extraction, financial_extraction)

    assert profile["target_name"]["confirmed_value"] == "白海数智"
    assert profile["target_type"]["confirmed_value"] == "一级市场融资标的"
    assert profile["industry"]["confirmed_value"] == "AI基础设施 / 算力 / 数据中心"
    assert profile["rachel_ecosystem"]["confirmed_value"] == "AI基础设施生态"
    assert profile["is_financing_or_secondary_transfer"]["confirmed_value"] is True
    assert profile["has_revenue"]["confirmed_value"] is True
    assert profile["is_profitable"]["confirmed_value"] is True
    assert profile["revenue_growth_status"]["confirmed_value"] == "高增长"
    assert profile["exit_path"]["confirmed_value"] == "IPO"


def test_target_profile_confirmed_values_flow_to_v0_5_v0_9(tmp_path) -> None:
    profile = confirmed_target_profile()
    assumption_data = build_assumption_table({}, {}, profile)

    assert assumption_data["target_name"] == "确认项目"
    assert assumption_data["target_profile"] == profile
    assert any(item["field"] == "标的类型" and item["confirmed_value"] == "项目公司 / SPV" for item in assumption_data["assumption_groups"]["project_basic"])

    basic_result = run_basic_private_market_valuation(assumption_data)
    multi_model_result = run_multi_model_comparison(basic_result, target_profile=profile)
    memo = build_private_market_investment_memo(None, None, assumption_data, basic_result, multi_model_result, target_profile=profile)
    tracking = build_project_tracking_record(memo, {"target_profile": profile})

    assert basic_result["target_name"] == "确认项目"
    assert basic_result["target_type"] == "项目公司 / SPV"
    assert multi_model_result["target_type"] == "项目公司 / SPV"
    assert memo["project_snapshot"]["所属行业"] == "绿色算力 / IDC"
    assert tracking["project_card"]["target_type"] == "项目公司 / SPV"

    output = write_target_profile_confirmation_report(profile, tmp_path, created=date(2026, 6, 28))
    content = output.read_text(encoding="utf-8")
    assert output == tmp_path / "15_估值引擎" / "标的基本信息确认" / "确认项目_2026-06-28_标的基本信息确认.md"
    assert "type: private_market_target_profile_confirmation" in content
    assert "public: false" in content
    assert "## 4. 标的类型判断理由" in content


def test_write_assumption_confirmation_report_public_false(tmp_path) -> None:
    assumption_data = {
        "target_name": "测试项目",
        "source_files": [{"file_name": "测试项目BP.pdf", "source_type": "项目资料"}],
        "assumption_groups": {
            key: [
                {
                    "field": "测试字段",
                    "extracted_value": "1000万元",
                    "confirmed_value": "1000万元",
                    "unit": "万元",
                    "period": "2026",
                    "source": "文件明确披露",
                    "source_file": "测试项目BP.pdf",
                    "source_location": "page 1",
                    "confidence": "高",
                    "needs_confirmation": False,
                    "use_in_valuation": True,
                    "notes": "",
                }
            ]
            for key in ASSUMPTION_GROUP_LABELS
        },
        "readiness_summary": {
            "valuation_readiness_level": "中",
            "reason": "测试原因",
            "ready_for_v0_6_calculation": True,
            "missing_before_calculation": ["退出路径"],
        },
        "ready_for_valuation_calculation": True,
        "valuation_inputs": {"revenue": {}, "cost_profit": {}, "cash_flow": {}, "capex_capacity": {}, "return_valuation": {}, "scenario_sensitivity": {}},
    }

    output = write_assumption_confirmation_report(assumption_data, tmp_path, created=date(2026, 6, 28))
    content = output.read_text(encoding="utf-8")

    assert output == tmp_path / "15_估值引擎" / "关键假设确认" / "测试项目_2026-06-28_关键假设确认.md"
    assert "type: private_market_assumption_confirmation" in content
    assert "public: false" in content
    assert "valuation_readiness: 中" in content
    assert "## 13. 进入 V0.6 自动估值计算前必须补充的数据" in content


def basic_assumption_data() -> dict:
    return {
        "target_name": "测试项目",
        "source_files": [{"file_name": "测试项目BP.pdf", "source_type": "项目资料"}],
        "readiness_summary": {
            "valuation_readiness_level": "高",
            "reason": "关键假设较完整。",
            "ready_for_v0_6_calculation": True,
            "missing_before_calculation": [],
        },
        "ready_for_valuation_calculation": True,
        "valuation_inputs": {
            "revenue": {
                "预测收入": {"confirmed_value": "3000万元", "confidence": "高", "source": "Excel明确披露"},
                "订单金额": {"confirmed_value": "2000万元", "confidence": "中", "source": "文件明确披露"},
            },
            "cost_profit": {
                "净利润": {"confirmed_value": "500万元", "confidence": "高", "source": "Excel明确披露"},
                "EBITDA": {"confirmed_value": "700万元", "confidence": "高", "source": "Excel明确披露"},
            },
            "cash_flow": {
                "自由现金流": {"confirmed_value": "400万元", "confidence": "高", "source": "Excel明确披露"},
            },
            "capex_capacity": {
                "项目总投资": {"confirmed_value": "1200万元", "confidence": "高", "source": "Excel明确披露"},
                "重置成本": {"confirmed_value": "1500万元", "confidence": "中", "source": "文件明确披露"},
            },
            "return_valuation": {
                "收入倍数": {"confirmed_value": "5", "confidence": "中", "source": "用户手动输入"},
                "利润倍数": {"confirmed_value": "12", "confidence": "中", "source": "用户手动输入"},
                "EBITDA 倍数": {"confirmed_value": "8", "confidence": "中", "source": "用户手动输入"},
                "订单倍数": {"confirmed_value": "2", "confidence": "中", "source": "用户手动输入"},
                "折现率": {"confirmed_value": "10%", "confidence": "中", "source": "用户手动输入"},
                "流动性折扣": {"confirmed_value": "10%", "confidence": "中", "source": "用户手动输入"},
            },
            "scenario_sensitivity": {},
        },
        "warnings": [],
    }


def test_run_basic_private_market_valuation_models_and_range() -> None:
    result = run_basic_private_market_valuation(basic_assumption_data())

    assert result["target_name"] == "测试项目"
    assert "收入倍数法" in result["available_models"]
    assert "利润倍数法" in result["available_models"]
    assert "EBITDA 倍数法" in result["available_models"]
    assert "订单倍数法" in result["available_models"]
    assert "DCF 简化法" in result["available_models"]
    assert result["valuation_range"]["method"] == "weighted_range"
    assert result["valuation_range"]["low"] is not None
    assert result["risk_adjustments"][0]["折扣项"] == "流动性折扣"
    assert "for_v0_7_multi_model_comparison" in result
    assert result["confidence_level"] in {"高", "中"}


def test_run_basic_private_market_valuation_uses_only_confirmed_inputs() -> None:
    data = basic_assumption_data()
    data["valuation_inputs"]["revenue"]["预测收入"]["confirmed_value"] = ""

    result = run_basic_private_market_valuation(data)

    revenue_model = next(item for item in result["model_results"] if item["model"] == "收入倍数法")
    assert revenue_model["status"] == "不可计算"
    assert "预测收入或历史收入" in revenue_model["missing_fields"]


def test_write_basic_valuation_calculation_report_public_false(tmp_path) -> None:
    result = run_basic_private_market_valuation(basic_assumption_data())

    output = write_basic_valuation_calculation_report(result, tmp_path, created=date(2026, 6, 28))
    content = output.read_text(encoding="utf-8")

    assert output == tmp_path / "15_估值引擎" / "基础估值计算" / "测试项目_2026-06-28_基础估值计算.md"
    assert "type: private_market_basic_valuation_calculation" in content
    assert "public: false" in content
    assert "## 8. 初步估值区间" in content
    assert "本文件仅用于 Rachel Capital OS 内部研究" in content


def test_run_multi_model_comparison_default_weights_and_range() -> None:
    basic_result = run_basic_private_market_valuation(basic_assumption_data())

    result = run_multi_model_comparison(basic_result)

    assert result["target_name"] == "测试项目"
    assert result["weighted_valuation_range"]["method"] == "weighted_multi_model"
    assert result["weighted_valuation_range"]["base"] is not None
    assert result["weighted_valuation_range"]["included_model_count"] >= 2
    assert result["model_dispersion"]["dispersion_level"] in {"低", "中", "高", "极高"}
    assert result["confidence_level"] in {"高", "中", "低", "仅供框架参考"}
    assert result["for_v0_8_decision_memo"]["recommended_research_action"] in {
        "进入观察池",
        "需要补充数据",
        "进入深度研究",
        "暂不进入估值",
        "等待更多财务或项目数据",
    }


def test_run_multi_model_comparison_user_weights_normalized() -> None:
    basic_result = run_basic_private_market_valuation(basic_assumption_data())
    user_weighting = [
        {"model": "收入倍数法", "user_weight": 90, "include_in_range": True},
        {"model": "利润倍数法", "user_weight": 10, "include_in_range": True},
        {"model": "EBITDA 倍数法", "user_weight": 0, "include_in_range": False},
        {"model": "订单倍数法", "user_weight": 0, "include_in_range": False},
        {"model": "DCF 简化法", "user_weight": 0, "include_in_range": False},
        {"model": "资产重估 / 重置成本法", "user_weight": 0, "include_in_range": False},
    ]

    result = run_multi_model_comparison(basic_result, user_weighting)
    included = [row for row in result["weighting_table"] if row["include_in_range"] and row["normalized_weight"] > 0]

    assert len(included) == 2
    assert round(sum(row["normalized_weight"] for row in included), 6) == 1
    assert any(row["model"] == "EBITDA 倍数法" for row in result["excluded_models"])


def test_write_multi_model_valuation_report_public_false(tmp_path) -> None:
    basic_result = run_basic_private_market_valuation(basic_assumption_data())
    result = run_multi_model_comparison(basic_result)

    output = write_multi_model_valuation_report(result, tmp_path, created=date(2026, 6, 28))
    content = output.read_text(encoding="utf-8")

    assert output == tmp_path / "15_估值引擎" / "多模型估值对比" / "测试项目_2026-06-28_多模型估值对比.md"
    assert "type: private_market_multi_model_valuation" in content
    assert "public: false" in content
    assert "## 7. 加权综合估值区间" in content
    assert "本文件仅用于 Rachel Capital OS 内部研究" in content


def investment_document_extraction() -> dict:
    return {
        "project_basic_info": {
            "project_name": "测试项目",
            "company_name": "测试项目公司",
            "industry": "AI基础设施",
            "rachel_ecosystem_guess": "AI基础设施生态",
            "target_type_guess": "一级市场融资标的",
            "location": "上海",
            "one_sentence_summary": "面向企业客户的 AI 基础设施平台。",
        },
        "founder_team": {
            "founders": ["张三"],
            "co_founders": ["李四"],
            "core_executives": ["王五"],
            "technical_lead": "李四",
            "business_lead": "王五",
            "finance_lead": "赵六",
            "industry_experience": "具备云计算和企业服务经验",
            "team_completeness": "较完整",
            "key_person_dependency": "中",
            "team_risks": "需核验核心团队稳定性",
        },
        "business_model": {
            "revenue_sources": "订阅费和项目交付",
            "customer_type": "企业客户",
            "payment_model": "年度订阅",
            "is_project_based": "部分项目制",
            "is_productized": "是",
            "depends_on_government_or_key_customers": "",
        },
        "technology_route": {
            "core_technology": "推理加速平台",
            "technical_maturity": "已量产",
            "patents": "3 项专利",
            "competitive_advantage": "低延迟和低成本",
        },
        "products_and_customers": {
            "products": "AI 推理平台",
            "customer_type": "企业客户",
            "signed_customers": ["客户A"],
            "orders": "2000万元订单",
            "contracts": "年度合同",
        },
        "market_space": {
            "market_size": "百亿级",
            "market_growth": "高增长",
            "competitors": ["竞品A"],
        },
        "financial_data": {
            "historical_revenue": "1000万元",
            "forecast_revenue": "3000万元",
            "gross_margin": "60%",
            "net_margin": "20%",
            "ebitda": "700万元",
            "cash_flow": "400万元",
            "capex": "1200万元",
        },
        "financing_info": {
            "is_fundraising": "是",
            "financing_amount": "5000万元",
            "pre_money_valuation": "5亿元",
            "post_money_valuation": "5.5亿元",
            "equity_offered": "9.1%",
            "use_of_proceeds": "研发和市场拓展",
        },
        "exit_path": {"ipo": "IPO", "expected_exit_time": "3-5年"},
        "risk_factors": {
            "technology_risk": "需核验性能指标",
            "market_risk": "竞争加剧",
            "team_risk": "关键人员稳定性需核验",
            "data_reliability_risk": "预测数据需审计",
        },
        "valuation_readiness": {
            "missing_data": ["可比融资交易"],
            "questions_for_company": ["请补充客户合同明细"],
        },
    }


def investment_financial_extraction() -> dict:
    return {
        "file_name": "测试项目财务模型.xlsx",
        "extraction_quality": "success",
        "extracted_financial_data": {
            "fields": {
                "预测收入": {"extraction_result": "3000万元"},
                "净利润": {"extraction_result": "500万元"},
                "项目现金流": {"extraction_result": "400万元"},
                "项目总投资": {"extraction_result": "1200万元"},
                "IRR": {"extraction_result": "18%"},
            },
            "missing_financial_data": [],
            "requires_user_confirmation": ["折现率口径"],
        },
    }


def test_build_private_market_investment_memo_full_inputs() -> None:
    assumption_data = basic_assumption_data()
    basic_result = run_basic_private_market_valuation(assumption_data)
    multi_model_result = run_multi_model_comparison(basic_result)

    memo = build_private_market_investment_memo(
        investment_document_extraction(),
        investment_financial_extraction(),
        assumption_data,
        basic_result,
        multi_model_result,
    )

    assert memo["target_name"] == "测试项目"
    assert memo["memo_completeness"] == "高"
    assert memo["project_snapshot"]["项目名称"] == "测试项目"
    assert memo["founder_team_review"]["创始人 / 联合创始人"]
    assert memo["financing_valuation_review"]["多模型估值区间"]
    assert memo["risk_summary"]["技术风险"]
    assert len(memo["due_diligence_questions"]) >= 24
    assert memo["research_action"]["suggested_action"] in {
        "进入观察池",
        "需要补充数据",
        "进入深度研究",
        "暂不进入估值",
        "等待更多财务或项目数据",
    }
    assert "for_v0_9_project_tracking" in memo


def test_build_private_market_investment_memo_low_completeness() -> None:
    memo = build_private_market_investment_memo(None, None, basic_assumption_data(), None, None)

    assert memo["memo_completeness"] == "低"
    assert "项目资料解析" in memo["input_status"]["missing_modules"]
    assert memo["research_action"]["suggested_action"] in {
        "需要补充数据",
        "暂不进入估值",
        "等待更多财务或项目数据",
        "进入观察池",
    }


def test_write_investment_memo_and_due_diligence_public_false(tmp_path) -> None:
    assumption_data = basic_assumption_data()
    basic_result = run_basic_private_market_valuation(assumption_data)
    multi_model_result = run_multi_model_comparison(basic_result)
    memo = build_private_market_investment_memo(
        investment_document_extraction(),
        investment_financial_extraction(),
        assumption_data,
        basic_result,
        multi_model_result,
    )

    memo_output = write_private_market_investment_memo(memo, tmp_path, created=date(2026, 6, 28))
    questions_output = write_due_diligence_questions(memo, tmp_path, created=date(2026, 6, 28))
    memo_content = memo_output.read_text(encoding="utf-8")
    questions_content = questions_output.read_text(encoding="utf-8")

    assert memo_output == tmp_path / "16_投资决策引擎" / "投资备忘录" / "测试项目_2026-06-28_投资备忘录草稿.md"
    assert questions_output == tmp_path / "16_投资决策引擎" / "尽调问题清单" / "测试项目_2026-06-28_尽调问题清单.md"
    assert "type: private_market_investment_memo" in memo_content
    assert "type: private_market_due_diligence_questions" in questions_content
    assert "public: false" in memo_content
    assert "public: false" in questions_content
    assert "## 12. 研究动作建议" in memo_content
    assert "## 5. 财务尽调" in questions_content


def full_investment_memo() -> dict:
    assumption_data = basic_assumption_data()
    basic_result = run_basic_private_market_valuation(assumption_data)
    multi_model_result = run_multi_model_comparison(basic_result)
    return build_private_market_investment_memo(
        investment_document_extraction(),
        investment_financial_extraction(),
        assumption_data,
        basic_result,
        multi_model_result,
    )


def test_build_project_tracking_record_from_memo() -> None:
    memo = full_investment_memo()
    record = build_project_tracking_record(memo, None)

    assert record["target_name"] == "测试项目"
    assert record["project_status"] in {"新建观察", "等待资料", "待深度尽调", "暂缓跟踪"}
    assert record["watchlist_status"] in {"active", "pending_data", "deep_research_candidate", "paused"}
    assert record["project_card"]["target_name"] == "测试项目"
    assert record["next_review_date"]
    assert record["tracking_tasks"]
    assert "for_v1_0_portfolio_decision" in record


def test_project_tracking_manual_override_and_review_dates() -> None:
    memo = full_investment_memo()
    record = build_project_tracking_record(
        memo,
        {
            "project_status": "待深度尽调",
            "watchlist_status": "deep_research_candidate",
            "next_review_date": "2026-07-05",
        },
    )

    assert record["project_status"] == "待深度尽调"
    assert record["watchlist_status"] == "deep_research_candidate"
    assert record["next_review_date"] == "2026-07-05"
    assert suggest_next_review_date("archived", "已归档") == ""


def test_write_project_tracking_outputs_public_false(tmp_path) -> None:
    record = build_project_tracking_record(full_investment_memo(), None)

    card_output = write_private_market_project_card(record, tmp_path, created=date(2026, 6, 28))
    tasks_output = write_project_tracking_tasks(record, tmp_path, created=date(2026, 6, 28))
    watchlist_output = update_private_market_project_watchlist(record, tmp_path, created=date(2026, 6, 28))
    card_content = card_output.read_text(encoding="utf-8")
    tasks_content = tasks_output.read_text(encoding="utf-8")
    watchlist_content = watchlist_output.read_text(encoding="utf-8")

    assert card_output == tmp_path / "03_公司数据库" / "一级市场项目" / "测试项目.md"
    assert tasks_output == tmp_path / "16_投资决策引擎" / "项目跟踪任务" / "测试项目_2026-06-28_项目跟踪任务.md"
    assert watchlist_output == tmp_path / "03_公司数据库" / "一级市场项目" / "一级市场项目观察池.md"
    assert "type: private_market_project" in card_content
    assert "type: private_market_project_tracking_tasks" in tasks_content
    assert "type: private_market_project_watchlist" in watchlist_content
    assert "public: false" in card_content
    assert "public: false" in tasks_content
    assert "public: false" in watchlist_content
    assert "[[测试项目]]" in watchlist_content


def test_update_project_watchlist_replaces_existing_project_row(tmp_path) -> None:
    memo = full_investment_memo()
    record = build_project_tracking_record(memo, None)
    update_private_market_project_watchlist(record, tmp_path, created=date(2026, 6, 28))
    updated = build_project_tracking_record(memo, {"project_status": "等待资料", "watchlist_status": "pending_data"})

    watchlist_output = update_private_market_project_watchlist(updated, tmp_path, created=date(2026, 6, 29))
    content = watchlist_output.read_text(encoding="utf-8")

    assert content.count("| 测试项目 |") == 1
    assert "pending_data" in content
