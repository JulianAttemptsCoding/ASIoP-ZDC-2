# Previous Vertex Model Comparison

Compared accepted `full-cpu-20260710-finalfix2` against previous successful Vertex outputs in project `asiop-zdc-1`:

- `full-cpu-20260710`: first completed full CPU run; champion `B1_ridge_constrained`; XGBoost validation candidates numerically blew up and were unusable.
- `full-cpu-20260710-finalfix`: previous successful/fixed run; champion `B1_ridge_constrained`.
- `full-cpu-20260710-finalfix2`: accepted run; champion `M1_xgb_focus_only`.

## Accepted vs Previous finalfix Champion

- Macro RMS relative four-vector error: `0.3276764732159172` -> `0.20443314430393622` (`37.61%` reduction).
- Energy MAE: `22.61899985919906 GeV` -> `11.48034175891426 GeV` (`49.24%` reduction).
- Energy relative RMSE: `0.26065339433663753` -> `0.1543518245985` (`40.78%` reduction).
- Angular median: `26.27980332575699 mrad` -> `5.872449369417561 mrad` (`77.65%` reduction).
- Angular 95%: `87.82566429883639 mrad` -> `16.62022486411495 mrad` (`81.08%` reduction).
- Mean energy-response bias magnitude: `0.0735128616961136` -> `0.023760074912790228` (`67.68%` reduction).

## Interpretation

The accepted run changes the selected champion from the ridge baseline to the XGBoost focus-only model after fixing the previous XGBoost failure mode. The main gains are energy scale/resolution and angular reconstruction, while empirical interval coverage remains near nominal in `finalfix` and `finalfix2`.

## Artifacts

- `previous_vertex_champion_comparison.csv`: champion metrics by run.
- `previous_vertex_improvement_vs_accepted.csv`: absolute and percent improvements.
- `previous_vertex_validation_leaderboards.csv`: validation candidate table by run.
- `previous_vertex_job_chronology.csv`: Vertex custom-job audit.
- `31_previous_vertex_champion_metric_comparison.png` through `36_previous_vertex_job_chronology.png`: comparison plots.
