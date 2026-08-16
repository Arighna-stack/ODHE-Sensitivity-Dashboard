import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from odhe_model import (
    DESIGN_BASIS,
    PARAM_SPECS,
    ProcessParameters,
    compute_msp,
    cost_breakdown,
    global_sobol_analysis,
    tornado_analysis,
)
from odhe_model.economics import ethylene_production_annual

st.set_page_config(page_title="ODHE Techno-Economic Dashboard", page_icon="⚗️", layout="wide")

st.title("⚗️ ODHE Techno-Economic Sensitivity Dashboard")
st.markdown(
    "Interactive techno-economic model for ethylene production via **Oxidative "
    "Dehydrogenation of Ethane (ODHE)**. Adjust feedstock, utility, process, and "
    "financial parameters to see their real-time effect on the **Minimum Selling "
    "Price (MSP)** of ethylene, then quantify which parameters matter most via "
    "local (tornado) and global (Sobol) sensitivity analysis."
)

# ---------------------------------------------------------------------------
# Sidebar — parameter inputs, grouped, single source of truth from PARAM_SPECS
# ---------------------------------------------------------------------------
st.sidebar.header("🔧 Scenario Parameters")
if st.sidebar.button("↺ Reset to defaults", width="stretch"):
    for name in PARAM_SPECS:
        st.session_state.pop(f"input_{name}", None)

groups = {}
for name, spec in PARAM_SPECS.items():
    groups.setdefault(spec["group"], []).append(name)

values = {}
for group_name, names in groups.items():
    with st.sidebar.expander(group_name, expanded=(group_name != "Financial")):
        for name in names:
            spec = PARAM_SPECS[name]
            fmt = "%.3f" if spec["step"] < 1 else "%.0f"
            values[name] = st.slider(
                f"{spec['label']} ({spec['unit']})",
                min_value=spec["min"],
                max_value=spec["max"],
                value=spec["default"],
                step=spec["step"],
                format=fmt,
                key=f"input_{name}",
            )

params = ProcessParameters(**values)

st.sidebar.divider()
ethylene_market_price = st.sidebar.number_input(
    "Ethylene Market Price ($/ton) — for margin only",
    min_value=500.0, max_value=3000.0, value=1300.0, step=25.0,
)

# ---------------------------------------------------------------------------
# Headline metrics
# ---------------------------------------------------------------------------
breakdown = cost_breakdown(params)
msp = breakdown["Total Annual Cost"] / ethylene_production_annual(params)
production = ethylene_production_annual(params)
margin = ethylene_market_price - msp

c1, c2, c3, c4 = st.columns(4)
c1.metric("💰 MSP", f"${msp:,.0f} /ton")
c2.metric("🏭 Ethylene Output", f"{production:,.0f} tons/yr")
c3.metric("📦 Total Annual Cost", f"${breakdown['Total Annual Cost']/1e6:,.1f} MM/yr")
c4.metric(
    "📈 Margin vs Market Price",
    f"${margin:,.0f} /ton",
    delta=f"{margin:,.0f}",
    delta_color="normal" if margin >= 0 else "inverse",
)

st.divider()

tab_overview, tab_tornado, tab_sobol, tab_export = st.tabs(
    ["📊 Overview & Cost Breakdown", "🌪️ Local Sensitivity (Tornado)",
     "🌐 Global Sensitivity (Sobol)", "📥 Export"]
)

# ---------------------------------------------------------------------------
# Overview tab
# ---------------------------------------------------------------------------
with tab_overview:
    left, right = st.columns([3, 2])

    cost_df = (
        pd.DataFrame(
            {"Category": k, "Annual Cost ($)": v}
            for k, v in breakdown.items()
            if k != "Total Annual Cost"
        )
        .sort_values("Annual Cost ($)", ascending=True)
    )

    with left:
        fig = px.bar(
            cost_df, x="Annual Cost ($)", y="Category", orientation="h",
            title="Annual Cost Breakdown", text_auto=".2s",
        )
        fig.update_layout(yaxis_title="", xaxis_title="Annual Cost ($/yr)")
        st.plotly_chart(fig, width="stretch")

    with right:
        pie = px.pie(cost_df, names="Category", values="Annual Cost ($)", hole=0.45,
                     title="Cost Share")
        st.plotly_chart(pie, width="stretch")

    st.subheader("Cost Breakdown Table")
    table_df = pd.DataFrame(
        {"Category": list(breakdown.keys()), "Annual Cost ($)": list(breakdown.values())}
    )
    table_df["Share of Total"] = table_df["Annual Cost ($)"] / breakdown["Total Annual Cost"]
    st.dataframe(
        table_df.style.format({"Annual Cost ($)": "${:,.0f}", "Share of Total": "{:.1%}"}),
        width="stretch", hide_index=True,
    )

    with st.expander("Process design basis & modeling notes"):
        st.markdown(f"""
- Nameplate ethylene capacity: **{DESIGN_BASIS.ethylene_capacity_tph:.1f} t/hr**, fixed regardless of process performance — the plant is dispatched to hit target output.
- Baseline ethane feed: **{DESIGN_BASIS.base_ethane_flow_tph:.1f} t/hr** at design conversion/selectivity; required feed scales inversely with **conversion × selectivity** as those parameters move away from baseline (lower efficiency ⇒ more feed needed for the same output ⇒ higher cost).
- Oxygen feed is derived from the ethane feed and the **C2H6:O2 ratio** slider.
- CAPEX is annualized with the capital recovery factor: `CRF = r(1+r)^n / ((1+r)^n - 1)`.
- Fixed O&M is modeled as a **% of CAPEX/year** (adjustable) rather than a hardcoded constant, which is standard TEA practice and keeps the assumption transparent.
- This is a screening-level TEA model intended to demonstrate sensitivity-analysis methodology, not a substitute for a rigorous Aspen/HYSYS-based cost estimate.
""")

# ---------------------------------------------------------------------------
# Tornado tab
# ---------------------------------------------------------------------------
with tab_tornado:
    st.subheader("One-at-a-time sensitivity: full slider-range sweep")
    st.caption(
        "Each parameter is swept across its entire slider range (min → max) while "
        "all others are held at their current sidebar values, then re-evaluated "
        "through the same MSP model. Bars are sorted by impact on MSP."
    )

    param_options = {spec["label"]: name for name, spec in PARAM_SPECS.items()}
    selected_labels = st.multiselect(
        "Parameters to include", list(param_options.keys()),
        default=list(param_options.keys()),
    )
    selected_names = [param_options[lbl] for lbl in selected_labels] or list(PARAM_SPECS.keys())

    tdf = tornado_analysis(params, selected_names)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=tdf["Parameter"], x=tdf["Impact"], base=tdf["Low_MSP"],
        orientation="h", marker_color="#2E86AB",
        hovertemplate="%{y}<br>MSP range: $%{base:,.0f} – $%{x:,.0f}<extra></extra>",
        customdata=tdf["High_MSP"],
    ))
    fig.add_vline(x=msp, line_dash="dash", line_color="gray",
                   annotation_text=f"Base MSP ${msp:,.0f}")
    fig.update_layout(
        title="Tornado Chart — Impact on MSP ($/ton)",
        xaxis_title="MSP ($/ton)", yaxis_title="", height=max(350, 45 * len(tdf)),
    )
    st.plotly_chart(fig, width="stretch")

    st.dataframe(
        tdf[["Parameter", "Low_MSP", "Base_MSP", "High_MSP", "Impact"]]
        .sort_values("Impact", ascending=False)
        .style.format({"Low_MSP": "${:,.0f}", "Base_MSP": "${:,.0f}",
                        "High_MSP": "${:,.0f}", "Impact": "${:,.0f}"}),
        width="stretch", hide_index=True,
    )

# ---------------------------------------------------------------------------
# Sobol tab
# ---------------------------------------------------------------------------
with tab_sobol:
    st.subheader("Variance-based global sensitivity (Sobol indices)")
    st.caption(
        "Unlike the tornado chart, Sobol indices account for the full parameter "
        "space and interaction effects between parameters simultaneously. "
        "S1 = first-order effect of a parameter alone; ST = total effect including "
        "interactions with all other parameters. Computed against the same MSP "
        "model as the live calculator above — cached, so it only recomputes if the "
        "parameter set or sample size changes."
    )

    sobol_names = st.multiselect(
        "Parameters to include in Sobol analysis", list(param_options.keys()),
        default=list(param_options.keys()), key="sobol_params",
    )
    n_samples = st.select_slider("Sample size (higher = more accurate, slower)",
                                  options=[128, 256, 512, 1024, 2048], value=512)

    sel_names = [param_options[lbl] for lbl in sobol_names] or list(PARAM_SPECS.keys())

    @st.cache_data(show_spinner="Running Sobol sampling & analysis...")
    def _cached_sobol(names_tuple, n):
        return global_sobol_analysis(list(names_tuple), n_samples=n)

    sobol_df = _cached_sobol(tuple(sel_names), n_samples)

    fig = go.Figure()
    fig.add_trace(go.Bar(name="S1 (first-order)", x=sobol_df["Parameter"], y=sobol_df["S1"],
                          error_y=dict(type="data", array=sobol_df["S1_conf"])))
    fig.add_trace(go.Bar(name="ST (total-order)", x=sobol_df["Parameter"], y=sobol_df["ST"],
                          error_y=dict(type="data", array=sobol_df["ST_conf"])))
    fig.update_layout(barmode="group", title="Sobol Sensitivity Indices",
                       yaxis_title="Sensitivity Index", xaxis_title="")
    st.plotly_chart(fig, width="stretch")

    st.dataframe(
        sobol_df.style.format({"S1": "{:.3f}", "S1_conf": "{:.3f}",
                                "ST": "{:.3f}", "ST_conf": "{:.3f}"}),
        width="stretch", hide_index=True,
    )

# ---------------------------------------------------------------------------
# Export tab
# ---------------------------------------------------------------------------
with tab_export:
    st.subheader("Download results")

    scenario_df = pd.DataFrame([{**values, "MSP ($/ton)": msp}])
    st.download_button(
        "⬇️ Current scenario (CSV)", scenario_df.to_csv(index=False),
        file_name="odhe_scenario.csv", mime="text/csv",
    )

    breakdown_df = pd.DataFrame(
        {"Category": list(breakdown.keys()), "Annual Cost ($)": list(breakdown.values())}
    )
    st.download_button(
        "⬇️ Cost breakdown (CSV)", breakdown_df.to_csv(index=False),
        file_name="odhe_cost_breakdown.csv", mime="text/csv",
    )

    tdf_export = tornado_analysis(params)
    st.download_button(
        "⬇️ Tornado sensitivity results (CSV)", tdf_export.to_csv(index=False),
        file_name="odhe_tornado_sensitivity.csv", mime="text/csv",
    )

    st.download_button(
        "⬇️ Sobol indices (CSV)", sobol_df.to_csv(index=False),
        file_name="odhe_sobol_indices.csv", mime="text/csv",
    )

st.divider()
st.caption("ODHE Techno-Economic Sensitivity Dashboard · Built with Streamlit, SALib & Plotly")
