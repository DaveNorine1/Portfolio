"""media mix model with geometric adstock and hill saturation, fit by nonlinear least squares."""
from dataclasses import dataclass
import numpy as np
from scipy.optimize import least_squares, minimize

CHANNELS = ["paid_search", "paid_social", "display", "ctv", "email"]


def adstock(x, decay):
    #carryover: this week's effective spend includes a decayed share of last week's
    out = np.zeros_like(x, dtype=float)
    carry = 0.0
    for i, value in enumerate(x):
        carry = value + decay * carry
        out[i] = carry
    return out


def hill(x, half_sat, shape):
    #diminishing returns: 0 at no spend, 0.5 at half_sat, approaches 1
    x = np.maximum(x, 1e-9)
    return x**shape / (x**shape + half_sat**shape)


@dataclass
class Params:
    baseline: float
    trend: float
    sin: float
    cos: float
    beta: np.ndarray
    decay: np.ndarray
    half_sat: np.ndarray
    shape: float = 1.5


def predict(params, spend, t):
    season = 2 * np.pi * t / 52
    y = params.baseline + params.trend * t + params.sin * np.sin(season) + params.cos * np.cos(season)
    for j in range(spend.shape[1]):
        y = y + params.beta[j] * hill(adstock(spend[:, j], params.decay[j]), params.half_sat[j], params.shape)
    return y


def _pack(p):
    return np.r_[p.baseline, p.trend, p.sin, p.cos, p.beta, p.decay, p.half_sat]


def _unpack(v, k, shape):
    return Params(v[0], v[1], v[2], v[3], v[4:4 + k], v[4 + k:4 + 2 * k], v[4 + 2 * k:4 + 3 * k], shape)


def fit(spend, y, t, shape=1.5, starts=6, seed=0, x0=None):
    #multi-start because adstock and saturation trade off against each other
    k = spend.shape[1]
    scale = spend.mean(axis=0)
    lower = np.r_[0, -np.inf, -np.inf, -np.inf, np.zeros(k), np.zeros(k), scale * 0.2]
    upper = np.r_[np.inf, np.inf, np.inf, np.inf, np.full(k, y.max() * 2), np.full(k, 0.9), scale * 8]
    rng = np.random.default_rng(seed)

    def residual(v):
        return predict(_unpack(v, k, shape), spend, t) - y

    best = None
    for i in range(starts):
        if i == 0 and x0 is not None:
            start = np.clip(x0, lower + 1e-9, upper - 1e-9)
        else:
            start = np.r_[y.mean() * 0.6, 0, 0, 0, rng.uniform(0.05, 0.3, k) * y.mean(),
                          rng.uniform(0.1, 0.6, k), scale * rng.uniform(0.8, 3, k)]
        result = least_squares(residual, start, bounds=(lower, upper), max_nfev=400)
        if best is None or result.cost < best.cost:
            best = result
    return _unpack(best.x, k, shape)


def weekly_media_leads(params, weekly_spend):
    #steady state: constant spend s adstocks to s / (1 - decay)
    effective = np.asarray(weekly_spend, dtype=float) / (1 - params.decay)
    return params.beta * hill(effective, params.half_sat, params.shape)


def optimize_budget(params, current, cut=0.20, low=0.5, high=1.5):
    #maximize steady-state leads at the reduced budget, each channel held within guardrails
    current = np.asarray(current, dtype=float)
    budget = current.sum() * (1 - cut)
    bounds = [(c * low, c * high) for c in current]

    def objective(s):
        return -weekly_media_leads(params, s).sum()

    best = None
    rng = np.random.default_rng(0)
    for i in range(12):
        start = current * (1 - cut) if i == 0 else current * rng.uniform(low, high, len(current))
        start = np.clip(start * budget / start.sum(), [b[0] for b in bounds], [b[1] for b in bounds])
        result = minimize(objective, start, bounds=bounds, method="SLSQP",
                          constraints={"type": "eq", "fun": lambda s: s.sum() - budget},
                          options={"maxiter": 500, "ftol": 1e-9})
        if result.success and (best is None or result.fun < best.fun):
            best = result
    if best is None:
        raise RuntimeError("budget optimizer did not converge")
    return best.x
