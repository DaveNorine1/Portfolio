"""writes made-up daily contact-center volume for larkfield water, the fictional company in this project."""
import csv
from datetime import date, timedelta
from pathlib import Path
import numpy as np

rng = np.random.default_rng(42)
start = date(2025, 1, 1)
with open(Path(__file__).parent / "ticket_volume.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["date", "tickets"])
    for i in range(365):
        d = start + timedelta(days=i)
        season = 1 + 0.2 * np.sin(2 * np.pi * (i - 80) / 365)
        weekend = 0.55 if d.weekday() >= 5 else 1.0
        w.writerow([d.isoformat(), int(rng.poisson(120 * season * weekend))])
