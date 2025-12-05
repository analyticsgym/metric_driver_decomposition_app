"""Formula evaluation functionality."""

from typing import Dict, List


def evaluate_formula(
    formula: str,
    values: Dict[str, float],
    numerators: List[str] = None,
    denominators: List[str] = None,
    multiplier: float = 1.0,
) -> float:
    """Compute metric value from formula using provided driver values.

    Args:
        formula: Formula expression as string or metric name (unused in calculation now, kept for interface)
        values: Dictionary of driver values (e.g., {"Spend": 50000, "CPA": 50, "AOV": 100})
        numerators: List of numerator variables.
        denominators: List of denominator variables.
        multiplier: Optional constant multiplier for the formula (default 1.0).

    Returns:
        Computed metric value

    Raises:
        ValueError: If numerators or denominators are not provided, or if a driver value is missing.
    """
    if numerators is None or denominators is None:
        raise ValueError("numerators and denominators must be explicitly provided.")

    # Compute numerator product
    numerator_product = 1.0
    for num in numerators:
        if num in values:
            numerator_product *= values[num]
        else:
            raise ValueError(f"Missing driver value: {num}")

    # Compute denominator product
    denominator_product = 1.0
    for den in denominators:
        if den in values:
            denominator_product *= values[den]
        else:
            raise ValueError(f"Missing driver value: {den}")

    # Avoid division by zero
    if denominator_product == 0:
        raise ValueError("Division by zero: denominator product is zero")

    return (numerator_product / denominator_product) * multiplier
