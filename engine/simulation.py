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
