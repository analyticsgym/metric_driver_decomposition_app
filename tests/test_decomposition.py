"""Tests for log decomposition functionality."""
import pytest
import pandas as pd
from src.decomposition import decompose, multiplicative_contribution


def test_decompose_basic():
    """Test basic decomposition."""
    formulas = {"Sales": "Spend / CPA * AOV"}
    t0 = {"Sales": 100000, "Spend": 50000, "CPA": 50, "AOV": 100}
    t1 = {"Sales": 40000, "Spend": 30000, "CPA": 60, "AOV": 80}

    drivers_df, outcome_info = decompose("Sales", t0, t1, formulas)

    # Check that drivers_df has the right columns
    assert "metric" in drivers_df.columns
    assert "absolute_contribution" in drivers_df.columns
    assert "percentage_points_contribution" in drivers_df.columns

    # Check that all drivers are present
    assert len(drivers_df) == 3  # Spend, CPA, AOV
    assert set(drivers_df["metric"]) == {"Spend", "CPA", "AOV"}

    # Check outcome info structure
    assert outcome_info["metric_name"] == "Sales"
    assert outcome_info["time0_value"] == 100000
    assert outcome_info["time1_value"] == 40000


def test_decompose_contributions_sum():
    """Test that driver contributions sum to total change."""
    formulas = {"Sales": "Spend / CPA * AOV"}
    t0 = {"Sales": 100000, "Spend": 50000, "CPA": 50, "AOV": 100}
    t1 = {"Sales": 40000, "Spend": 30000, "CPA": 60, "AOV": 80}

    drivers_df, outcome_info = decompose("Sales", t0, t1, formulas)

    # Sum of absolute contributions should equal absolute change (within rounding)
    sum_abs = drivers_df["absolute_contribution"].sum()
    abs_change = outcome_info["absolute_change"]
    assert abs(sum_abs - abs_change) < 0.01

    # Sum of PPT contributions should equal PPT change (within rounding)
    sum_ppt = drivers_df["percentage_points_contribution"].sum()
    ppt_change = outcome_info["percentage_points_change"]
    assert abs(sum_ppt - ppt_change) < 0.01


def test_multiplicative_contribution_direct():
    """Test multiplicative_contribution directly."""
    t0 = {"Sales": 100000, "Spend": 50000, "CPA": 50, "AOV": 100}
    t1 = {"Sales": 40000, "Spend": 30000, "CPA": 60, "AOV": 80}

    numerators = ["Spend", "AOV"]
    denominators = ["CPA"]

    drivers_df, outcome_info = multiplicative_contribution(
        "Sales", t0, t1, numerators, denominators
    )

    assert isinstance(drivers_df, pd.DataFrame)
    assert len(drivers_df) == 3
    assert "absolute_contribution" in drivers_df.columns
    assert outcome_info["metric_name"] == "Sales"

