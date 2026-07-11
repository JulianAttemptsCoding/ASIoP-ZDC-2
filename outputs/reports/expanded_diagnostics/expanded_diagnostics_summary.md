# Expanded Diagnostics Summary

This folder adds training/validation loss-vs-boosting diagnostics, broader result-study plots, and previous Vertex model comparisons for the accepted all-neutron scalar-feature/XGBoost result.

## Loss Curves

- Overall best validation relative four-vector RMSE: `0.2143414040678046` at boosting round `735`.
- `E` best validation RMSE: `20.408325706358482` GeV at boosting round `980`.
- `px` best validation RMSE: `5.177989169890205` GeV at boosting round `2499`.
- `py` best validation RMSE: `5.20788450849503` GeV at boosting round `2499`.
- `pz` best validation RMSE: `19.135673644391403` GeV at boosting round `980`.

## Previous Vertex Comparison

See `previous_vertex_comparison_summary.md`. Headline: accepted `finalfix2` reduced macro test error by `37.61%`, energy MAE by `49.24%`, and angular median by `77.65%` relative to previous `finalfix` champion.

## Figure Index

- `01_data_overview.png`
- `02_component_pred_vs_true.png`
- `03_component_residuals.png`
- `04_component_metric_bars.png`
- `05_energy_bias_resolution_slices.png`
- `06_component_bias_resolution_slices.png`
- `07_angular_error.png`
- `08_validation_leaderboard.png`
- `09_feature_importance.png`
- `10_pencil_vs_all_neutron_energy.png`
- `11_mass_shell_residual.png`
- `12_energy_response_density.png`
- `13_training_validation_loss_overall.png`
- `14_training_validation_loss_components.png`
- `15_training_validation_loss_native_heads.png`
- `16_error_driver_correlations.png`
- `17_tail_feature_contrast.png`
- `18_test_focus_energy_slice_diagnostics.png`
- `19_loss_overall_train_validation_vs_boosting.png`
- `20_loss_E_train_validation_vs_boosting.png`
- `21_loss_px_train_validation_vs_boosting.png`
- `22_loss_py_train_validation_vs_boosting.png`
- `23_loss_pz_train_validation_vs_boosting.png`
- `24_native_target_loss_grid_vs_boosting.png`
- `25_loss_overall_train_validation_gap.png`
- `26_loss_component_train_validation_gaps.png`
- `27_loss_best_round_train_vs_validation_bars.png`
- `28_component_metric_comparison_focus_vs_all.png`
- `29_component_resolution_energy_slice_heatmap.png`
- `30_top_feature_error_correlations.png`
- `31_previous_vertex_champion_metric_comparison.png`
- `32_previous_vertex_percent_improvement_vs_finalfix.png`
- `33_previous_vertex_validation_leaderboard_log.png`
- `34_previous_vertex_interval_coverage.png`
- `35_previous_vertex_energy_response_bias.png`
- `36_previous_vertex_job_chronology.png`
