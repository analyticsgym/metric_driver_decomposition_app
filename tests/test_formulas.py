"""Tests for formula parsing and evaluation."""
import pytest
from src.formulas import parse_formula, get_drivers_in_formula_order, evaluate_formula


def test_parse_formula_basic():
    """Test parsing a basic formula."""
    numerators, denominators = parse_formula("Spend / CPA * AOV")
    assert set(numerators) == {"Spend", "AOV"}
    assert denominators == ["CPA"]


def test_parse_formula_multiple_divisions():
    """Test parsing formula with multiple divisions."""
    numerators, denominators = parse_formula("AOV / CPA")
    assert numerators == ["AOV"]
    assert denominators == ["CPA"]


def test_parse_formula_complex():
    """Test parsing a complex formula."""
    numerators, denominators = parse_formula("A * B / C * D")
    assert set(numerators) == {"A", "B", "D"}
    assert denominators == ["C"]


def test_get_drivers_in_formula_order():
    """Test getting drivers in formula order."""
    order = get_drivers_in_formula_order("Spend / CPA * AOV")
    assert order == ["Spend", "CPA", "AOV"]


def test_evaluate_formula_basic():
    """Test evaluating a basic formula."""
    values = {"Spend": 50000, "CPA": 50, "AOV": 100}
    result = evaluate_formula("Spend / CPA * AOV", values)
    expected = 50000 / 50 * 100
    assert result == expected


def test_evaluate_formula_missing_value():
    """Test that missing driver values raise ValueError."""
    values = {"Spend": 50000, "CPA": 50}  # Missing AOV
    with pytest.raises(ValueError, match="Missing driver value"):
        evaluate_formula("Spend / CPA * AOV", values)


def test_evaluate_formula_division_by_zero():
    """Test that division by zero raises ValueError."""
    values = {"Spend": 50000, "CPA": 0, "AOV": 100}
    with pytest.raises(ValueError, match="Division by zero"):
        evaluate_formula("Spend / CPA * AOV", values)

