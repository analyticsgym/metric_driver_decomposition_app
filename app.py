import streamlit as st
import pandas as pd
import yaml
import matplotlib.pyplot as plt
from pathlib import Path

from src.formulas import parse_formula, get_drivers_in_formula_order, evaluate_formula
from src.decomposition import decompose
from src.plotting import create_waterfall_chart
from src.utils import validate_decomposition, format_value
from src.llm_summary import generate_executive_summary

# Load formulas from config
config_path = Path(__file__).parent / "config" / "formulas.yaml"
with open(config_path) as f:
    FORMULAS = yaml.safe_load(f)

# ==========================================================
# STREAMLIT UI
# ==========================================================

st.title("Sub-Metrics Driver Decomposition")

st.write(
    "This tool uses log decomposition to analyze time-window vs. time-window changes in a business outcome metric, based on driver sub-metric contributions."
)

# -----------------------------
# Metric selection
# -----------------------------
# Build pretty formula labels: "Sales = Spend / CPA * AOV" etc.
formula_labels = {}
reverse_formula_labels = {}
for metric_key, formula_str in FORMULAS.items():
    metric_name_clean = metric_key.split("_")[0]
    label = f"{metric_name_clean} = {formula_str}"
    formula_labels[label] = formula_str
    reverse_formula_labels[formula_str] = metric_key

# Show selectbox with cleaned-up formula labels
selected_label = st.selectbox(
    "Select an outcome metric to decompose", list(formula_labels.keys())
)
formula = formula_labels[selected_label]

# Get original metric_name and metric_name_clean from formula string
metric_name = reverse_formula_labels[formula]
metric_name_clean = metric_name.split("_")[0]

numerators, denominators = parse_formula(formula)
drivers = numerators + denominators

st.subheader("Input Values")

# -----------------------------
# Dynamic T0 and T1 UI
# -----------------------------
t0 = {}
t1 = {}

cols = st.columns(2)
# Set up default values for t0 and t1
default_t0 = {"Spend": 50_000, "CPA": 50, "AOV": 100}
default_t1 = {"Spend": 30_000, "CPA": 60, "AOV": 80}

with cols[0]:
    st.markdown("##### Time 0 Values")
    # Input only drivers (not the metric itself)
    for d in drivers:
        init_val = default_t0.get(d, 1)
        t0[d] = st.number_input(
            f"{d} (t0)", min_value=0.0, value=float(init_val), key=f"t0_{d}"
        )

    # Compute and display metric as read-only
    try:
        computed_t0_metric = evaluate_formula(formula, t0)
        t0[metric_name] = computed_t0_metric
        st.markdown(
            f"**{metric_name_clean} (t0) (computed):** {computed_t0_metric:,.2f}"
        )
    except (ValueError, ZeroDivisionError) as e:
        st.error(f"Error computing {metric_name_clean}: {str(e)}")
        t0[metric_name] = default_t0.get(metric_name, 0.0)

with cols[1]:
    st.markdown("##### Time 1 Values")
    # Input only drivers (not the metric itself)
    for d in drivers:
        init_val = default_t1.get(d, 1)
        t1[d] = st.number_input(
            f"{d} (t1)", min_value=0.0, value=float(init_val), key=f"t1_{d}"
        )

    # Compute and display metric as read-only
    try:
        computed_t1_metric = evaluate_formula(formula, t1)
        t1[metric_name] = computed_t1_metric
        st.markdown(
            f"**{metric_name_clean} (t1) (computed):** {computed_t1_metric:,.2f}"
        )
    except (ValueError, ZeroDivisionError) as e:
        st.error(f"Error computing {metric_name_clean}: {str(e)}")
        t1[metric_name] = default_t1.get(metric_name, 0.0)


# -----------------------------
# Run decomposition
# -----------------------------
if st.button("Run Decomposition"):
    drivers_df, outcome_info = decompose(metric_name, t0, t1, FORMULAS)

    # Get drivers in formula order
    formula_order = get_drivers_in_formula_order(formula)

    # Create clean metric name (remove suffix like _1, _2, etc.)
    metric_name_clean = outcome_info["metric_name"].split("_")[0]

    # -----------------------------
    # Output Metric Summary
    # -----------------------------
    st.subheader("Outcome Metric Summary")

    # Calculate percentage change
    pct_change = (
        (outcome_info["time1_value"] - outcome_info["time0_value"])
        / outcome_info["time0_value"]
        * 100
        if outcome_info["time0_value"] != 0
        else 0
    )

    # Determine if metric is sales for formatting
    is_sales = outcome_info["metric_name"].startswith("Sales")

    # Format output metric table
    output_df = pd.DataFrame()
    output_df["Metric"] = [metric_name_clean]
    output_df["t0 Value"] = [format_value(outcome_info["time0_value"], is_sales)]
    output_df["t1 Value"] = [format_value(outcome_info["time1_value"], is_sales)]
    output_df["Percent Change"] = [f"{pct_change:.2f}%"]
    output_df["Absolute Change"] = [
        format_value(outcome_info["absolute_change"], is_sales)
    ]

    st.dataframe(
        output_df,
        use_container_width=True,
        hide_index=True,
    )

    # -----------------------------
    # Driver Contributions
    # -----------------------------
    st.subheader("Driver Contributions")

    # Format display columns - check if metric name starts with "Sales" for currency formatting
    is_sales = outcome_info["metric_name"].startswith("Sales")
    display_df = pd.DataFrame()
    display_df["Driver"] = drivers_df["metric"]
    display_df["t0 Value"] = drivers_df["time0_value"].apply(
        lambda x: format_value(x, is_sales)
    )
    display_df["t1 Value"] = drivers_df["time1_value"].apply(
        lambda x: format_value(x, is_sales)
    )
    display_df["Percent Change"] = drivers_df["pct_change"].apply(
        lambda x: f"{x*100:.2f}%"
    )
    display_df["Abs Contribution"] = drivers_df["absolute_contribution"].apply(
        lambda x: format_value(x, is_sales)
    )
    display_df["Percentage Points Contribution"] = drivers_df[
        "percentage_points_contribution"
    ].apply(lambda x: f"{x:.2f} ppts")

    # Calculate totals for Abs Contribution and PPT Contribution
    total_abs_contribution = drivers_df["absolute_contribution"].sum()
    total_ppt_contribution = drivers_df["percentage_points_contribution"].sum()

    # Add Total row
    total_row = pd.DataFrame(
        {
            "Driver": ["Total"],
            "t0 Value": [""],
            "t1 Value": [""],
            "Percent Change": [""],
            "Abs Contribution": [format_value(total_abs_contribution, is_sales)],
            "Percentage Points Contribution": [f"{total_ppt_contribution:.2f} ppts"],
        }
    )

    # Concatenate display_df with total row
    display_df_with_total = pd.concat([display_df, total_row], ignore_index=True)

    st.dataframe(
        display_df_with_total,
        use_container_width=True,
        hide_index=True,
    )

    # -----------------------------
    # True Waterfall Chart
    # -----------------------------
    st.subheader("Waterfall Chart: Contribution Share by Sub-Metric")
    waterfall_fig = create_waterfall_chart(
        drivers_df, outcome_info, formula_order, metric_name_clean
    )
    st.pyplot(waterfall_fig)
    plt.close(waterfall_fig)

    # -----------------------------
    # Executive Summary Generation
    # -----------------------------
    st.subheader("LLM-Generated Executive Summary")

    # add bullet signaling the LLM summary is experimental and use with caution
    st.markdown(
        """
    <div style="background-color: #f0f0f0; padding: 10px; border-radius: 5px;">
    <p><strong>Note:</strong> The LLM-generated executive summary is experimental and should be used with caution.</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    with st.spinner("Generating executive summary..."):
        try:
            summary = generate_executive_summary(
                metric_name=metric_name,
                formula=formula,
                outcome_df=output_df,
                drivers_df=drivers_df,
                numerators=numerators,
                denominators=denominators,
            )
            st.markdown(summary)
        except ValueError as e:
            st.warning(f"⚠️ Could not generate executive summary: {str(e)}")
        except Exception as e:
            st.error(f"❌ Error generating executive summary: {str(e)}")

    # -----------------------------
    # Validation Check
    # -----------------------------
    is_valid, error_msg = validate_decomposition(drivers_df, outcome_info)

    if not is_valid:
        st.error(f"❌ **Validation Failed:** {error_msg} Please check your inputs.")
        st.stop()  # Stop execution if validation fails

# Footer
st.markdown("---")
st.caption("Built with Streamlit · Multiplicative log-share decomposition")
