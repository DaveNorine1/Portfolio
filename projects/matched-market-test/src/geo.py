"""matched-market test: pick pairs, estimate lift with difference-in-differences, check it against placebos."""
from itertools import product
import numpy as np
from scipy import stats


def match_pairs(log_leads, fit_weeks):
    #greedy: closest pre-period level and shape first, each market used once
    fit = log_leads[:, :fit_weeks]
    k = fit.shape[0]
    corr = np.corrcoef(fit - fit.mean(axis=1, keepdims=True))
    level = np.abs(fit.mean(axis=1)[:, None] - fit.mean(axis=1)[None, :])
    score = (1 - corr) + level
    np.fill_diagonal(score, np.inf)
    pairs, used = [], set()
    for i, j in sorted(((a, b) for a in range(k) for b in range(a + 1, k)), key=lambda x: score[x]):
        if i not in used and j not in used:
            pairs.append((i, j))
            used.update((i, j))
    return pairs


def pair_effect(log_leads, treated, control, pre, post):
    #difference-in-differences on logs, so the effect reads as an approximate percent lift
    t = log_leads[treated, post].mean() - log_leads[treated, pre].mean()
    c = log_leads[control, post].mean() - log_leads[control, pre].mean()
    return t - c


def effects(log_leads, pairs, pre, post):
    return np.array([pair_effect(log_leads, a, b, pre, post) for a, b in pairs])


def t_interval(values, level=0.95):
    n = len(values)
    mean = values.mean()
    se = values.std(ddof=1) / np.sqrt(n)
    half = stats.t.ppf(0.5 + level / 2, n - 1) * se
    return mean, mean - half, mean + half


def sign_flip_p(values):
    #exact randomization test: every way the coin flips could have assigned treatment
    observed = abs(values.mean())
    flips = [abs((values * np.array(s)).mean()) for s in product([1, -1], repeat=len(values))]
    return float(np.mean(np.array(flips) >= observed - 1e-12))


def normal_posterior(mean, se, prior_mean=0.0, prior_sd=0.10):
    #conjugate normal update with a skeptical prior centered on no effect
    precision = 1 / prior_sd**2 + 1 / se**2
    post_mean = (prior_mean / prior_sd**2 + mean / se**2) / precision
    return post_mean, np.sqrt(1 / precision)
