"""Log decomposition mathematics for multiplicative driver attribution."""
import pandas as pd
import numpy as np
from typing import Tuple, Dict
from src.formulas import parse_formula


def multiplicative_contribution(
    metric_name: str,
    t0: Dict[str, float],
    t1: Dict[str, float],
    numerators: list,
    denominators: list,
) -> Tuple[pd.DataFrame, Dict]:
    """Decompose metric change into driver contributions.

    Args:
        metric_name: Name of the metric being decomposed
        t0: Dictionary of values at time 0 (including metric and all drivers)
        t1: Dictionary of values at time 1 (including metric and all drivers)
        numerators: List of numerator driver names
        denominators: List of denominator driver names

    Returns:
        Tuple of:
        - drivers_df: DataFrame with only driver rows (inputs)
        - outcome_info: Dict with metric change information for reconciliation
    """
    drivers = numerators + denominators

    # growth factors
    g = {d: t1[d] / t0[d] for d in drivers}

    pct_change = {d: (t1[d] - t0[d]) / t0[d] for d in drivers}

    df = pd.DataFrame(
        {
            "driver": drivers,
            "time0_value": [t0[d] for d in drivers],
            "time1_value": [t1[d] for d in drivers],
            "growth_factor": [g[d] for d in drivers],
            "pct_change": [pct_change[d] for d in drivers],
        }
    )

    # +log for numerator, –log for denominator
    df["log_driver"] = df.apply(
        lambda r: (
            np.log(r["growth_factor"])
            if r["driver"] in numerators
            else -np.log(r["growth_factor"])
        ),
        axis=1,
    )

    # normalize log shares
    total_log = df["log_driver"].sum()
    df["log_share"] = df["log_driver"] / total_log

    # final metric changes
    metric_f = t1[metric_name] / t0[metric_name]
    metric_pct_change = (metric_f - 1) * 100
    metric_abs_change = t1[metric_name] - t0[metric_name]

    df["percentage_points_contribution"] = df["log_share"] * metric_pct_change
    df["absolute_contribution"] = df["log_share"] * metric_abs_change

    # add column for direction label
    df["direction_label"] = np.where(
        df["absolute_contribution"] >= 0, "positive", "negative"
    )

    # rename driver column to metric name for display
    df = df.rename(columns={"driver": "metric"})

    # Prepare outcome info for reconciliation
    outcome_info = {
        "metric_name": metric_name,
        "time0_value": t0[metric_name],
        "time1_value": t1[metric_name],
        "absolute_change": metric_abs_change,
        "percentage_points_change": metric_pct_change,
        "sum_absolute_contributions": df["absolute_contribution"].sum(),
        "sum_ppt_contributions": df["percentage_points_contribution"].sum(),
    }

    return df, outcome_info


def log_decompose(
    formula_str: str, t0: Dict[str, float], t1: Dict[str, float]
) -> Tuple[pd.DataFrame, Dict]:
    """Decompose a metric using log decomposition.
    
    Args:
        formula_str: Formula expression as string (e.g., "Spend / CPA * AOV")
        t0: Dictionary of values at time 0
        t1: Dictionary of values at time 1
    
    Returns:
        Tuple of (drivers_df, outcome_info)
    """
    numerators, denominators = parse_formula(formula_str)
    
    # Extract metric name from t0/t1 (it should be a key that's not a driver)
    drivers = numerators + denominators
    metric_candidates = set(t0.keys()) - set(drivers)
    if len(metric_candidates) != 1:
        raise ValueError(
            f"Could not uniquely identify metric. "
            f"Found {metric_candidates} in t0/t1 that are not drivers."
        )
    metric_name = metric_candidates.pop()
    
    return multiplicative_contribution(metric_name, t0, t1, numerators, denominators)


def decompose(
    metric_name: str,
    t0: Dict[str, float],
    t1: Dict[str, float],
    formulas_dict: Dict[str, str],
) -> Tuple[pd.DataFrame, Dict]:
    """Decompose a metric by name using formulas dictionary.
    
    Args:
        metric_name: Name of the metric to decompose
        t0: Dictionary of values at time 0
        t1: Dictionary of values at time 1
        formulas_dict: Dictionary mapping metric names to formulas
    
    Returns:
        Tuple of (drivers_df, outcome_info)
    """
    if metric_name not in formulas_dict:
        raise ValueError(f"Metric '{metric_name}' not found in formulas dictionary")
    
    formula = formulas_dict[metric_name]
    numerators, denominators = parse_formula(formula)
    return multiplicative_contribution(metric_name, t0, t1, numerators, denominators)

