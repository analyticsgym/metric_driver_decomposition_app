"""Tests for formula evaluation."""
import pytest
from src.formulas import evaluate_formula


def test_evaluate_formula_basic():
    """Test evaluating a basic formula."""
    values = {"Spend": 50000, "CPA": 50, "AOV": 100}
    result = evaluate_formula(
        "Spend / CPA * AOV",
        values,
        numerators=["Spend", "AOV"],
        denominators=["CPA"],
    )
    expected = 50000 / 50 * 100
    assert result == expected


def test_evaluate_formula_missing_value():
    """Test that missing driver values raise ValueError."""
    values = {"Spend": 50000, "CPA": 50}  # Missing AOV
    with pytest.raises(ValueError, match="Missing driver value"):
        evaluate_formula(
            "Spend / CPA * AOV",
            values,
            numerators=["Spend", "AOV"],
            denominators=["CPA"],
        )


def test_evaluate_formula_division_by_zero():
    """Test that division by zero raises ValueError."""
    values = {"Spend": 50000, "CPA": 0, "AOV": 100}
    with pytest.raises(ValueError, match="[Dd]ivision by zero"):
        evaluate_formula(
            "Spend / CPA * AOV",
            values,
            numerators=["Spend", "AOV"],
            denominators=["CPA"],
        )


def test_evaluate_formula_no_numerators_denominators():
    """Test that omitting numerators/denominators raises ValueError."""
    values = {"Spend": 50000, "CPA": 50, "AOV": 100}
    with pytest.raises(ValueError):
        evaluate_formula("Spend / CPA * AOV", values)


def test_evaluate_formula_with_multiplier():
    """Test formula evaluation with a multiplier."""
    values = {"CTR": 0.02, "CVR": 0.05, "AOV": 100, "CPM": 5}
    result = evaluate_formula(
        "CTR * CVR * AOV / CPM",
        values,
        numerators=["CTR", "CVR", "AOV"],
        denominators=["CPM"],
        multiplier=1000,
    )
    expected = (0.02 * 0.05 * 100 / 5) * 1000
    assert abs(result - expected) < 1e-9
