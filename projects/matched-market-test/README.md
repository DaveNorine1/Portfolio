# Matched-market test

A four-pair geo test on a simulated panel of 40 markets. It matches pairs on pre-period behavior, checks them on weeks they weren't matched on, estimates lift with difference-in-differences, and runs A/A and power checks before turning the read into a scale-or-stop decision.

```
pip install numpy scipy pytest
python src/run.py
python -m pytest
```

Results are in `results/results.json`. All data is invented.
