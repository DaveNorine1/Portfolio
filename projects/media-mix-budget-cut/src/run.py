"""simulate three years of weekly data, fit the model, check it, and compare two ways to take a 20% cut."""
import json
from pathlib import Path
import numpy as np
from mmm import CHANNELS, Params, adstock, fit, optimize_budget, predict, weekly_media_leads

HERE = Path(__file__).resolve().parent.parent
WEEKS, HOLDOUT, CUT, BOOTSTRAPS = 156, 26, 0.20, 200

#all of this is invented, and the model never sees it
TRUTH = Params(baseline=620.0, trend=0.35, sin=45.0, cos=-30.0,
               beta=np.array([420.0, 260.0, 90.0, 300.0, 120.0]),
               decay=np.array([0.10, 0.35, 0.30, 0.65, 0.15]),
               half_sat=np.array([38000.0, 52000.0, 42000.0, 110000.0, 7000.0]))
MEAN_SPEND = np.array([62000.0, 58000.0, 36000.0, 70000.0, 9000.0])


def simulate(seed=20261):
    rng = np.random.default_rng(seed)
    t = np.arange(WEEKS, dtype=float)
    season = 1 + 0.25 * np.sin(2 * np.pi * (t - 6) / 52)
    spend = np.zeros((WEEKS, len(CHANNELS)))
    for j, mean in enumerate(MEAN_SPEND):
        noise = rng.lognormal(0, 0.28, WEEKS)
        spend[:, j] = mean * season * noise
    #ctv and display run in flights, which is what makes them hard to separate in real data
    for j, on, off in [(3, 8, 5), (2, 10, 3)]:
        cycle = (np.arange(WEEKS) % (on + off)) < on
        spend[:, j] *= cycle * (on + off) / on
    y = predict(TRUTH, spend, t) + rng.normal(0, 28, WEEKS)
    return t, spend, y


def repeat_across_seeds(runs=30, draws=40):
    #one simulated world can flatter a method, so run the whole exercise on many of them
    covered_gap, covered_opt, covered_cut, overstated, model_gain, true_gain = 0, 0, 0, 0, [], []
    for seed in range(runs):
        t, spend, y = simulate(1000 + seed)
        est = fit(spend, y, t, starts=3)
        current = spend[-52:].mean(axis=0)
        across, plan = current * (1 - CUT), optimize_budget(est, current, CUT)
        def change(p, s):
            base = p.baseline + p.trend * t[-1]
            return (base + weekly_media_leads(p, s).sum()) / (base + weekly_media_leads(p, current).sum()) - 1
        fitted, residuals = predict(est, spend, t), y - predict(est, spend, t)
        x0 = np.r_[est.baseline, est.trend, est.sin, est.cos, est.beta, est.decay, est.half_sat]
        rng = np.random.default_rng(seed)
        gaps, opts, cuts = [], [], []
        for _ in range(draws):
            starts = rng.integers(0, WEEKS - 8, WEEKS // 8 + 1)
            res = np.concatenate([residuals[s:s + 8] for s in starts])[:WEEKS]
            d = fit(spend, fitted + res, t, starts=1, x0=x0)
            opts.append(change(d, plan)); cuts.append(change(d, across)); gaps.append(opts[-1] - cuts[-1])
        truth_opt, truth_cut = change(TRUTH, plan), change(TRUTH, across)
        inside = lambda v, x: np.percentile(v, 2.5) <= x <= np.percentile(v, 97.5)
        covered_gap += inside(gaps, truth_opt - truth_cut)
        covered_opt += inside(opts, truth_opt)
        covered_cut += inside(cuts, truth_cut)
        estimated = change(est, plan) - change(est, across)
        overstated += estimated > truth_opt - truth_cut
        model_gain.append(estimated); true_gain.append(truth_opt - truth_cut)
    return {"runs": runs, "draws": draws, "coverage_even_cut": covered_cut / runs, "coverage_reallocation": covered_opt / runs,
            "coverage_gain": covered_gap / runs, "share_overstated": overstated / runs,
            "mean_model_gain": float(np.mean(model_gain)), "mean_true_gain": float(np.mean(true_gain)),
            "share_true_gain_positive": float(np.mean(np.array(true_gain) > 0))}


def main():
    t, spend, y = simulate()
    train = WEEKS - HOLDOUT

    #out-of-time check first: fit on the early weeks, score the last 26
    backtest = fit(spend[:train], y[:train], t[:train])
    #adstock has to run over the full series so holdout weeks inherit carryover
    pred = predict(backtest, spend, t)[train:]
    actual = y[train:]
    mape = float(np.mean(np.abs(pred - actual) / actual))
    r2 = float(1 - ((pred - actual) ** 2).sum() / ((actual - actual.mean()) ** 2).sum())
    naive = np.full(HOLDOUT, y[:train][-26:].mean())
    naive_mape = float(np.mean(np.abs(naive - actual) / actual))

    final = fit(spend, y, t)
    residuals = y - predict(final, spend, t)

    current = spend[-52:].mean(axis=0)
    across = current * (1 - CUT)
    optimized = optimize_budget(final, current, CUT)

    base_total = final.baseline + final.trend * t[-1]
    def total(params, s):
        return params.baseline + params.trend * t[-1] + weekly_media_leads(params, s).sum()

    def change(params, s):
        return total(params, s) / total(params, current) - 1

    #moving-block bootstrap of the residuals so autocorrelation survives the resample
    rng = np.random.default_rng(7)
    block = 8
    x0 = np.r_[final.baseline, final.trend, final.sin, final.cos, final.beta, final.decay, final.half_sat]
    fitted = predict(final, spend, t)
    across_draws, optimized_draws, gap_draws, opt_alloc = [], [], [], []
    for _ in range(BOOTSTRAPS):
        starts = rng.integers(0, WEEKS - block, WEEKS // block + 1)
        res = np.concatenate([residuals[s:s + block] for s in starts])[:WEEKS]
        draw = fit(spend, fitted + res, t, starts=1, x0=x0)
        a, o = change(draw, across), change(draw, optimized)
        across_draws.append(a)
        optimized_draws.append(o)
        gap_draws.append(o - a)
    ci = lambda v: [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))]

    out = {
        "note": "synthetic data; no real company figures",
        "seed": 20261,
        "channels": CHANNELS,
        "backtest": {"holdout_weeks": HOLDOUT, "mape": mape, "r2": r2, "naive_mape": naive_mape,
                     "weeks": t[train:].tolist(), "actual": actual.tolist(), "predicted": pred.tolist()},
        "recovery": {c: {"true_decay": float(TRUTH.decay[i]), "fit_decay": float(final.decay[i]),
                         "true_half_sat": float(TRUTH.half_sat[i]), "fit_half_sat": float(final.half_sat[i]),
                         "true_weekly_leads": float(weekly_media_leads(TRUTH, current)[i]),
                         "fit_weekly_leads": float(weekly_media_leads(final, current)[i])}
                     for i, c in enumerate(CHANNELS)},
        "scenario": {
            "cut": CUT, "current_spend": current.tolist(),
            "across_the_board": {"spend": across.tolist(), "leads_change": float(change(final, across)),
                                 "ci95": ci(across_draws), "truth": float(change(TRUTH, across))},
            "optimized": {"spend": optimized.tolist(), "leads_change": float(change(final, optimized)),
                          "ci95": ci(optimized_draws), "truth": float(change(TRUTH, optimized))},
            "gap": {"mean": float(np.mean(gap_draws)), "ci95": ci(gap_draws),
                    "share_positive": float(np.mean(np.array(gap_draws) > 0))},
        },
        "simulator": {"baseline": float(base_total), "shape": final.shape,
                      "beta": final.beta.tolist(), "decay": final.decay.tolist(),
                      "half_sat": final.half_sat.tolist(), "current": current.tolist(),
                      "weekly_total": float(total(final, current))},
    }
    out["across_seeds"] = repeat_across_seeds()
    (HERE / "results").mkdir(exist_ok=True)
    (HERE / "results" / "results.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({k: out[k] for k in ("recovery",)}, indent=1))
    print({k: v for k, v in out["backtest"].items() if k in ("mape", "r2", "naive_mape")})
    print(json.dumps(out["across_seeds"], indent=1))


if __name__ == "__main__":
    main()
