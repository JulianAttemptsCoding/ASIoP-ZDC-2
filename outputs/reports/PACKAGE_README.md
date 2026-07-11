# ZDC Study Package

Created: 2026-07-11

## Status

This package documents the accepted scalar-feature/XGBoost ZDC single-neutron four-vector result and
the QA path that resolved the ECAL/HCAL hit-signal gate using the user's continuation plus the prior
`ML ZDC all` implementation evidence.

## Most Important Files

- `outputs/reports/final_report.md`: self-contained result, provenance, metrics, limitations, and
  reproduction command.
- `outputs/reports/model_card.md`: champion model card for `M1_xgb_focus_only`.
- `outputs/reports/hit_unit_resolution.md`: ECAL/HCAL hit-signal scale decision and evidence.
- `outputs/reports/qa_ledger.md` and `outputs/reports/qa_ledger_continuation_20260711.md`: original
  audit plus continuation evidence.
- `outputs/reports/selection_decision.md`: validation selection decision from the accepted Vertex run.
- `outputs/metrics/test_focus_summary.json`: locked focus-test summary.
- `outputs/metrics/validation_leaderboard.csv`: validation candidate comparison.
- `outputs/predictions/test_M1_xgb_focus_only.parquet`: accepted champion focus-test prediction
  artifact copied from the prior Vertex output set.
- `outputs/plots/expanded_diagnostics/`: expanded study plot suite, including train/validation loss
  vs boosting, separate `E`, `px`, `py`, and `pz` loss curves, native head losses, component
  metrics, feature importance, angular error, response density, and energy-slice diagnostics.
- `outputs/tables/expanded_diagnostics/`: CSV/JSON source tables behind the expanded plots.
- `outputs/reports/expanded_diagnostics/expanded_diagnostics_summary.md`: index and notes for the
  expanded diagnostics.
- `outputs/reports/expanded_diagnostics/previous_vertex_comparison_summary.md`: comparison to prior
  successful Vertex jobs in project `asiop-zdc-1`.
- `outputs/reports/previous_vertex_jobs/`: copied small metric, leaderboard, selection, and job-state
  artifacts from the previous Vertex output prefixes.
- `outputs/reports/expanded_diagnostics_montage.png`: visual QA montage of all 36 expanded plots.
- `outputs/ZDC_Accepted_XGB_Result_Presentation.pptx`: self-standing presentation for colleagues.
- `zdc_hybrid_source_accepted_xgb_20260711.tar.gz`: source tarball for the final accepted-result
  repository state.
- `outputs/reports/vertex_data_staging.json`: proof that the local ROOT file matches the staged
  `US-CENTRAL1` object used by Vertex.

## Rebuild Command

```bash
python -m zdc_reco.cli run-all-gcs --data-gcs gs://asiop-zdc-1-zdc-reco-us-central1/data/myTree_20251117_765k_0to300GeV_neutron_All.root --output-gcs gs://asiop-zdc-1-zdc-reco-us-central1/runs/rebuild-<DATE>/outputs --config configs/legacy_vertex_default.yaml --workdir /tmp/zdc_run
```

## Delete Staged Data Later

```bash
gcloud storage rm "gs://asiop-zdc-1-zdc-reco-us-central1/data/myTree_20251117_765k_0to300GeV_neutron_All.root"
```

## What Is Still Not Claimed

The accepted run is not the newer dual-grid T4 neural study. It is the completed scalar-feature
XGBoost study from the prior implementation, now explicitly imported and documented in this repo.

## Expanded Diagnostics Provenance

The added loss-curve diagnostics come from the Vertex loss-curve job recorded in
`outputs/reports/expanded_diagnostics/diagnostics_manifest.json`, with source artifacts from
`gs://asiop-zdc-1-zdc-reco-us-central1/runs/full-cpu-20260710-finalfix2/outputs` and output prefix
`gs://asiop-zdc-1-zdc-reco-us-central1/runs/loss-curves-20260711/outputs`. No local retraining was
performed to create those boosting curves.

The previous-model comparison uses saved artifacts from these Vertex output prefixes:

- `gs://asiop-zdc-1-zdc-reco-us-central1/runs/full-cpu-20260710/outputs`
- `gs://asiop-zdc-1-zdc-reco-us-central1/runs/full-cpu-20260710-finalfix/outputs`
- `gs://asiop-zdc-1-zdc-reco-us-central1/runs/full-cpu-20260710-finalfix2/outputs`
