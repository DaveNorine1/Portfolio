# Media mix model for a budget cut

A rebuild of the approach on synthetic data. It simulates three years of weekly leads across five channels, fits a media mix model with geometric adstock and Hill saturation, checks it on a 26-week holdout, and compares two ways to take a 20% cut. Because the data is simulated, the fitted model can be graded against the known truth.

```
pip install numpy scipy pytest
python src/run.py
python -m pytest
```

Results are in `results/results.json`. All data is invented.
