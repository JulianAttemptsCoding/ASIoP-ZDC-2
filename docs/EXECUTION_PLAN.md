# Reproducible execution plan

## Phase 0 — repository and data preflight

Read every tracked file; create a clean environment; run unit/smoke tests; record OS, CPU, RAM,
Python/packages, CUDA/driver/T4, git state, and configuration hash. Record each ROOT file's byte size
and SHA-256. The input data never enter the source archive.

Inspect beginning/middle/end chunks and report every tree/branch/type, event count, jagged alignment,
truth multiplicity/status/parent information, signal units and abnormal values, coordinate centers,
segmentation IDs, detector extents, generator support, duplicate rates, and group identifiers.
Resolve total-versus-kinetic energy and GeV-versus-MeV using the neutron mass shell. Fail closed on
ambiguity or unknown hit-signal meaning.

## Phase 1 — production artifacts

Build chunked, resumable, hash-addressed Parquet/Zarr artifacts:

```text
outputs/preflight/schema.lock.yaml
outputs/preflight/data_fingerprint.json
outputs/data/event_index.parquet
outputs/data/targets.parquet
outputs/data/splits.parquet
outputs/data/scalars/<partition>.parquet
outputs/data/ecal_grid/<partition>
outputs/data/hcal_grid/<partition>
outputs/reports/grid_mapping_report.json
outputs/reports/feature_manifest.csv
```

Truth/targets stay separate from inference inputs. Compare the optimized builder with a scalar
reference on at least 1,000 random events. Benchmark 50,000 events before full production. Every
stage uses atomic writes, row counts, schemas, checksums, and resume invalidation based on upstream
hashes.

## Phase 2 — split and leakage gates

Freeze group-safe 80/10/10. Verify UID uniqueness, group exclusivity, duplicate/near-duplicate
fingerprint exclusivity, deterministic reproduction, order independence, and energy×angle balance.
Unit tests must prove no training, selection, or calibration command can read test rows.

## Phase 3 — baselines and corrected tree family

Train `B0`, `B1`, and the three `T1` energy variants for each of focus-only, guard-band, and
full-support training. Preserve all validation predictions and learning histories. Use no more than
10 bounded XGBoost trials after one fixed configuration beats baselines. Compute per-head early
stopping with a nonzero minimum improvement tolerance.

## Phase 4 — dual-grid network

Only after grid parity and a small CPU batch overfit test pass, run one T4 smoke job, then at most four
bounded trials. Use one worker, mixed precision, deterministic seeds, gradient/numerical checks,
checkpointing, and explicit timeout. Reject any run that cannot overfit a tiny subset, produces
quantile crossing, or diverges across two confirmation seeds.

## Phase 5 — selection, blend, and calibration

Rank all uncalibrated candidates with the locked validation protocol. Evaluate only the five allowed
blend weights. Freeze champion, fit the one global isotonic calibrator, compare identity versus
calibrated output under the same gates, and create empirical interval calibrations. Write the full
selection decision before test access.

## Phase 6 — one-time test and reporting

Open test once. Produce fixed tables, bootstraps, predictions, plots, uncertainty coverage, and
failure-population reports. Compare against the historical supplied result, clearly labeled as a
different prior run rather than a paired evaluation unless event IDs/predictions permit pairing.

## Required final artifacts

```text
outputs/models/<candidate_id>/*
outputs/predictions/validation_<candidate_id>.parquet
outputs/predictions/test_<champion_id>.parquet
outputs/metrics/validation_leaderboard.csv
outputs/metrics/test_focus_summary.json
outputs/metrics/test_slices.parquet
outputs/metrics/empirical_coverage.parquet
outputs/reports/cost_ledger.csv
outputs/reports/trial_ledger.csv
outputs/reports/selection_decision.md
outputs/reports/test_unlock.json
outputs/reports/final_report.md
outputs/reports/model_card.md
outputs/reports/qa_ledger.md
outputs/plots/*.png
environment.lock.txt
```

## Vertex budget

The user’s absolute maximum is $90. The operational planned maximum is $78, leaving $12 reserve.
Retrieve current official regional prices and T4 availability immediately before submission; never
hard-code an old hourly rate. The cost ledger must include machine, accelerator, disk, maximum wall
time, replicas, maximum committed cost, actual cost/status, and cumulative total.

Suggested allocation ceilings, adjusted downward after current prices are known:

- CPU preflight/feature build/baselines: $18.
- XGBoost bounded study: $12.
- T4 smoke and dual-grid trials: $36.
- Confirmation, final inference, and reports: $12.

Every job has one replica, one concurrent trial, an explicit timeout, billing labels, and resumable
outputs. Do not deploy an endpoint or leave a persistent resource. Stop optional work at $78 committed
or actual spend; budget alerts alone are not hard caps.
