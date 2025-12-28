def calculate_cld(ideal: float, actual: float) -> float:
    loss = ideal - actual
    return round(loss if loss > 0 else 0, 2)


