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
    def calculate_actual(self, events: List[Dict]):

        value = 0
        monthly_amount = self.initial_monthly_amount

        total_expected = 0
        total_actual = 0

        event_map = {}
        pause_ranges = []
        step_up_rate = 0

        for event in events:
            event_type = event.get("type")

            if event_type == "PAUSE_RANGE":
                pause_ranges.append(
                    (event.get("start_month"), event.get("end_month"))
                )

            elif event_type == "STEP_UP":
                step_up_rate = event.get("yearly_growth", 0)

            else:
                month = event.get("month")
                if month:
                    if month not in event_map:
                        event_map[month] = []
                    event_map[month].append(event)

        history = []

        for month in range(1, self.total_months + 1):

            contribution = monthly_amount
            total_expected += monthly_amount

            for start, end in pause_ranges:
                if start and end and start <= month <= end:
                    contribution = 0

            if month in event_map:
                for event in event_map[month]:

                    if event["type"] == "SKIP":
                        contribution = 0

                    elif event["type"] == "REDUCE":
                        contribution = monthly_amount * event.get("factor", 1)

                    elif event["type"] == "INCREASE":
                        monthly_amount *= event.get("factor", 1)
                        contribution = monthly_amount

            total_actual += contribution

            if step_up_rate and month % 12 == 0:
                monthly_amount *= (1 + step_up_rate)

            value = (value + contribution) * (1 + self.monthly_return)
            
            if month % 12 == 0:
                history.append({"year": month // 12, "actual_value": round(value, 2)})

        return (
            round(value, 2),
            round(total_expected, 2),
            round(total_actual, 2),
            history
        )

    # ----------------------------------
    # Monte Carlo Simulation (Clean Version)
    # ----------------------------------
    def monte_carlo(
        self,
        events: List[Dict],
        simulations: int = 1000,
        volatility: float = 0.15
    ):

        results = []

        for _ in range(simulations):

            value = 0
            monthly_amount = self.initial_monthly_amount

            monthly_mean = self.monthly_return
            monthly_vol = volatility / 12

            event_map = {}
            pause_ranges = []
            step_up_rate = 0

            for event in events:
                event_type = event.get("type")

                if event_type == "PAUSE_RANGE":
                    pause_ranges.append(
                        (event.get("start_month"), event.get("end_month"))
                    )

                elif event_type == "STEP_UP":
                    step_up_rate = event.get("yearly_growth", 0)

                else:
                    month = event.get("month")
                    if month:
                        if month not in event_map:
                            event_map[month] = []
                        event_map[month].append(event)

            for month in range(1, self.total_months + 1):

                contribution = monthly_amount

                for start, end in pause_ranges:
                    if start and end and start <= month <= end:
                        contribution = 0

                if month in event_map:
                    for event in event_map[month]:

                        if event["type"] == "SKIP":
                            contribution = 0

                        elif event["type"] == "REDUCE":
                            contribution = monthly_amount * event.get("factor", 1)

                        elif event["type"] == "INCREASE":
                            monthly_amount *= event.get("factor", 1)
                            contribution = monthly_amount

                random_return = random.gauss(monthly_mean, monthly_vol)

                value = (value + contribution) * (1 + random_return)

                if step_up_rate and month % 12 == 0:
                    monthly_amount *= (1 + step_up_rate)

            results.append(value)

        results.sort()

        def percentile(p):
            index = int(p * len(results))
            return round(results[index], 2)

        min_val = min(results)
        max_val = max(results)

        return {
            "mean": round(sum(results) / len(results), 2),
            "p10": percentile(0.10),
            "p50": percentile(0.50),
            "p90": percentile(0.90),
            "best_case": round(max_val, 2),
            "worst_case": round(min_val, 2)
        }