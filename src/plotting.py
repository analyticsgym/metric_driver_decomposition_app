"""Visualization functions for driver decomposition analysis."""
import matplotlib.pyplot as plt
import pandas as pd
from typing import Dict, List


def create_waterfall_chart(
    drivers_df: pd.DataFrame,
    outcome_info: Dict,
    formula_order: List[str],
    metric_name_clean: str,
):
    """Create a true waterfall chart showing cumulative path from t0 to t1.

    Args:
        drivers_df: DataFrame with driver contributions
        outcome_info: Dict with metric information
        formula_order: List of driver names in the order they appear in the formula
        metric_name_clean: Clean metric name without suffix (e.g., "Sales" instead of "Sales_1")

    Returns:
        matplotlib Figure object
    """
    fig, ax = plt.subplots(figsize=(12, 7))

    # Prepare data for waterfall
    t0_value = outcome_info["time0_value"]
    t1_value = outcome_info["time1_value"]
    total_abs_change = outcome_info["absolute_change"]

    # Reorder drivers_df to match formula order
    drivers_df_ordered = (
        drivers_df.set_index("metric").loc[formula_order].reset_index()
    )

    # Build labels and store PPT contributions
    labels = [f"{metric_name_clean}\n(t0)"]
    colors = ["#4472C4"]  # Blue for starting value
    ppt_contributions = []  # Store PPT contributions for each driver

    # Add each driver in formula order
    for idx, row in drivers_df_ordered.iterrows():
        labels.append(row["metric"])
        contribution = row["absolute_contribution"]
        ppt_contributions.append(row["percentage_points_contribution"])
        # Color based on direction
        if contribution >= 0:
            colors.append("#2ca02c")  # Green for positive
        else:
            colors.append("#d62728")  # Red for negative

    # Add final value
    labels.append(f"{metric_name_clean}\n(t1)")
    colors.append("#4472C4")  # Blue for ending value

    # Build waterfall data: heights and bottoms
    num_items = len(labels)
    x_positions = range(num_items)
    bar_width = 0.6

    heights = []
    bottoms = []
    cumulative = t0_value

    # Starting value
    heights.append(t0_value)
    bottoms.append(0)

    # Driver contributions (deltas) in formula order
    for idx, row in drivers_df_ordered.iterrows():
        contribution = row["absolute_contribution"]
        heights.append(contribution)
        bottoms.append(cumulative)
        cumulative += contribution

    # Ending value - start at zero like t0
    heights.append(t1_value)
    bottoms.append(0)

    # Draw connecting lines between drivers (not to t1 since it starts at zero)
    line_y = t0_value
    num_drivers = len(labels) - 2  # Exclude t0 and t1
    for i in range(num_drivers):
        if i == 0:
            # From start bar to first delta
            ax.plot(
                [i + bar_width, i + 1],
                [line_y, line_y],
                color="gray",
                linewidth=2,
                alpha=0.6,
                zorder=1,
            )
            line_y += heights[i + 1]
        else:
            # Between delta bars
            ax.plot(
                [i, i + 1],
                [line_y, line_y],
                color="gray",
                linewidth=2,
                alpha=0.6,
                zorder=1,
            )
            line_y += heights[i + 1]

    # Draw bars
    bars = ax.bar(
        x_positions,
        heights,
        bottom=bottoms,
        width=bar_width,
        color=colors,
        alpha=0.7,
        edgecolor="black",
        linewidth=1.5,
        zorder=2,
    )

    # Add value labels on bars - check if metric name starts with "Sales" for currency formatting
    is_sales = outcome_info["metric_name"].startswith("Sales")
    for i, (bar, label) in enumerate(zip(bars, labels)):
        bar_height = heights[i]
        bar_bottom = bottoms[i]
        bar_center = bar_bottom + bar_height / 2

        if i == 0:
            # Starting value
            label_text = (
                f"${bar_height:,.0f}" if is_sales else f"{bar_height:.2f}"
            )
            label_color = "white"
        elif i == len(labels) - 1:
            # Ending value
            # Calculate percentage change vs t0
            pct_change_vs_t0 = (
                ((t1_value - t0_value) / t0_value * 100) if t0_value != 0 else 0
            )
            val_str = f"${bar_height:,.0f}" if is_sales else f"{bar_height:.2f}"
            label_text = f"{val_str}\n{pct_change_vs_t0:+.1f}%"
            label_color = "white"
        else:
            # Delta contribution
            contribution = heights[i]
            driver_idx = i - 1  # Index into drivers (0-based, i=1 is first driver)
            ppt_contribution = ppt_contributions[driver_idx]
            val_str = (
                f"${contribution:,.0f}" if is_sales else f"{contribution:.2f}"
            )
            label_text = f"{val_str}\n{ppt_contribution:.1f} ppts"
            label_color = "black"

        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar_center,
            label_text,
            ha="center",
            va="center",
            fontsize=14,
            fontweight="bold",
            color=label_color,
        )

    # Customize chart
    ax.set_xticks(x_positions)
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=14)
    # Remove y axis values, ticks, and label
    ax.set_yticks([])
    ax.set_ylabel("")
    ax.tick_params(axis='y', left=False, right=False, labelleft=False)
    ax.set_title(
        f"Waterfall: {metric_name_clean} Decomposition\n"
        f"t0 → Drivers → t1",
        fontsize=14,
        fontweight="bold",
        pad=20,
    )
    ax.grid(axis="y", alpha=0.3, linestyle="--")

    # Add zero line if needed
    min_y = min(min(bottoms), min([b + h for b, h in zip(bottoms, heights)]))
    if min_y < 0:
        ax.axhline(0, color="black", linewidth=0.8)

    plt.tight_layout()
    return fig

