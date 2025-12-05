import streamlit as st
import pandas as pd
import yaml
import matplotlib.pyplot as plt
from pathlib import Path

from src.formulas import evaluate_formula
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
# Build pretty formula labels from the list of objects
formula_map = {}
for f_obj in FORMULAS:
    label = f_obj["formula_drop_down"]
    formula_map[label] = f_obj

# Callback to clear results when formula changes
def reset_results():
    st.session_state.decomposition_results = None
    st.session_state.llm_summary = None
    st.session_state.llm_summary_error = None

# Show selectbox with cleaned-up formula labels
selected_label = st.selectbox(
    "Select an outcome metric to decompose",
    list(formula_map.keys()),
    on_change=reset_results,
)
selected_obj = formula_map[selected_label]

metric_name = selected_obj["output_metric"]
metric_name_clean = metric_name  # In new config this is already clean e.g. "Sales"


numerators = selected_obj.get("numerators", [])
denominators = selected_obj.get("denominators", [])
multiplier = selected_obj.get("multiplier", 1.0)
drivers = numerators + denominators

# We keep a string representation for display/logic that might need it
# formatting like "Sales = ..." -> strip "Sales = " if needed or just use label
# But evaluate_formula now accepts explicit lists, so the string is less critical for calculation
# define a formula string for display or legacy usage (RHS of equation)
if " = " in selected_obj["formula_drop_down"]:
    formula_str = selected_obj["formula_drop_down"].split(" = ", 1)[1]
else:
    formula_str = selected_obj["formula_drop_down"] # fallback

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
        # Use custom label if available
        label = selected_obj.get("driver_labels", {}).get(d, f"{d} (t0)")
        if not label.endswith("(t0)"):
            label = f"{label} (t0)"
            
        # Set format based on driver name
        fmt = "%.4f" if d in ["CTR", "CVR"] else "%.2f"
            
        t0[d] = st.number_input(
            label, min_value=0.0, value=float(init_val), key=f"t0_{d}", format=fmt
        )

    # Compute and display metric as read-only
    try:
        computed_t0_metric = evaluate_formula(
            metric_name, t0, numerators=numerators, denominators=denominators, multiplier=multiplier
        )
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
        # Use custom label if available
        label = selected_obj.get("driver_labels", {}).get(d, f"{d} (t1)")
        if not label.endswith("(t1)"):
            label = f"{label} (t1)"

        # Set format based on driver name
        fmt = "%.4f" if d in ["CTR", "CVR"] else "%.2f"

        t1[d] = st.number_input(
            label, min_value=0.0, value=float(init_val), key=f"t1_{d}", format=fmt
        )

    # Compute and display metric as read-only
    try:
        computed_t1_metric = evaluate_formula(
            metric_name, t1, numerators=numerators, denominators=denominators, multiplier=multiplier
        )
        t1[metric_name] = computed_t1_metric
        st.markdown(
            f"**{metric_name_clean} (t1) (computed):** {computed_t1_metric:,.2f}"
        )
    except (ValueError, ZeroDivisionError) as e:
        st.error(f"Error computing {metric_name_clean}: {str(e)}")
        t1[metric_name] = default_t1.get(metric_name, 0.0)


# -----------------------------
# Initialize session state
# -----------------------------
if "decomposition_results" not in st.session_state:
    st.session_state.decomposition_results = None
if "llm_summary" not in st.session_state:
    st.session_state.llm_summary = None
    st.session_state.llm_summary_error = None

# -----------------------------
# Run decomposition
# -----------------------------
if st.button("Run Decomposition"):
    drivers_df, outcome_info = decompose(
        metric_name, t0, t1, numerators=numerators, denominators=denominators
    )

    # Get drivers in formula order
    # Use the explicit order from config
    formula_order = selected_obj.get("driver_order", drivers)

    # Create clean metric name (remove suffix like _1, _2, etc.)
    metric_name_clean = outcome_info["metric_name"].split("_")[0]

    # Calculate percentage change
    pct_change = (
        (outcome_info["time1_value"] - outcome_info["time0_value"])
        / outcome_info["time0_value"]
        * 100
        if outcome_info["time0_value"] != 0
        else 0
    )

    # Determine if metric is sales or CPA for formatting
    is_currency_metric = outcome_info["metric_name"].startswith("Sales") or outcome_info["metric_name"].startswith("CPA")

    # Format output metric table
    output_df = pd.DataFrame()
    output_df["Metric"] = [metric_name_clean]
    output_df["t0 Value"] = [format_value(outcome_info["time0_value"], is_currency_metric)]
    output_df["t1 Value"] = [format_value(outcome_info["time1_value"], is_currency_metric)]
    output_df["Percent Change"] = [f"{pct_change:.2f}%"]
    output_df["Absolute Change"] = [
        format_value(outcome_info["absolute_change"], is_currency_metric)
    ]

    # Format display columns for driver contributions
    display_df = pd.DataFrame()
    display_df["Driver"] = drivers_df["metric"]
    display_df["t0 Value"] = drivers_df["time0_value"].apply(
        lambda x: format_value(x, is_currency_metric)
    )
    display_df["t1 Value"] = drivers_df["time1_value"].apply(
        lambda x: format_value(x, is_currency_metric)
    )
    display_df["Percent Change"] = drivers_df["pct_change"].apply(
        lambda x: f"{x*100:.2f}%"
    )
    display_df["Abs Contribution"] = drivers_df["absolute_contribution"].apply(
        lambda x: format_value(x, is_currency_metric)
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
            "Abs Contribution": [format_value(total_abs_contribution, is_currency_metric)],
            "Percentage Points Contribution": [f"{total_ppt_contribution:.2f} ppts"],
        }
    )

    # Concatenate display_df with total row
    display_df_with_total = pd.concat([display_df, total_row], ignore_index=True)

    # Store all results in session state
    # Note: matplotlib figures can't be pickled, so we recreate them when needed
    st.session_state.decomposition_results = {
        "drivers_df": drivers_df,
        "outcome_info": outcome_info,
        "output_df": output_df,
        "display_df_with_total": display_df_with_total,
        "formula_order": formula_order,
        "metric_name_clean": metric_name_clean,
        "metric_name": metric_name,
        "formula": formula_str,
        "numerators": numerators,
        "denominators": denominators,
    }

    # Clear LLM summary when new decomposition is run
    st.session_state.llm_summary = None
    st.session_state.llm_summary_error = None

    # -----------------------------
    # Validation Check
    # -----------------------------
    is_valid, error_msg = validate_decomposition(drivers_df, outcome_info)

    if not is_valid:
        st.error(f"❌ **Validation Failed:** {error_msg} Please check your inputs.")
        st.session_state.decomposition_results = None
        st.stop()  # Stop execution if validation fails

# -----------------------------
# Display decomposition results (persisted)
# -----------------------------
if st.session_state.decomposition_results is not None:
    results = st.session_state.decomposition_results
    # -----------------------------
    # Output Metric Summary
    # -----------------------------
    st.subheader("Outcome Metric Summary")
    st.dataframe(
        results["output_df"],
        use_container_width=True,
        hide_index=True,
    )

    # -----------------------------
    # Driver Contributions
    # -----------------------------
    st.subheader("Driver Contributions")
    st.dataframe(
        results["display_df_with_total"],
        use_container_width=True,
        hide_index=True,
    )

    # -----------------------------
    # True Waterfall Chart
    # -----------------------------
    st.subheader("Waterfall Chart: Contribution Share by Sub-Metric")
    # Recreate the waterfall chart (matplotlib figures can't be pickled in session_state)
    waterfall_fig = create_waterfall_chart(
        results["drivers_df"],
        results["outcome_info"],
        results["formula_order"],
        results["metric_name_clean"],
        selected_obj.get("higher_is_better", True),
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

    generate_button = st.button("Generate Executive Summary")
    if generate_button:
        with st.spinner("Generating executive summary..."):
            try:
                summary = generate_executive_summary(
                    metric_name=results["metric_name"],
                    formula=results["formula"],
                    outcome_df=results["output_df"],
                    drivers_df=results["drivers_df"],
                    numerators=results["numerators"],
                    denominators=results["denominators"],
                )
                st.session_state.llm_summary = summary
                st.session_state.llm_summary_error = None
            except ValueError as e:
                st.session_state.llm_summary = None
                st.session_state.llm_summary_error = (
                    f"⚠️ Could not generate executive summary: {str(e)}"
                )
            except Exception as e:
                st.session_state.llm_summary = None
                st.session_state.llm_summary_error = (
                    f"❌ Error generating executive summary: {str(e)}"
                )

    # Display the summary or error from the session state if present
    if st.session_state.llm_summary is not None:
        st.code(st.session_state.llm_summary, language="markdown")
    elif st.session_state.llm_summary_error is not None:
        if st.session_state.llm_summary_error.startswith("⚠️"):
            st.warning(st.session_state.llm_summary_error)
        else:
            st.error(st.session_state.llm_summary_error)

# Footer
st.markdown("---")
st.caption(
    "Built with Streamlit · Log Decomposition for Sub-Metric Contribution Analysis"
)
