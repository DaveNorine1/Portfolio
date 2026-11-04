"""simulate a market panel, run a four-pair test, and turn the read into a scale-or-stop call."""
import json
from pathlib import Path
import numpy as np
from scipy import stats
from geo import effects, match_pairs, normal_posterior, sign_flip_p, t_interval

HERE = Path(__file__).resolve().parent.parent
MARKETS, PRE, TEST, FIT_WEEKS = 40, 78, 8, 52
TRUE_LIFT, N_PAIRS = 0.07, 4
#invented economics for the decision
SPEND_PER_MARKET_WEEK, VALUE_PER_LEAD = 4500.0, 180.0


def simulate(seed=511):
    rng = np.random.default_rng(seed)
    weeks = PRE + TEST
    t = np.arange(weeks)
    common = 0.10 * np.sin(2 * np.pi * t / 52) + np.cumsum(rng.normal(0, 0.006, weeks))
    size = rng.uniform(np.log(120), np.log(650), MARKETS)
    regional = rng.normal(0, 1, (6, weeks)).cumsum(axis=1) * 0.008
    region = rng.integers(0, 6, MARKETS)
    noise = rng.normal(0, 0.055, (MARKETS, weeks))
    return size[:, None] + common + regional[region] + noise


def main():
    log_leads = simulate()
    pre = np.arange(PRE)
    post = np.arange(PRE, PRE + TEST)
    pairs = match_pairs(log_leads, FIT_WEEKS)

    #score each pair on weeks it was not matched on, then keep the four tightest
    def holdout_gap(p):
        a, b = p
        return np.std(log_leads[a, FIT_WEEKS:PRE] - log_leads[b, FIT_WEEKS:PRE])

    ranked = sorted(pairs, key=holdout_gap)
    chosen = ranked[:N_PAIRS]
    rng = np.random.default_rng(99)
    #coin flip decides which market in each pair gets the campaign
    chosen = [(a, b) if rng.random() < 0.5 else (b, a) for a, b in chosen]
    treated_panel = log_leads.copy()
    for a, _ in chosen:
        treated_panel[a, post] += TRUE_LIFT

    pair_lift = effects(treated_panel, chosen, pre, post)
    mean, low, high = t_interval(pair_lift)

    #a/a: untreated pairs from the rest of the pool over the real test window
    rest = ranked[N_PAIRS:]
    rng = np.random.default_rng(3)
    aa_means, hits = [], 0
    draws = 4000
    for _ in range(draws):
        idx = rng.choice(len(rest), N_PAIRS, replace=False)
        signs = rng.choice([-1, 1], N_PAIRS)
        e = effects(log_leads, [rest[i] for i in idx], pre, post) * signs
        _, l, h = t_interval(e)
        aa_means.append(e.mean())
        hits += (l > 0) or (h < 0)
    aa_sd = float(np.std(aa_means))
    pair_sd = aa_sd * np.sqrt(N_PAIRS)
    false_positive = hits / draws

    #power: how often would n pairs clear zero if the lift were real
    power = []
    for n in (2, 4, 6, 8, 12, 16):
        rejected = 0
        pool = rest
        for _ in range(3000):
            idx = rng.choice(len(pool), min(n, len(pool)), replace=False)
            signs = rng.choice([-1, 1], len(idx))
            e = effects(log_leads, [pool[i] for i in idx], pre, post) * signs + TRUE_LIFT
            _, l, _h = t_interval(e)
            rejected += l > 0
        power.append({"pairs": n, "power": rejected / 3000})

    #decision: does the campaign pay back at this lift
    #counterfactual comes from observed leads and the estimated lift, as it would in real life
    observed = np.exp(treated_panel[[a for a, _ in chosen]][:, post]).sum()
    base = observed / np.exp(mean)
    incremental = observed - base
    spend = SPEND_PER_MARKET_WEEK * N_PAIRS * TEST
    breakeven_leads = spend / VALUE_PER_LEAD
    breakeven_lift = float(np.log(1 + breakeven_leads / base))
    se = pair_sd / np.sqrt(N_PAIRS)
    post_mean, post_sd = normal_posterior(mean, se)
    prob_positive = float(1 - stats.norm.cdf(0, post_mean, post_sd))
    prob_pays = float(1 - stats.norm.cdf(breakeven_lift, post_mean, post_sd))

    def index(series):
        return (np.exp(series) / np.exp(series[:, pre]).mean(axis=1, keepdims=True)).mean(axis=0) * 100

    treated = treated_panel[[a for a, _ in chosen]]
    control = treated_panel[[b for _, b in chosen]]
    out = {
        "note": "synthetic data; no real company figures",
        "true_lift_log": TRUE_LIFT,
        "true_lift_pct": float(np.exp(TRUE_LIFT) - 1),
        "pairs": [{"pair": f"Pair {i + 1}", "lift": float(v)} for i, v in enumerate(pair_lift)],
        "estimate": {"lift": float(mean), "low": float(low), "high": float(high),
                     "lift_pct": float(np.exp(mean) - 1), "low_pct": float(np.exp(low) - 1),
                     "high_pct": float(np.exp(high) - 1), "sign_flip_p": sign_flip_p(pair_lift),
                     "sign_flip_min_p": 2 / 2**N_PAIRS},
        "checks": {"aa_pool_pairs": len(rest), "aa_draws": draws, "aa_false_positive": false_positive, "aa_sd": aa_sd},
        "power": power,
        "decision": {"spend": spend, "value_per_lead": VALUE_PER_LEAD, "base_leads": float(base),
                     "incremental_leads": float(incremental), "breakeven_lift_pct": float(np.exp(breakeven_lift) - 1),
                     "cost_per_incremental_lead": float(spend / incremental),
                     "posterior_mean_pct": float(np.exp(post_mean) - 1),
                     "posterior_low_pct": float(np.exp(post_mean - 1.96 * post_sd) - 1),
                     "posterior_high_pct": float(np.exp(post_mean + 1.96 * post_sd) - 1),
                     "prob_positive": prob_positive, "prob_pays_back": prob_pays},
        "series": {"week": list(range(-PRE, TEST)), "treated": index(treated).tolist(), "control": index(control).tolist()},
    }
    (HERE / "results").mkdir(exist_ok=True)
    (HERE / "results" / "results.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k != "series"}, indent=1))


if __name__ == "__main__":
    main()
