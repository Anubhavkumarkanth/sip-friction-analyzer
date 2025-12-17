from typing import List, Dict
import random


class SIPSimulator:

    def __init__(
        self,
        monthly_amount: float,
        annual_return: float,
        years: int
    ):
        self.initial_monthly_amount = monthly_amount
        self.monthly_return = annual_return / 12
        self.total_months = years * 12

    # ----------------------------------
    # Ideal disciplined investing
    # ----------------------------------
    def calculate_ideal(self):
        value = 0
        monthly_amount = self.initial_monthly_amount
        history = []

        for month in range(1, self.total_months + 1):
            value = (value + monthly_amount) * (1 + self.monthly_return)
            if month % 12 == 0:
                history.append({"year": month // 12, "ideal_value": round(value, 2)})

        return round(value, 2), history

    # ----------------------------------
    # Behavioral investing
    # ----------------------------------
