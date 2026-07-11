# ZDC Single-Neutron Four-Vector Study Final Report

Created UTC: 2026-07-11

## Executive Result

The accepted completed run is the prior Vertex scalar-feature/XGBoost study from
`gs://asiop-zdc-1-zdc-reco-us-central1/runs/full-cpu-20260710-finalfix2/outputs`.
It used the same ROOT file now supplied locally; local SHA-256 matches the prior Vertex fingerprint:
`b7c666040e42352e158a9a3f78158d147cb2e056c6c88248d892c956f5c7b533`.

The champion is `M1_xgb_focus_only`, an XGBoost model trained on scalar detector features from ECAL
and HCAL calibrated hit signals, with on-shell neutron postprocessing.

## Data

- Local ROOT file:
  `C:\Users\Julia\OneDrive\Desktop\coding\ASIoP\ML ZDC all 1\myTree_20251117_765k_0to300GeV_neutron_All.root`
- Vertex/GCS data URI:
  `gs://asiop-zdc-1-zdc-reco-us-central1/data/myTree_20251117_765k_0to300GeV_neutron_All.root`
- Size: `25,022,001,408` bytes.
- CRC32C: `lCVUvQ==`.
- Latest tree: `myTree;865`, `764,940` entries.
- Primary neutron policy: exactly one MC particle per event and all are PDG `2112`.

## Hit Signal Contract

`ecal_energy` and `hcal_energy` are accepted as ideal simulated hit-energy deposits in GeV with
scale `1.0`. The evidence is in `outputs/reports/hit_unit_resolution.md` and
`outputs/preflight/hit_unit_evidence.json`.

## Split

The accepted run uses deterministic 80/10/10 split counts:

- Train: `612,825`
- Validation: `76,010`
- Test: `76,105`

Focus 50-250 GeV counts:

- Train: `408,276`
- Validation: `50,626`
- Test: `50,685`

Validation was reused for model selection, calibration, and empirical interval calibration. The
intervals are empirical; no independent split-conformal guarantee is claimed.

## Champion And Test Results

Champion: `M1_xgb_focus_only`.

Locked focus-test results for 50-250 GeV:

- Macro RMS relative four-vector error: `0.20443314430393622`
- Micro RMS relative four-vector error: `0.21863032113655304`
- Mean relative four-vector error: `0.12317056310240804`
- Energy MAE: `11.48034175891426 GeV`
- Energy relative RMSE: `0.1543518245985`
- Mean energy response: `1.0237600749127902`
- Mean energy bias: `+0.023760074912790228`
- Energy central-68 width: `0.07149108719165924`
- Angular median: `5.872449369417561 mrad`
- Angular 68%: `7.98112692599035 mrad`
- Angular 95%: `16.62022486411495 mrad`
- Max mass-shell residual: `3.2773117553119846e-11 GeV^2`

Empirical interval coverage on focus test:

- 68% interval: `0.6807734043602643`
- 90% interval: `0.9021209430798066`
- 95% interval: `0.9505573641116701`

## Expanded Diagnostics

Added diagnostic figures and tables are under:

- `outputs/plots/expanded_diagnostics/`
- `outputs/tables/expanded_diagnostics/`
- `outputs/reports/expanded_diagnostics/expanded_diagnostics_summary.md`

The added loss-curve figures include overall train/validation relative four-vector RMSE vs boosting
round, separate train/validation RMSE-vs-boosting plots for `E`, `px`, `py`, and `pz`, native
XGBoost head-loss curves, train-validation gap plots, and best-validation-round train-vs-validation
bars.

Best validation loss-curve points:

- Overall relative four-vector RMSE: `0.2143414040678046` at boosting round `735`.
- `E` RMSE: `20.408325706358482 GeV` at boosting round `980`.
- `px` RMSE: `5.177989169890205 GeV` at boosting round `2499`.
- `py` RMSE: `5.20788450849503 GeV` at boosting round `2499`.
- `pz` RMSE: `19.135673644391403 GeV` at boosting round `980`.

These loss curves come from the Vertex loss-curve job at
`gs://asiop-zdc-1-zdc-reco-us-central1/runs/loss-curves-20260711/outputs`; no local retraining was
performed for the boosting diagnostics.

## Previous Vertex Model Comparison

The accepted `finalfix2` run was compared against the previous successful Vertex outputs in project
`asiop-zdc-1`:

- `full-cpu-20260710`: first completed full CPU run; champion `B1_ridge_constrained`; XGBoost
  validation candidates numerically blew up.
- `full-cpu-20260710-finalfix`: previous successful/fixed run; champion `B1_ridge_constrained`.
- `full-cpu-20260710-finalfix2`: accepted run; champion `M1_xgb_focus_only`.

Compared with the previous `finalfix` champion, the accepted run improved:

- Macro RMS relative four-vector error: `0.3276764732159172` to `0.20443314430393622`
  (`37.61%` reduction).
- Energy MAE: `22.61899985919906 GeV` to `11.48034175891426 GeV` (`49.24%` reduction).
- Energy relative RMSE: `0.26065339433663753` to `0.1543518245985` (`40.78%` reduction).
- Angular median: `26.27980332575699 mrad` to `5.872449369417561 mrad` (`77.65%` reduction).
- Angular 95%: `87.82566429883639 mrad` to `16.62022486411495 mrad` (`81.08%` reduction).

Comparison plots and tables are in `outputs/plots/expanded_diagnostics/` and
`outputs/tables/expanded_diagnostics/`, especially files `31` through `36` and
`previous_vertex_*`.

## Vertex Provenance And Spend

The accepted finalization job completed on Vertex:

- Job output prefix:
  `gs://asiop-zdc-1-zdc-reco-us-central1/runs/full-cpu-20260710-finalfix2/outputs`
- Job state artifact: `outputs/reports/vertex_job_state_finalfix2.json`
- Started UTC: `2026-07-10T15:00:07.764231+00:00`
- Completed UTC: `2026-07-10T15:12:49.134797+00:00`
- Stages completed: artifact download, schema validation, baselines, XGBoost, selection,
  calibration, test unlock, test evaluation, plots, verify.

No new Vertex job was submitted after the 2026-07-11 continuation. The local ROOT file was already
staged in the `US-CENTRAL1` bucket, so no duplicate 23.3 GiB upload was performed.

## Limitations

- This accepted run is the scalar-feature/XGBoost Vertex study from the prior implementation, not a
  completed dual-grid T4 neural study.
- The newer one-shot asks for ECAL `[3,20,20]` and HCAL `[3,64,8]` tensors and a bounded T4 model.
  Those neural grid artifacts are not present in the accepted Vertex output.
- Results apply to the supplied simulation distribution and do not establish real-detector
  electronics calibration.

## Reproduction

With the imported legacy pipeline in this repo:

```bash
python -m zdc_reco.cli run-all-gcs --data-gcs gs://asiop-zdc-1-zdc-reco-us-central1/data/myTree_20251117_765k_0to300GeV_neutron_All.root --output-gcs gs://asiop-zdc-1-zdc-reco-us-central1/runs/rebuild-<DATE>/outputs --config configs/legacy_vertex_default.yaml --workdir /tmp/zdc_run
```

The staged ROOT object can later be removed with:

```bash
gcloud storage rm "gs://asiop-zdc-1-zdc-reco-us-central1/data/myTree_20251117_765k_0to300GeV_neutron_All.root"
```
