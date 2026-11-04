import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from geo import effects, match_pairs, normal_posterior, sign_flip_p, t_interval


def test_did_recovers_a_known_lift_exactly():
    panel = np.ones((2, 10))
    panel[0, 8:] += 0.05
    assert abs(effects(panel, [(0, 1)], np.arange(8), np.arange(8, 10))[0] - 0.05) < 1e-12


def test_common_shock_does_not_move_the_estimate():
    panel = np.ones((2, 10))
    panel[:, 8:] += 0.3
    assert abs(effects(panel, [(0, 1)], np.arange(8), np.arange(8, 10))[0]) < 1e-12


def test_pairs_use_each_market_once():
    rng = np.random.default_rng(0)
    pairs = match_pairs(rng.normal(size=(10, 30)), 30)
    flat = [m for p in pairs for m in p]
    assert len(flat) == len(set(flat)) == 10


def test_four_pairs_cannot_reach_significance_by_randomization_alone():
    assert sign_flip_p(np.array([0.1, 0.1, 0.1, 0.1])) == 0.125


def test_interval_contains_the_mean():
    m, l, h = t_interval(np.array([0.01, 0.05, 0.03, 0.07]))
    assert l < m < h


def test_prior_pulls_estimate_toward_zero():
    m, _ = normal_posterior(0.1, 0.05)
    assert 0 < m < 0.1
