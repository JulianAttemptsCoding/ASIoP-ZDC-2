# QA Ledger Continuation

Created UTC: 2026-07-11

## User Continuation

The user stated that the ECAL/HCAL interpretation should be resolved from normal ZDC branch/spec
logic and directed inspection of:

`C:\Users\Julia\OneDrive\Desktop\coding\ASIoP\ML ZDC all`

## Actions

- Read the prior implementation config, data-contract docs, ROOT I/O, feature builder, geometry
  code, pipeline code, CLI, and completed Vertex artifacts.
- Located prior hit-unit evidence at
  `C:\Users\Julia\OneDrive\Desktop\coding\ASIoP\ML ZDC all\outputs\preflight\hit_unit_evidence.json`.
- Accepted `ecal_energy` and `hcal_energy` as GeV hit/deposit signals with scale `1.0`.
- Preserved the earlier blocker as
  `outputs/reports/BLOCKED_SUPERSEDED_BY_HIT_UNIT_EVIDENCE.md`.
- Imported the prior executable scalar/XGBoost pipeline under `src/zdc_reco`.
- Added `zdc-reco-legacy = "zdc_reco.cli:main"` to `pyproject.toml`.
- Copied compact accepted Vertex result artifacts into `outputs/metrics`, `outputs/predictions`,
  `outputs/plots`, `outputs/preflight`, and `outputs/reports`.

## Accepted Vertex Run

- Source GCS output:
  `gs://asiop-zdc-1-zdc-reco-us-central1/runs/full-cpu-20260710-finalfix2/outputs`
- Champion: `M1_xgb_focus_only`
- Split counts: train `612,825`, validation `76,010`, test `76,105`
- Focus counts: train `408,276`, validation `50,626`, test `50,685`
- Test macro RMS relative four-vector error: `0.20443314430393622`
- Test energy MAE: `11.48034175891426 GeV`
- Test angular median: `5.872449369417561 mrad`

## Current Remaining Caveat

The accepted run completes the prior scalar-feature/XGBoost study. It does not complete the newer
dual-grid T4 neural path requested by the stricter one-shot prompt.

## Final Local QA

Passed after importing the accepted scalar/XGBoost path and rebuilding the final package:

- `.venv\Scripts\python.exe -m compileall -q src tests legacy_tests`
- `.venv\Scripts\python.exe -m unittest discover -s tests -v`
- `.venv\Scripts\python.exe -m unittest discover -s legacy_tests -v`
- `.venv\Scripts\python.exe -m pytest -q`
- `.venv\Scripts\python.exe -m pytest legacy_tests -q`
- `.venv\Scripts\ruff.exe check .`
- `.venv\Scripts\python.exe -m zdc_hybrid.smoke`
- `.venv\Scripts\python.exe -m zdc_reco.cli synthetic-smoke`
- `.venv\Scripts\python.exe -m zdc_reco.cli validate-config --config configs/legacy_vertex_default.yaml`
- `.venv\Scripts\python.exe -m zdc_hybrid.cli verify --output-dir outputs`
- `zdc-reco-legacy --help`
- Clean extraction of `zdc_hybrid_source_accepted_xgb_20260711.tar.gz`, followed by compile, strict
  unit tests, legacy unit tests, pytest, Ruff, and both smoke tests from the extracted source.
- Final zip inspection confirmed no ROOT data, virtualenv, caches, egg-info metadata, model binaries,
  stale blocked zip/source tar/deck artifacts, or Python bytecode.

One attempted command,
`.venv\Scripts\python.exe -m zdc_hybrid.cli validate-config --config configs/study.yaml`, returned
an argparse error because the strict `zdc_hybrid` CLI does not expose a `validate-config`
subcommand. The matching strict verifier and the legacy config validator both passed.
