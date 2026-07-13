# Direct-kinetic XGBoost accuracy diagnostics

Plots use calibrated M1_xgb_focus_only outputs from the completed direct-kinetic
Vertex job. Predictions are joined to the locked target table by event_uid and
filtered to 50-250 GeV.
All component quantities are reconstructed physical GeV values.

Regression has no classification accuracy. Tolerance figures report explicit
fractions within 1, 5, and 10 GeV and within 1%, 5%, and 10% of true total energy.
Normalized momentum residuals use (prediction - truth) / E_true to avoid singular
values at px or py near zero.

The generator validates energy MAE, energy-relative RMSE, angular quantiles, and
maximum mass-shell residual against saved focus_test_metrics.json before
writing plots.
Per-boosting loss curves were not persisted in the direct-kinetic output artifacts.
