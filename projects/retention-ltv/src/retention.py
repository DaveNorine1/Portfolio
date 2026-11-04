"""churn, lifetime value, and who should get a retention offer."""
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier as GBM

FEATURES = ["tenure_months", "orders_per_month", "discount_share", "support_tickets", "days_since_order", "paid_channel"]
HORIZON, OFFER_MONTHS, OBSERVED = 24, 6, 6


def expected_months(hazard, horizon=HORIZON):
    #expected active months from a constant monthly churn rate
    return (1 - (1 - hazard) ** horizon) * (1 - hazard) / hazard


def months_with_offer(h_control, h_offer, offer_months=OFFER_MONTHS, horizon=HORIZON):
    #the offer changes churn for its first months, then behavior returns to normal
    first = expected_months(h_offer, offer_months)
    later = expected_months(h_control, horizon - offer_months)
    return first + (1 - h_offer) ** offer_months * later


def to_hazard(retained, months=OBSERVED):
    return 1 - np.clip(retained, 0.001, 0.999) ** (1 / months)


def simulate(n, rng):
    d = pd.DataFrame({
        "tenure_months": rng.gamma(2.0, 7.0, n).clip(1, 72),
        "orders_per_month": rng.gamma(3.0, 0.7, n).clip(0.1, 8),
        "discount_share": rng.beta(1.6, 3.0, n),
        "support_tickets": rng.poisson(0.5, n),
        "days_since_order": rng.gamma(1.6, 11.0, n).clip(0, 120),
        "paid_channel": rng.binomial(1, 0.45, n),
    })
    d["margin"] = (d.orders_per_month * rng.normal(11, 2, n).clip(5, 20)).round(2)
    logit = (-2.45 - 0.022 * d.tenure_months - 0.22 * d.orders_per_month + 1.15 * d.discount_share
             + 0.22 * d.support_tickets + 0.021 * d.days_since_order + 0.2 * d.paid_channel)
    d["true_hazard"] = 1 / (1 + np.exp(-logit))
    #the offer helps price-sensitive customers, does little for the checked-out, and can wake up loyal ones
    effect = 0.08 + 0.75 * d.discount_share - 0.009 * d.days_since_order - 0.0045 * d.tenure_months
    d["true_effect"] = effect.clip(-0.2, 0.65)
    d["true_hazard_offer"] = (d.true_hazard * (1 - d.true_effect)).clip(0.001, 0.95)
    return d


def run_test(d, rng, share=0.5):
    #a randomized past offer: did each customer stay through the observed window
    d = d.copy()
    d["offered"] = rng.binomial(1, share, len(d))
    h = np.where(d.offered == 1, d.true_hazard_offer, d.true_hazard)
    d["retained"] = rng.binomial(1, (1 - h) ** OBSERVED)
    return d


def fit(test, seed=0):
    #one model per arm, so the gap between them estimates what the offer changes
    args = dict(max_depth=3, learning_rate=0.05, max_iter=200, min_samples_leaf=50, random_state=seed)
    control = GBM(**args).fit(test.loc[test.offered == 0, FEATURES], test.loc[test.offered == 0, "retained"])
    offer = GBM(**args).fit(test.loc[test.offered == 1, FEATURES], test.loc[test.offered == 1, "retained"])
    return control, offer


def score(d, control, offer, cost):
    out = d.copy()
    out["p_control"] = control.predict_proba(d[FEATURES])[:, 1]
    out["p_offer"] = offer.predict_proba(d[FEATURES])[:, 1]
    h0, h1 = to_hazard(out.p_control), to_hazard(out.p_offer)
    out["ltv"] = out.margin * expected_months(h0)
    added = months_with_offer(h0, h1) - expected_months(h0)
    out["offer_value"] = out.margin * added - cost
    return out


def true_value(d, cost):
    #what an offer is really worth for each customer, known only because the data is simulated
    return d.margin * (months_with_offer(d.true_hazard, d.true_hazard_offer) - expected_months(d.true_hazard)) - cost


def strategies(scored, cost):
    n = (scored.offer_value > 0).sum()
    risk_top = scored.p_control.rank(method="first") <= n
    value_top = scored.ltv.rank(method="first", ascending=False) <= n
    return {"Offer to no one": np.zeros(len(scored), bool), "Offer to everyone": np.ones(len(scored), bool),
            "Highest churn risk": risk_top.values, "Highest lifetime value": value_top.values,
            "Highest expected gain": (scored.offer_value > 0).values}
