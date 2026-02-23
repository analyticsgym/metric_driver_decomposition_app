"""Tests for log decomposition functionality."""
import pytest
import pandas as pd
from src.decomposition import decompose, multiplicative_contribution


NUMERATORS = ["Spend", "AOV"]
DENOMINATORS = ["CPA"]

T0 = {"Sales": 100000, "Spend": 50000, "CPA": 50, "AOV": 100}
T1 = {"Sales": 40000, "Spend": 30000, "CPA": 60, "AOV": 80}


def test_decompose_basic():
    """Test basic decomposition returns expected columns and drivers."""
    drivers_df, outcome_info = decompose(
        "Sales", T0, T1, numerators=NUMERATORS, denominators=DENOMINATORS
    )

    assert "metric" in drivers_df.columns
    assert "absolute_contribution" in drivers_df.columns
    assert "percentage_points_contribution" in drivers_df.columns

    assert len(drivers_df) == 3  # Spend, CPA, AOV
    assert set(drivers_df["metric"]) == {"Spend", "CPA", "AOV"}

    assert outcome_info["metric_name"] == "Sales"
    assert outcome_info["time0_value"] == 100000
    assert outcome_info["time1_value"] == 40000


def test_decompose_contributions_sum():
    """Test that driver contributions sum to total metric change."""
    drivers_df, outcome_info = decompose(
        "Sales", T0, T1, numerators=NUMERATORS, denominators=DENOMINATORS
    )

    sum_abs = drivers_df["absolute_contribution"].sum()
    assert abs(sum_abs - outcome_info["absolute_change"]) < 0.01

    sum_ppt = drivers_df["percentage_points_contribution"].sum()
    assert abs(sum_ppt - outcome_info["percentage_points_change"]) < 0.01


def test_multiplicative_contribution_direct():
    """Test multiplicative_contribution directly."""
    drivers_df, outcome_info = multiplicative_contribution(
        "Sales", T0, T1, NUMERATORS, DENOMINATORS
    )

    assert isinstance(drivers_df, pd.DataFrame)
    assert len(drivers_df) == 3
    assert "absolute_contribution" in drivers_df.columns
    assert outcome_info["metric_name"] == "Sales"


def test_decompose_direction_labels():
    """Test that direction labels are set correctly."""
    drivers_df, _ = decompose(
        "Sales", T0, T1, numerators=NUMERATORS, denominators=DENOMINATORS
    )
    assert set(drivers_df["direction_label"]).issubset({"positive", "negative"})


def test_decompose_zero_driver_t0_raises():
    """Test that a zero t0 driver value raises a clear error."""
    t0_bad = {"Sales": 100000, "Spend": 0, "CPA": 50, "AOV": 100}
    with pytest.raises(ValueError, match="zero"):
        decompose("Sales", t0_bad, T1, numerators=NUMERATORS, denominators=DENOMINATORS)


def test_decompose_no_change():
    """Test that identical t0 and t1 raises a clear error (total_log == 0)."""
    with pytest.raises(ValueError, match="no change"):
        decompose("Sales", T0, T0, numerators=NUMERATORS, denominators=DENOMINATORS)
