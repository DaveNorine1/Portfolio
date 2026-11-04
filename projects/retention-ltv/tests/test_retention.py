import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from retention import expected_months, months_with_offer, run_test, simulate, strategies, to_hazard, true_value, fit, score


def test_expected_months_matches_a_manual_sum():
    h = 0.1
    assert abs(expected_months(h, 12) - sum((1 - h) ** t for t in range(1, 13))) < 1e-9


def test_offer_with_no_effect_adds_no_months():
    assert abs(months_with_offer(0.05, 0.05) - expected_months(0.05)) < 1e-9


def test_lower_churn_during_the_offer_adds_months():
    assert months_with_offer(0.05, 0.02) > expected_months(0.05)


def test_hazard_round_trip():
    assert abs(to_hazard((1 - 0.07) ** 6) - 0.07) < 1e-9


def test_some_customers_are_hurt_by_an_offer():
    d = simulate(5000, np.random.default_rng(0))
    assert (d.true_effect < 0).any() and (d.true_effect > 0).any()


def test_targeting_compares_equal_group_sizes():
    rng = np.random.default_rng(1)
    t = run_test(simulate(4000, rng), rng)
    c, o = fit(t)
    s = strategies(score(simulate(2000, rng), c, o, 25.0), 25.0)
    assert s["Highest churn risk"].sum() == s["Highest expected gain"].sum() == s["Highest lifetime value"].sum()


def test_offer_to_no_one_is_worth_zero():
    d = simulate(100, np.random.default_rng(2))
    assert true_value(d, 25.0)[np.zeros(100, bool)].sum() == 0
