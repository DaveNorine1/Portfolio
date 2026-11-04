import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from mmm import adstock, hill, optimize_budget, Params, weekly_media_leads


def test_adstock_carries_over():
    assert np.allclose(adstock(np.array([100.0, 0, 0]), 0.5), [100, 50, 25])


def test_hill_is_half_at_half_saturation():
    assert abs(hill(np.array([50.0]), 50.0, 1.5)[0] - 0.5) < 1e-9


def test_hill_never_increases_marginal_return_past_half_sat():
    x = np.linspace(100, 1000, 50)
    assert (np.diff(hill(x, 100.0, 1.5)) > 0).all()
    assert (np.diff(hill(x, 100.0, 1.5), 2) < 0).all()


def _params():
    return Params(100, 0, 0, 0, np.array([200.0, 50.0]), np.array([0.2, 0.2]), np.array([50.0, 50.0]))


def test_optimizer_spends_exactly_the_reduced_budget():
    current = np.array([100.0, 100.0])
    assert abs(optimize_budget(_params(), current, 0.15).sum() - 170) < 1e-4


def test_optimizer_respects_guardrails():
    current = np.array([100.0, 100.0])
    s = optimize_budget(_params(), current, 0.15, low=0.5, high=1.5)
    assert (s >= 50 - 1e-6).all() and (s <= 150 + 1e-6).all()


def test_optimizer_beats_across_the_board():
    current = np.array([100.0, 100.0])
    p = _params()
    assert weekly_media_leads(p, optimize_budget(p, current, 0.15)).sum() > weekly_media_leads(p, current * 0.85).sum()
