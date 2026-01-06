def calculate_cld(ideal: float, actual: float) -> float:
    loss = ideal - actual
    return round(loss if loss > 0 else 0, 2)


def calculate_ccr(expected_total: float, actual_total: float) -> float:
    if expected_total == 0:
        return 1.0
    return round(actual_total / expected_total, 4)


def calculate_discipline_score(ccr: float, cld_ratio: float) -> float:
    penalty = 40 * (1 - ccr) + 60 * cld_ratio
    score = 100 - penalty
    return round(min(100, max(0, score)), 2)
