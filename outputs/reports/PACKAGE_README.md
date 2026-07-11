# ZDC Blocked Study Package

Created: 2026-07-11

## Status

This package documents a fail-closed run of the requested ZDC single-neutron four-vector study. It is
not a completed training/evaluation result. The study stopped at the Phase 1 data-contract gate
because ECAL/HCAL hit-signal units and conversion to GeV were not found in authoritative simulation
metadata, simulation code, or data documentation.

## Most important files

- `outputs/reports/BLOCKED.md`: exact stop reason, resolved facts, failing check, and smallest user
  decision needed.
- `outputs/reports/qa_ledger.md`: commands run, tests, checklist status, and audit trail.
- `outputs/reports/analysis_summary.md`: compact narrative summary.
- `outputs/ZDC_Blocked_Rebuild_Presentation.pptx`: self-standing presentation for colleagues.
- `zdc_hybrid_source_blocked_20260711.tar.gz`: source-only tarball. It excludes ROOT data, local
  environments, caches, models, predictions, and credentials.
- `environment.lock.txt`: exact Python package lock from the working `.venv`.
- `outputs/preflight/root_metadata.json`: ROOT metadata from the supplied GCS object.
- `outputs/reports/truth_summary.json`: truth-branch full pass showing one neutron per event and
  total-energy GeV semantics.
- `outputs/reports/hit_sample_summary.json`: deterministic sample-window hit checks.
- `outputs/reports/artifact_hashes.sha256`: SHA-256 hashes for key artifacts.

## Rebuild command after the missing authority is supplied

```bash
zdc-reco run-all --config configs/study.yaml --data gs://asiop-zdc-1-zdc-reco-us-central1/data/myTree_20251117_765k_0to300GeV_neutron_All.root
```

Without authoritative hit-unit evidence, the command correctly fails closed and writes
`outputs/reports/BLOCKED.md`.

## What was not run

No production feature build, new split freeze, baseline training, XGBoost training, dual-grid T4
training, champion selection, calibration, test unlock, or final test metric was run under this
current repository state. New Vertex spend after blocker detection was `$0`.
