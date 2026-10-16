from typing import List, Dict, Optional, Tuple, Any
import math
import random


def _required_factor(event: Dict[str, Any]) -> float:
    """The multiplier on a REDUCE or INCREASE event.

    Missing is an error. Falling back to 1.0 would quietly turn the event into a
    no-op, and the dict an API request produces holds an explicit None rather
    than omitting the key, so a plain .get("factor", 1.0) does not even do that.
    """
    factor = event.get("factor")
    if factor is None:
        raise ValueError(f"{event.get('type')} event requires a factor")
    return float(factor)


class SIPSimulator:
    """Core simulation engine for Systematic Investment Plans (SIP)

    Supports deterministic growth modeling, friction event scheduling
    (pauses, skips, reductions, step-ups), and stochastic Monte Carlo simulations.
    """

    def __init__(
        self,
        monthly_amount: float,
        annual_return: float,
        years: int
    ):
        if monthly_amount <= 0:
            raise ValueError("Monthly amount must be positive.")
        if years <= 0:
            raise ValueError("Investment duration in years must be positive.")

        self.initial_monthly_amount = float(monthly_amount)
        self.annual_return = float(annual_return)
        self.monthly_return = float(annual_return) / 12.0
        self.total_months = int(years * 12)

    def calculate_ideal(self) -> Tuple[float, List[Dict[str, Any]]]:
        """Calculates ideal wealth accumulation without any friction events."""
        value = 0.0
        monthly_amount = self.initial_monthly_amount
        history: List[Dict[str, Any]] = []

        for month in range(1, self.total_months + 1):
            value = (value + monthly_amount) * (1.0 + self.monthly_return)
            if month % 12 == 0:
                history.append({
                    "year": month // 12,
                    "ideal_value": round(value, 2)
                })

        return round(value, 2), history

    def _build_cashflow_schedule(
        self, events: List[Dict[str, Any]]
    ) -> Tuple[List[float], List[float]]:
        """Pre-computes the expected and actual cashflow schedules for all months.

        Handles one-off events (SKIP, REDUCE, INCREASE), date ranges (PAUSE_RANGE),
        and recurring annual increases (STEP_UP).
        """
        event_map: Dict[int, List[Dict[str, Any]]] = {}
        pause_ranges: List[Tuple[int, int]] = []
        step_up_rate = 0.0

        for event in events or []:
            event_type = event.get("type")
            if event_type == "PAUSE_RANGE":
                start = event.get("start_month")
                end = event.get("end_month")
                if start is not None and end is not None:
                    pause_ranges.append((int(start), int(end)))
            elif event_type == "STEP_UP":
                step_up_rate = float(event.get("yearly_growth") or 0.0)
            else:
                month = event.get("month")
                if month is not None:
                    m = int(month)
                    if m not in event_map:
                        event_map[m] = []
                    event_map[m].append(event)

        expected_schedule: List[float] = []
        actual_schedule: List[float] = []

        current_base_amount = self.initial_monthly_amount

        for month in range(1, self.total_months + 1):
            expected_schedule.append(current_base_amount)
            contribution = current_base_amount

            # Check pause ranges
            is_paused = any(start <= month <= end for start, end in pause_ranges)
            if is_paused:
                contribution = 0.0

            # Process discrete month events
            if month in event_map:
                for event in event_map[month]:
                    e_type = event.get("type")
                    if e_type == "SKIP":
                        contribution = 0.0
                    elif e_type == "REDUCE":
                        contribution = current_base_amount * _required_factor(event)
                    elif e_type == "INCREASE":
                        current_base_amount *= _required_factor(event)
                        contribution = current_base_amount

            actual_schedule.append(max(0.0, contribution))

            # Annual step up applied at the end of each full year
            if step_up_rate > 0 and month % 12 == 0:
                current_base_amount *= (1.0 + step_up_rate)

        return expected_schedule, actual_schedule

    def calculate_actual(
        self, events: List[Dict[str, Any]]
    ) -> Tuple[float, float, float, List[Dict[str, Any]]]:
        """Calculates actual portfolio value considering investor friction events."""
        expected_schedule, actual_schedule = self._build_cashflow_schedule(events)

        value = 0.0
        history: List[Dict[str, Any]] = []

        for month in range(1, self.total_months + 1):
            contribution = actual_schedule[month - 1]
            value = (value + contribution) * (1.0 + self.monthly_return)

            if month % 12 == 0:
                history.append({
                    "year": month // 12,
                    "actual_value": round(value, 2)
                })

        total_expected = sum(expected_schedule)
        total_actual = sum(actual_schedule)

        return (
            round(value, 2),
            round(total_expected, 2),
            round(total_actual, 2),
            history
        )

    def monte_carlo(
        self,
        events: List[Dict[str, Any]],
        simulations: int = 1000,
        volatility: float = 0.15,
        seed: Optional[int] = None,
    ) -> Dict[str, float]:
        """Performs Monte Carlo simulation modeling market return uncertainty.

        Annual volatility is correctly converted to monthly volatility using
        the square-root-of-time rule: sigma_monthly = sigma_annual / sqrt(12).

        Each call draws from its own random.Random. The module-level
        random.gauss keeps shared state, which is not safe when several requests
        run in the server's thread pool at once, and it cannot be seeded per
        request. With a seed the same inputs give the same percentiles.
        """
        if simulations <= 0:
            raise ValueError("Simulations count must be positive.")

        _, actual_schedule = self._build_cashflow_schedule(events)

        monthly_mean = self.monthly_return
        monthly_vol = float(volatility) / math.sqrt(12.0)
        rng = random.Random(seed)

        results: List[float] = []

        for _ in range(simulations):
            val = 0.0
            for month in range(1, self.total_months + 1):
                contribution = actual_schedule[month - 1]
                monthly_rand_return = rng.gauss(monthly_mean, monthly_vol)
                # Ensure portfolio value does not become negative on extreme negative shocks
                val = max(0.0, (val + contribution) * (1.0 + monthly_rand_return))
            results.append(val)

        results.sort()

        def compute_percentile(p: float) -> float:
            if not results:
                return 0.0
            idx = p * (len(results) - 1)
            lower = int(idx)
            upper = min(lower + 1, len(results) - 1)
            weight = idx - lower
            interpolated = (1.0 - weight) * results[lower] + weight * results[upper]
            return round(interpolated, 2)

        return {
            "mean": round(sum(results) / len(results), 2),
            "p10": compute_percentile(0.10),
            "p50": compute_percentile(0.50),
            "p90": compute_percentile(0.90),
            "best_case": round(max(results), 2),
            "worst_case": round(min(results), 2)
        }
