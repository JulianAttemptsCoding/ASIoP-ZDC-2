# Study Summary

## Bottom Line

The local ROOT file was verified against the `US-CENTRAL1` GCS object already usable by Vertex AI.
After the user directed use of the prior `ML ZDC all` implementation, the ECAL/HCAL hit-signal gate
was resolved as scale `1.0` GeV for `ecal_energy` and `hcal_energy`.

The accepted completed result is the prior Vertex scalar-feature/XGBoost run:

`gs://asiop-zdc-1-zdc-reco-us-central1/runs/full-cpu-20260710-finalfix2/outputs`

## Data Facts

- Local file:
  `C:\Users\Julia\OneDrive\Desktop\coding\ASIoP\ML ZDC all 1\myTree_20251117_765k_0to300GeV_neutron_All.root`
- Vertex/GCS data URI:
  `gs://asiop-zdc-1-zdc-reco-us-central1/data/myTree_20251117_765k_0to300GeV_neutron_All.root`
- Size: `25,022,001,408` bytes.
- SHA-256: `b7c666040e42352e158a9a3f78158d147cb2e056c6c88248d892c956f5c7b533`.
- CRC32C: `lCVUvQ==`.
- Latest tree: `myTree;865` with `764,940` entries.
- Truth pass verified exactly one PDG `2112` neutron candidate per event.

## Accepted Result

- Champion: `M1_xgb_focus_only`
- Split counts: train `612,825`, validation `76,010`, test `76,105`
- Focus test count: `50,685`
- Focus-test macro RMS relative four-vector error: `0.20443314430393622`
- Energy MAE: `11.48034175891426 GeV`
- Energy relative RMSE: `0.1543518245985`
- Angular median: `5.872449369417561 mrad`
- Angular 68/95: `7.98112692599035 / 16.62022486411495 mrad`

## Expanded Graphs

Expanded study figures are in `outputs/plots/expanded_diagnostics/`. The requested boosting plots
are files `19` through `23`: overall loss and separate `E`, `px`, `py`, and `pz` train/validation
RMSE curves. The same folder also contains native-head losses, train-validation gap plots, feature
importance, feature/error correlations, energy-slice diagnostics, angular-error plots,
response-density plots, and component metric summaries.

## Previous Vertex Comparison

The accepted `finalfix2` XGBoost champion was compared against prior successful Vertex jobs in
`asiop-zdc-1`. Versus the previous `finalfix` champion (`B1_ridge_constrained`), it reduced macro
RMS relative four-vector error by `37.61%`, energy MAE by `49.24%`, energy relative RMSE by
`40.78%`, angular median by `77.65%`, and angular 95% by `81.08%`. The comparison report is
`outputs/reports/expanded_diagnostics/previous_vertex_comparison_summary.md`.

## Caveat

This is a completed scalar-feature/XGBoost Vertex run from the prior implementation. The newer
dual-grid T4 neural path requested by the stricter prompt is not present in the accepted run.
