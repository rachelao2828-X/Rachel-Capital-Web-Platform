from datetime import date

import pytest

from app.services.valuation_engine.document_parser import parse_uploaded_document
from app.services.valuation_engine.financial_model_parser import parse_financial_model
from app.services.valuation_engine.listed import ListedCompanyProfile, analyze_listed_company
from app.services.valuation_engine.memo_writer import (
    write_assumption_confirmation_report,
    write_listed_memo,
    write_private_market_document_analysis,
    write_private_market_document_valuation_framework,
    write_private_market_financial_model_analysis,
    write_private_market_memo,
)
from app.services.valuation_engine.assumption_manager import (
    ASSUMPTION_GROUP_LABELS,
    build_assumption_table,
    finalize_assumption_data,
)
from app.services.valuation_engine.private_market import PrivateMarketProfile, analyze_private_market
from app.services.valuation_engine.private_market_autofill import (
    build_private_market_autofill_from_document,
    build_private_market_autofill_from_financial_model,
)
from app.services.valuation_engine.private_market_extractor import extract_private_market_document


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
