"""Utility functions for validation and formatting."""
from typing import Dict, Tuple


def validate_inputs(
    t0: Dict[str, float], t1: Dict[str, float], drivers: list
) -> None:
    """Validate that t0 and t1 contain all required driver values.
    
    Args:
        t0: Dictionary of values at time 0
        t1: Dictionary of values at time 1
        drivers: List of driver names required
    
    Raises:
        ValueError: If any driver is missing from t0 or t1
    """
    missing_t0 = set(drivers) - set(t0.keys())
    missing_t1 = set(drivers) - set(t1.keys())
    
    if missing_t0:
        raise ValueError(f"Missing drivers in t0: {missing_t0}")
    if missing_t1:
        raise ValueError(f"Missing drivers in t1: {missing_t1}")


def format_value(value: float, is_sales: bool = False) -> str:
    """Format a numeric value for display.
    
    Args:
        value: Numeric value to format
        is_sales: If True, format as currency ($X,XXX.XX), else as float (X.XX)
    
    Returns:
        Formatted string
    """
    if is_sales:
        return f"${value:,.2f}"
    else:
        return f"{value:.2f}"


def validate_decomposition(
    drivers_df, outcome_info, rounding_tolerance: float = None
) -> Tuple[bool, str]:
    """Validate that driver contributions sum to metric change.
    
    Args:
        drivers_df: DataFrame with driver contributions
        outcome_info: Dict with metric change information
        rounding_tolerance: Optional tolerance for comparison. 
                          If None, auto-calculates based on change magnitude.
    
    Returns:
        Tuple of (is_valid: bool, error_message: str)
    """
    if rounding_tolerance is None:
        rounding_tolerance = max(abs(outcome_info["absolute_change"]) * 0.001, 0.01)

    # Check if sum of contributions matches total change
    abs_diff = abs(
        outcome_info["sum_absolute_contributions"] - outcome_info["absolute_change"]
    )
    abs_check_passed = abs_diff < rounding_tolerance

    ppt_diff = abs(
        outcome_info["sum_ppt_contributions"]
        - outcome_info["percentage_points_change"]
    )
    ppt_check_passed = ppt_diff < 0.01

    if not (abs_check_passed and ppt_check_passed):
        error_msg = (
            f"Sum of driver contributions does not match "
            f"total change in {outcome_info['metric_name']}. "
            f"Absolute difference: ${abs_diff:.2f}, "
            f"PPT difference: {ppt_diff:.2f} ppts."
        )
        return False, error_msg

    return True, ""

