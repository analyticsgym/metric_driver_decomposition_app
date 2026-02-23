"""Tests for formula evaluation functionality."""
import pytest
from src.formulas import evaluate_formula


def test_evaluate_formula_basic():
    """Test evaluating a basic formula with explicit numerators/denominators."""
    values = {"Spend": 50000, "CPA": 50, "AOV": 100}
    result = evaluate_formula(
        "Sales", values, numerators=["Spend", "AOV"], denominators=["CPA"]
    )
    expected = 50000 * 100 / 50
    assert result == expected


def test_evaluate_formula_multiplier():
    """Test formula with a multiplier constant."""
    values = {"CTR": 0.01, "CVR": 0.05, "AOV": 100, "CPM": 5.0}
    result = evaluate_formula(
        "ROAS",
        values,
        numerators=["CTR", "CVR", "AOV"],
        denominators=["CPM"],
        multiplier=1000.0,
    )
    expected = (0.01 * 0.05 * 100 / 5.0) * 1000.0
    assert abs(result - expected) < 1e-9


def test_evaluate_formula_no_denominators():
    """Test formula with no denominators (pure product)."""
    values = {"Spend": 30000, "ROAS": 2.5}
    result = evaluate_formula(
        "Sales", values, numerators=["Spend", "ROAS"], denominators=[]
    )
    assert result == 75000.0


def test_evaluate_formula_missing_value():
    """Test that missing driver values raise ValueError."""
    values = {"Spend": 50000, "CPA": 50}  # Missing AOV
    with pytest.raises(ValueError, match="Missing driver value"):
        evaluate_formula(
            "Sales", values, numerators=["Spend", "AOV"], denominators=["CPA"]
        )


def test_evaluate_formula_division_by_zero():
    """Test that division by zero raises ValueError."""
    values = {"Spend": 50000, "CPA": 0, "AOV": 100}
    with pytest.raises(ValueError, match="[Dd]ivision by zero"):
        evaluate_formula(
            "Sales", values, numerators=["Spend", "AOV"], denominators=["CPA"]
        )


def test_evaluate_formula_missing_numerators_arg():
    """Test that omitting numerators/denominators raises ValueError."""
    values = {"Spend": 50000, "CPA": 50, "AOV": 100}
    with pytest.raises(ValueError):
        evaluate_formula("Sales", values)
