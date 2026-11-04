"""simulates a subscription business, fits the models on a past test, and compares who to target on new customers."""
import json
from pathlib import Path
import numpy as np
from sklearn.metrics import roc_auc_score
from retention import expected_months, fit, run_test, score, simulate, strategies, true_value

HERE = Path(__file__).resolve().parent.parent
COST, TRAIN, NEW, RUNS = 25.0, 30000, 20000, 20


def one(seed):
    rng = np.random.default_rng(seed)
    test = run_test(simulate(TRAIN, rng), rng)
    control, offer = fit(test, seed)
    new = simulate(NEW, rng)
    scored = score(new, control, offer, COST)
    truth = true_value(new, COST)
    strat = {k: float(truth[m].sum() / NEW * 1000) for k, m in strategies(scored, COST).items()}
    shares = {k: float(m.mean()) for k, m in strategies(scored, COST).items()}
    actual = np.random.default_rng(seed + 999).binomial(1, (1 - new.true_hazard) ** 6)
    true_ltv = new.margin * expected_months(new.true_hazard)
    gain = scored.offer_value > 0
    buckets = np.quantile(scored.p_control, np.linspace(0, 1, 11))
    idx = np.clip(np.digitize(scored.p_control, buckets[1:-1]), 0, 9)
    calibration = [[float(scored.p_control[idx == i].mean()), float(actual[idx == i].mean())] for i in range(10)]
    return {"strat": strat, "shares": shares, "auc": float(roc_auc_score(actual, scored.p_control)),
            "ltv_error": float(np.abs(scored.ltv - true_ltv).mean() / true_ltv.mean()), "ltv_corr": float(np.corrcoef(scored.ltv, true_ltv)[0, 1]),
            "estimated_gain": float(scored.offer_value[gain].sum() / NEW * 1000), "calibration": calibration,
            "right_call": float((gain.values == (truth > 0).values).mean()), "base_retention": float(actual.mean())}


def main():
    runs = [one(1000 + s) for s in range(RUNS)]
    names = list(runs[0]["strat"])
    table = {k: {"mean": float(np.mean([r["strat"][k] for r in runs])), "low": float(np.percentile([r["strat"][k] for r in runs], 2.5)),
                 "high": float(np.percentile([r["strat"][k] for r in runs], 97.5)), "share": float(np.mean([r["shares"][k] for r in runs]))} for k in names}
    best_wins = float(np.mean([max(r["strat"], key=r["strat"].get) == "Highest expected gain" for r in runs]))
    out = {"note": "synthetic data; no real company figures", "offer_cost": COST, "train_customers": TRAIN, "new_customers": NEW, "runs": RUNS, "strategies": table, "best_wins": best_wins}
    for k in ("auc", "ltv_error", "ltv_corr", "right_call", "estimated_gain", "base_retention"):
        out[k] = float(np.mean([r[k] for r in runs]))
    out["true_gain"] = table["Highest expected gain"]["mean"]
    out["calibration"] = np.mean([r["calibration"] for r in runs], axis=0).tolist()
    (HERE / "results").mkdir(exist_ok=True)
    (HERE / "results/results.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k != "calibration"}, indent=1)); print(np.round(out["calibration"], 3).tolist())


if __name__ == "__main__":
    main()
