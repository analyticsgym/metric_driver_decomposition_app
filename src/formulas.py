"""Formula parsing and evaluation functionality."""

import re
from typing import Tuple, Dict, List


def parse_formula(expr: str) -> Tuple[List[str], List[str]]:
    """Convert 'Spend / CPA * AOV' → numerators, denominators, dropping constant numbers.
       Handles parenthetical denominators, e.g. 'CPM / (CTR * CVR * 1000)'.

    Args:
        expr: Formula expression as string (e.g., "Spend / CPA * AOV")

    Returns:
        Tuple of (numerators, denominators) lists, variables only (no constant numbers)
    """
    numerators = []
    denominators = []

    # Helper to parse a "slice" of formula text into variables given an operator context
    def parse_slice(slice_expr: str, destination: List[str]):
        tokens = re.split(r"\s*([*/])\s*", slice_expr)
        current_op = "*"
        for token in tokens:
            if token == "" or token is None:
                continue
            if token == "*":
                current_op = "*"
            elif token == "/":
                current_op = "/"
            else:
                token_stripped = token.strip()
                if not token_stripped:
                    continue
                # check and skip constant numbers
                try:
                    float(token_stripped)
                    continue
                except ValueError:
                    pass
                destination.append(token_stripped)

    # Find any denominator group inside parentheses after a division
    pattern = re.compile(r"/(?:\s*)\(([^)]*)\)")
    match = pattern.search(expr)

    if match:
        # Everything before the '/(' is numerators (can have multiple multipliers)
        numerator_expr = expr[: match.start()]
        denominator_expr = match.group(1)

        # Parse numerators before '/('
        parse_slice(numerator_expr, numerators)
        # Parse each denominator in the parentheses (always denominator)
        denom_tokens = re.split(r"\s*[*]\s*", denominator_expr)
        for tok in denom_tokens:
            stripped = tok.strip()
            if not stripped:
                continue
            # skip number constants
            try:
                float(stripped)
                continue
            except ValueError:
                denominators.append(stripped)
        # Parse the rest of the formula that comes after the closing ')'
        rest_expr = expr[match.end() :]
        if rest_expr.strip():
            # Is it more denominators or numerators?
            # Recurse on the rest, but context: after /( ) it's multiplied
            # For "CPM / (CTR * CVR * 1000) * X" we are multiplying more numerators
            parse_slice(rest_expr, numerators)
        return numerators, denominators
    else:
        # No complex parenthesis denominator, handle simply
        tokens = re.split(r"\s*([*/])\s*", expr)
        current_op = "*"
        for token in tokens:
            if token == "":
                continue
            if token == "*":
                current_op = "*"
            elif token == "/":
                current_op = "/"
            else:
                token_stripped = token.strip()
                if not token_stripped:
                    continue
                try:
                    float(token_stripped)
                    continue
                except ValueError:
                    pass
                if current_op == "*":
                    numerators.append(token_stripped)
                else:
                    denominators.append(token_stripped)
        return numerators, denominators


def get_drivers_in_formula_order(formula: str) -> List[str]:
    """Return drivers in the order they appear in the formula.

    Args:
        formula: Formula expression as string

    Returns:
        List of driver names in order of appearance
    """
    tokens = re.split(r"\s*([*/])\s*", formula)
    drivers_in_order = []

    for token in tokens:
        if token not in ["*", "/"]:
            drivers_in_order.append(token)

    return drivers_in_order


def evaluate_formula(
    formula: str, values: Dict[str, float], formulas_dict: Dict[str, str] = None
) -> float:
    """Compute metric value from formula using provided driver values.

    Args:
        formula: Formula expression as string or metric name
        values: Dictionary of driver values (e.g., {"Spend": 50000, "CPA": 50, "AOV": 100})
        formulas_dict: Optional dict mapping metric names to formulas.
                      If None and formula is a metric name, raises ValueError.

    Returns:
        Computed metric value

    Raises:
        ValueError: If missing driver values or division by zero
    """
    # If formula is a metric name, look it up in formulas_dict
    if formulas_dict and formula in formulas_dict:
        formula_expr = formulas_dict[formula]
    else:
        formula_expr = formula

    numerators, denominators = parse_formula(formula_expr)

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

    return numerator_product / denominator_product
