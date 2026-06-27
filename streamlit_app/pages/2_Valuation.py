import os
from pathlib import Path
import sys

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings
from app.services.valuation_service import (
    ECOSYSTEM_OPTIONS,
    EXIT_OPTIONS,
    GROWTH_OPTIONS,
    MARKET_OPTIONS,
    TargetProfile,
    analyze_target,
    generate_valuation_memo,
)


def default_vault_path() -> str:
    return os.getenv("OBSIDIAN_VAULT_PATH") or settings.obsidian_vault_path or "/Users/rachelao/Documents/Rachel Capital"


def build_profile(
    target_name: str,
    is_listed: bool,
    market: str,
    is_financing_or_transaction: bool,
    is_complete_company: bool,
    is_single_project_spv: bool,
    is_asset_or_resource_based: bool,
    has_revenue: bool,
    is_profitable: bool,
    revenue_growth_status: str,
    cash_flow_stable: bool,
    ecosystem: str,
    exit_path: str,
) -> TargetProfile:
    return TargetProfile(
        target_name=target_name.strip(),
        is_listed=is_listed,
        market=market,
        is_financing_or_transaction=is_financing_or_transaction,
        is_complete_company=is_complete_company,
        is_single_project_spv=is_single_project_spv,
        is_asset_or_resource_based=is_asset_or_resource_based,
        has_revenue=has_revenue,
        is_profitable=is_profitable,
        revenue_growth_status=revenue_growth_status,
        cash_flow_stable=cash_flow_stable,
        ecosystem=ecosystem,
        exit_path=exit_path,
    )


st.set_page_config(page_title="估值驾驶舱 | Rachel Capital OS Platform", layout="wide")
st.title("Rachel 估值驾驶舱")
st.caption("Valuation Cockpit V0.1：标的识别与模型推荐引擎，仅用于本地研究框架准备。")

with st.form("valuation_target_form"):
    st.subheader("标的基本信息")
    col_name, col_market, col_ecosystem = st.columns([1.4, 1, 1.2])
    target_name = col_name.text_input("标的名称", placeholder="例如：中国船舶 / OpenAI / 信宜绿色算力中心")
    market = col_market.selectbox("市场", MARKET_OPTIONS)
    ecosystem = col_ecosystem.selectbox("所属生态", ECOSYSTEM_OPTIONS)

    col_a, col_b, col_c, col_d = st.columns(4)
    is_listed = col_a.checkbox("是否上市", value=market in {"A股", "港股", "美股"})
    is_financing_or_transaction = col_b.checkbox("是否正在融资或交易")
    is_complete_company = col_c.checkbox("是否为完整公司主体", value=True)
    is_single_project_spv = col_d.checkbox("是否为单一项目 / SPV", value=market == "项目型")

    col_e, col_f, col_g, col_h = st.columns(4)
    is_asset_or_resource_based = col_e.checkbox("是否主要依赖资产或资源")
    has_revenue = col_f.checkbox("是否已有收入", value=True)
    is_profitable = col_g.checkbox("是否盈利")
    cash_flow_stable = col_h.checkbox("现金流是否稳定")

    col_growth, col_exit = st.columns(2)
    revenue_growth_status = col_growth.selectbox("收入增长状态", GROWTH_OPTIONS)
    exit_path = col_exit.selectbox("退出路径", EXIT_OPTIONS)

    submitted = st.form_submit_button("识别标的类型")

if submitted:
    if not target_name.strip():
        st.error("请先填写标的名称。")
    else:
        profile = build_profile(
            target_name=target_name,
            is_listed=is_listed,
            market=market,
            is_financing_or_transaction=is_financing_or_transaction,
            is_complete_company=is_complete_company,
            is_single_project_spv=is_single_project_spv,
            is_asset_or_resource_based=is_asset_or_resource_based,
            has_revenue=has_revenue,
            is_profitable=is_profitable,
            revenue_growth_status=revenue_growth_status,
            cash_flow_stable=cash_flow_stable,
            ecosystem=ecosystem,
            exit_path=exit_path,
        )
        classification, recommendation = analyze_target(profile)
        st.session_state["valuation_profile"] = profile
        st.session_state["valuation_classification"] = classification
        st.session_state["valuation_recommendation"] = recommendation

profile = st.session_state.get("valuation_profile")
classification = st.session_state.get("valuation_classification")
recommendation = st.session_state.get("valuation_recommendation")

if profile and classification and recommendation:
    st.divider()
    st.subheader("标的分类结果")
    result_a, result_b, result_c = st.columns(3)
    result_a.metric("主分类", classification.primary_type)
    result_b.metric("辅助分类", "、".join(classification.auxiliary_types) if classification.auxiliary_types else "无")
    result_c.metric("所属生态", profile.ecosystem)

    with st.expander("识别依据", expanded=True):
        for reason in classification.reasons:
            st.write(f"- {reason}")

    st.subheader("模型推荐")
    model_a, model_b, model_c = st.columns(3)
    model_a.markdown("**主模型**")
    model_a.write("、".join(recommendation.primary_models))
    model_b.markdown("**辅助模型**")
    model_b.write("、".join(recommendation.auxiliary_models) if recommendation.auxiliary_models else "无")
    model_c.markdown("**不适用模型**")
    model_c.write("、".join(recommendation.unsuitable_models) if recommendation.unsuitable_models else "无")

    st.info(recommendation.rationale)

    st.subheader("多模型适用性对比")
    st.dataframe(recommendation.comparison_table, use_container_width=True, hide_index=True)

    st.subheader("需要补充的数据")
    for item in recommendation.data_requirements:
        st.write(f"- {item}")

    st.subheader("Obsidian 估值备忘录草稿")
    vault_path = st.text_input("Obsidian Vault 路径", value=default_vault_path())
    output_hint = Path(vault_path).expanduser() / "15_估值引擎" / "估值历史"
    st.caption(f"输出目录：{output_hint}")

    if st.button("生成 Obsidian 估值备忘录草稿"):
        try:
            output_path = generate_valuation_memo(
                profile=profile,
                classification=classification,
                recommendation=recommendation,
                vault_path=vault_path,
            )
        except OSError as exc:
            st.error(f"生成失败：{exc}")
        else:
            st.success(f"已生成：{output_path}")
            st.code(str(output_path), language="text")
else:
    st.info("填写标的基本信息后，点击“识别标的类型”生成分类和模型推荐。")

st.divider()
st.caption("本页面仅用于 Rachel Capital OS 本地研究、估值框架和投资备忘录准备，不连接交易系统，不生成操作结论。")
