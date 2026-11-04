# Retention and lifetime value

Who should get a retention offer? This project simulates a subscription business, fits churn models to a randomized past offer, estimates each customer's lifetime value, and compares targeting rules on new customers. Because the data is simulated, every rule can be graded against what the offer was truly worth.

```
pip install numpy pandas scikit-learn pytest
python src/run.py
python -m pytest
```

Results are in `results/results.json`. All data is invented.
