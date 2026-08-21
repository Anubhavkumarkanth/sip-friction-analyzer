"""Financial friction metric calculations.

Calculates key indicators of investor behavioral leakage:
- CLD: Compounding Loss Due to Friction
- CCR: Contribution Compliance Rate
- Discipline Score: 0-100 composite index penalizing skips and lost compounding
"""


def calculate_cld(ideal: float, actual: float) -> float:
    """Calculates compounding loss due to friction events in portfolio growth."""
    loss = ideal - actual
    return round(max(0.0, float(loss)), 2)


def calculate_ccr(expected_total: float, actual_total: float) -> float:
    """Calculates the Contribution Compliance Rate (CCR).

    CCR = actual_total_contributions / expected_total_contributions
    """
    if expected_total <= 0:
        return 1.0
    ratio = float(actual_total) / float(expected_total)
    return round(min(1.0, max(0.0, ratio)), 4)


def calculate_discipline_score(ccr: float, cld_ratio: float) -> float:
    """Calculates a normalized 0-100 score representing financial discipline.

    Penalty incorporates both contribution deficiency (40% weight) and
    lost opportunity cost from lost compounding (60% weight).
    """
    bounded_ccr = min(1.0, max(0.0, float(ccr)))
    bounded_cld_ratio = min(1.0, max(0.0, float(cld_ratio)))

    penalty = (40.0 * (1.0 - bounded_ccr)) + (60.0 * bounded_cld_ratio)
    score = 100.0 - penalty
    return round(min(100.0, max(0.0, score)), 2)
