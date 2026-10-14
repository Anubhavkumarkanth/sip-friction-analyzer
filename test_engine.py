"""Engine and metric tests. No database or network is needed.

Expected values come from the closed-form annuity-due formula, not from running
the engine and pasting its output back in:

    future value = P * ((1 + i)^n - 1) / i * (1 + i)

with P the monthly amount, i the monthly rate (annual / 12) and n the number of
months. The engine adds each contribution and then applies the month's growth,
which is exactly the "due" convention.
"""

import random

import pytest

from engine.friction import calculate_ccr, calculate_cld, calculate_discipline_score
from engine.simulation import SIPSimulator


def annuity_due(monthly_amount, annual_rate, months):
    i = annual_rate / 12
    return monthly_amount * (((1 + i) ** months - 1) / i) * (1 + i)


def run(events, monthly_amount=5000, annual_return=0.12, years=1):
    sim = SIPSimulator(monthly_amount=monthly_amount, annual_return=annual_return, years=years)
    ideal, _ = sim.calculate_ideal()
    actual, total_expected, total_actual, _ = sim.calculate_actual(events)
    return ideal, actual, total_expected, total_actual


# ---------------------------------------------------------------- compounding
def test_a_contribution_is_invested_at_the_start_of_its_month():
    # Only month 1 is paid. It is added, then grows for all twelve months.
    _, actual, _, actual_total = run(
        [{"type": "PAUSE_RANGE", "start_month": 2, "end_month": 12}], monthly_amount=1000,
    )
    assert actual_total == 1000
    assert actual == pytest.approx(1000 * 1.01**12, abs=0.01)


@pytest.mark.parametrize("amount,rate,years", [(10000, 0.12, 10), (2500, 0.08, 25), (50000, 0.15, 3)])
def test_ideal_value_matches_closed_form(amount, rate, years):
    ideal, history = SIPSimulator(amount, rate, years).calculate_ideal()
    assert ideal == pytest.approx(annuity_due(amount, rate, years * 12), abs=0.01)
    assert len(history) == years
    assert history[-1] == {"year": years, "ideal_value": ideal}


def test_zero_return_is_just_the_sum_of_contributions():
    ideal, actual, expected_total, actual_total = run([], monthly_amount=1000, annual_return=0.0, years=2)
    assert ideal == actual == expected_total == actual_total == 24000.0


# ------------------------------------------------------------- friction events
def test_skipping_one_month_loses_that_contribution_compounded_to_the_end():
    # Month 2 of 12: the skipped 5000 would have grown for 11 more months.
    ideal, actual, expected_total, actual_total = run([{"type": "SKIP", "month": 2}])
    assert ideal - actual == pytest.approx(5000 * 1.01**11, abs=0.01)
    assert expected_total - actual_total == 5000


def test_reducing_a_month_loses_only_the_missing_part():
    ideal, actual, *_ = run([{"type": "REDUCE", "month": 5, "factor": 0.4}])
    assert ideal - actual == pytest.approx(5000 * 0.6 * 1.01**8, abs=0.01)


def test_pause_range_is_inclusive_at_both_ends():
    _, _, expected_total, actual_total = run([{"type": "PAUSE_RANGE", "start_month": 3, "end_month": 5}])
    assert expected_total - actual_total == 3 * 5000


def test_pausing_every_month_leaves_nothing_and_scores_zero():
    ideal, actual, expected_total, actual_total = run([{"type": "PAUSE_RANGE", "start_month": 1, "end_month": 12}])
    assert actual == 0.0 and actual_total == 0.0

    ccr = calculate_ccr(expected_total, actual_total)
    score = calculate_discipline_score(ccr, calculate_cld(ideal, actual) / ideal)
    assert (ccr, score) == (0.0, 0.0)


def test_step_up_raises_each_year_by_the_given_rate():
    _, _, expected_total, actual_total = run([{"type": "STEP_UP", "yearly_growth": 0.10}], years=3)
    assert actual_total == expected_total
    assert expected_total == pytest.approx(12 * 5000 * (1 + 1.1 + 1.1**2), abs=0.01)


def test_a_step_up_can_beat_the_flat_ideal_and_the_loss_floors_at_zero():
    ideal, actual, expected_total, actual_total = run([{"type": "STEP_UP", "yearly_growth": 0.10}], years=5)
    assert actual > ideal
    assert calculate_cld(ideal, actual) == 0.0
    assert calculate_ccr(expected_total, actual_total) == 1.0


def test_an_event_without_its_factor_is_an_error_not_a_silent_no_op():
    sim = SIPSimulator(5000, 0.12, 1)
    for event in ({"type": "REDUCE", "month": 3, "factor": None}, {"type": "INCREASE", "month": 3}):
        with pytest.raises(ValueError, match="requires a factor"):
            sim.calculate_actual([event])


def test_rejects_non_positive_inputs():
    with pytest.raises(ValueError):
        SIPSimulator(monthly_amount=0, annual_return=0.12, years=5)
    with pytest.raises(ValueError):
        SIPSimulator(monthly_amount=5000, annual_return=0.12, years=0)
    with pytest.raises(ValueError):
        SIPSimulator(5000, 0.12, 5).monte_carlo(events=[], simulations=0)


def test_random_skip_reduce_pause_schedules_never_beat_the_ideal():
    """Property check over generated schedules (fixed seed, so it cannot flake)."""
    rng = random.Random(20261014)
    for _ in range(200):
        years = rng.randint(1, 15)
        events = []
        for _ in range(rng.randint(0, 6)):
            kind = rng.choice(["SKIP", "REDUCE", "PAUSE_RANGE"])
            month = rng.randint(1, years * 12)
            if kind == "SKIP":
                events.append({"type": "SKIP", "month": month})
            elif kind == "REDUCE":
                events.append({"type": "REDUCE", "month": month, "factor": rng.uniform(0.05, 1.0)})
            else:
                events.append({"type": "PAUSE_RANGE", "start_month": month, "end_month": month + rng.randint(0, 12)})

        ideal, actual, expected_total, actual_total = run(events, years=years)
        ccr = calculate_ccr(expected_total, actual_total)
        score = calculate_discipline_score(ccr, calculate_cld(ideal, actual) / ideal)

        assert actual <= ideal + 0.01
        assert 0.0 <= ccr <= 1.0
        assert 0.0 <= score <= 100.0


# ------------------------------------------------------------------ the metrics
def test_ccr_is_clamped_and_safe_with_nothing_expected():
    assert calculate_ccr(0, 0) == 1.0
    assert calculate_ccr(100, 150) == 1.0
    assert calculate_ccr(100, 25) == 0.25


def test_discipline_score_weights_skipped_money_at_40_and_lost_growth_at_60():
    assert calculate_discipline_score(1.0, 0.0) == 100.0
    assert calculate_discipline_score(0.5, 0.0) == 80.0
    assert calculate_discipline_score(1.0, 0.5) == 70.0
    assert calculate_discipline_score(0.5, 0.5) == 50.0
    assert calculate_discipline_score(0.0, 1.0) == 0.0
    # Out-of-range inputs are clamped instead of producing a score outside 0-100.
    assert calculate_discipline_score(2.0, -1.0) == 100.0


# ------------------------------------------------------------------ Monte Carlo
def test_monte_carlo_with_a_seed_is_reproducible():
    sim = SIPSimulator(5000, 0.12, 5)
    first = sim.monte_carlo(events=[], simulations=300, volatility=0.15, seed=7)
    again = sim.monte_carlo(events=[], simulations=300, volatility=0.15, seed=7)
    other = sim.monte_carlo(events=[], simulations=300, volatility=0.15, seed=8)
    assert first == again
    assert first != other


def test_monte_carlo_with_almost_no_volatility_collapses_to_the_deterministic_answer():
    sim = SIPSimulator(5000, 0.12, 5)
    deterministic, *_ = sim.calculate_actual([])
    result = sim.monte_carlo(events=[], simulations=50, volatility=1e-9, seed=1)
    for key in ("p10", "p50", "p90", "mean"):
        assert result[key] == pytest.approx(deterministic, rel=1e-6)


def test_monte_carlo_percentiles_are_ordered_and_follow_the_events():
    sim = SIPSimulator(5000, 0.12, 5)
    full = sim.monte_carlo(events=[], simulations=400, volatility=0.15, seed=3)
    paused = sim.monte_carlo(
        events=[{"type": "PAUSE_RANGE", "start_month": 1, "end_month": 30}],
        simulations=400, volatility=0.15, seed=3,
    )
    assert full["worst_case"] <= full["p10"] <= full["p50"] <= full["p90"] <= full["best_case"]
    assert paused["p50"] < full["p50"]


def test_monte_carlo_with_one_simulation_reports_that_one_value_everywhere():
    result = SIPSimulator(5000, 0.12, 2).monte_carlo(events=[], simulations=1, volatility=0.15, seed=4)
    assert len({result[k] for k in ("mean", "p10", "p50", "p90", "best_case", "worst_case")}) == 1


def test_wider_volatility_widens_the_spread():
    sim = SIPSimulator(5000, 0.12, 10)
    calm = sim.monte_carlo(events=[], simulations=500, volatility=0.05, seed=11)
    wild = sim.monte_carlo(events=[], simulations=500, volatility=0.40, seed=11)
    assert (wild["p90"] - wild["p10"]) > (calm["p90"] - calm["p10"])
