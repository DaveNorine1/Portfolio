# Forecasting consumer sentiment

University of Michigan Master of Applied Data Science capstone, built with Paul Stotts and Ali Alrubaiee. We used 40+ monthly FRED series to forecast the University of Michigan Consumer Sentiment Index.

`results/` holds tables saved from the team's project. The code stays in the team's private repository.

- `model_comparison.csv`: model scores from the saved comparison
- `selected_feature_importance.csv`: top features in the saved run
- `selected_umcsent_correlations.csv`: correlations with sentiment for selected series
- `scenario_analysis_results.csv`: saved scenario forecasts

The linear model's R² of 0.989 in that table should not be read as forecast accuracy. A three-month moving average of sentiment itself carries 94% of feature importance, and the scenarios barely move the forecast, so those models are mostly predicting sentiment from sentiment. The team separately reported a held-out LASSO R² of about 0.68 under a different protocol.
