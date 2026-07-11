# QA Ledger

Created UTC: 2026-07-11. This ledger records technical evidence and actions only.

## Scope

Input data: `gs://asiop-zdc-1-zdc-reco-us-central1/data/myTree_20251117_765k_0to300GeV_neutron_All.root`.
Task: execute the single-neutron ZDC four-vector study under the repository protocol. Outcome:
blocked at Phase 1 because ECAL/HCAL hit-signal units and GeV conversion are not authoritatively
defined.

## Repository Intake

- Read every file in `/read me first/`: `AGENT_PROMPT.md`, `ATTACHMENT_AUDIT.md`,
  `EVALUATION_PROTOCOL.md`, `EXECUTION_PLAN.md`, `MASTER_QC_CHECKLIST.md`, `MODEL_DESIGN.md`,
  `QC_LEDGER_10_PASSES.md`, and `RESEARCH.md`.
- Read every file returned by `rg --files` in the repo, including source, tests, docs, config,
  Vertex templates, root prompt, manifest, Dockerfile, Makefile, and README.
- `git status --short --branch` failed because the directory was not a Git repository at intake.

## Commands Run

| Command | Exit | Evidence |
|---|---:|---|
| `python --version` | 0 | Local default was Python 3.13.1, not used for final verification. |
| bundled Python 3.12 `compileall -q src tests` | 0 | Compile passed before environment install. |
| bundled Python 3.12 `unittest discover -s tests -v` | 1 | Failed because `sklearn` was not installed. |
| bundled Python 3.12 `pytest -q` | 1 | Failed because `pytest` was not installed. |
| bundled Python 3.12 `ruff check .` | 1 | Failed because `ruff` was not installed. |
| bundled Python 3.12 `python -m zdc_hybrid.smoke` | 0 | Perfect macro score 0; mass-shell abs max `1.09e-11`. |
| `py -3.11 -m venv .venv` and `.venv pip install -e '.[dev]'` | 0 | Installed Python 3.11 environment and package. |
| `.venv python -m compileall -q src tests` | 0 | Passed. |
| `.venv python -m unittest discover -s tests -v` | 0 | 9 tests passed before CLI edits. |
| `.venv python -m pytest -q` | 0 | 9 tests passed before CLI edits. |
| `.venv ruff check .` | 1 | Failed on `UP037` in `src/zdc_hybrid/calibration.py`. |
| Source edit | n/a | Removed quoted self-type annotation in `calibration.py`. |
| `.venv ruff check .` | 0 | Passed after lint fix. |
| `gsutil ls -L <ROOT URI>` | 0 | Object exists, 25,022,001,408 bytes, CRC32C `lCVUvQ==`. |
| Uproot ROOT metadata open | 0 | Found `myTree;865`, `myTree;864`, ECAL/HCAL histograms, and branch names. |
| Truth-only full pass over `mcPar_*` | 0 | `truth_summary.json`; one PDG 2112 candidate per event; mass shell decisive. |
| Bucket/repo search for unit authority | 0 | No authoritative simulation code/docs found. |
| `python -m zdc_hybrid.cli preflight ...` | nonzero | Correct fail-closed behavior; wrote `BLOCKED.md`. |
| `docker --version` | 1 | Docker is not installed locally; Docker verification could not run. |
| `nvidia-smi` | 1 | No local NVIDIA utility; no local GPU evidence. |
| Presentation render and overflow QA | 0 | `slides_test.py` passed; `presentation_preview_montage.png` visually inspected. |
| Source tarball clean extract/test | 0 | Rebuilt after manifest refresh; extracted to temp; compile, unittest, pytest, Ruff, and smoke passed from the extracted source. |
| Final package zip build/list inspection | 0 | Built `ZDC_blocked_study_package_20260711.zip`; inspected entries and confirmed no ROOT data, venv, caches, models, or predictions. |

## Material Changes

- Added `src/zdc_hybrid/cli.py` with required command names and fail-closed preflight/verify/run-all
  behavior.
- Added `gcsfs` dependency and `zdc-reco` console entry point in `pyproject.toml`.
- Added CLI tests in `tests/test_core.py`.
- Fixed Ruff `UP037` in `src/zdc_hybrid/calibration.py`.
- Generated `environment.lock.txt` from the actual `.venv` environment.
- Generated evidence artifacts under `outputs/preflight` and `outputs/reports`.

## Phase 0 Audit

Phase 0 partially passed and then hit two local execution defects:

- Python environment, package install, compile, unittest, pytest, Ruff, and smoke now pass in `.venv`
  after the lint fix.
- Docker cannot be verified locally because Docker is not installed. This remains a reproducibility
  gap, but the current hard stop is earlier: unresolved hit units.
- The repo was not a Git repository at intake, so there was no starting commit/status to record.
- ROOT data were located in GCS and opened from the supplied URI. The ROOT file was not copied into
  the repository.

## Phase 1 Audit

Resolved:

- Latest tree and branches enumerated in `outputs/preflight/root_metadata.json`.
- Event count is 764,940 in `myTree;865`.
- Primary-neutron identity is unambiguous: exactly one MC particle per event and all are PDG 2112.
- Truth energy is total energy in GeV by mass-shell closure.

Failed hard gate:

- ECAL/HCAL hit-signal meaning and GeV conversion are unresolved. Existing names and prior inferred
  scales are not authoritative documentation or simulation code.

Action:

- Stopped before target building, splits, training, calibration, test unlock, plotting, or final
  performance claims.

## Master Checklist Status

| # | Status | Evidence |
|---:|---|---|
| 1 | PASS | Input, output, neutron, detector, focus range, data size, and budget are in docs and blocker. |
| 2 | PASS | Objective is energy response/angle compensation, not generic AI. |
| 3 | PASS | Prior numbers are labeled historical only. |
| 4 | PASS | Simulation-only boundary is explicit. |
| 5 | PASS | Attachment hashes are recorded in `docs/ATTACHMENT_AUDIT.md`. |
| 6 | PASS | Attachment audit accounts for supplied files/sheets/slides/source placeholders. |
| 7 | PASS | Current blocker claims trace to command artifacts. |
| 8 | PASS | No causal tail-driver claim is made. |
| 9 | PASS | Truth energy semantics resolved by mass-shell evidence. |
| 10 | PASS | Benchmark membership can use converted generator branch after blocker resolution. |
| 11 | NOT REACHED | No model target artifacts built. |
| 12 | NOT REACHED | No final predictions produced. |
| 13 | NOT REACHED | Grid mapping not fully locked because Phase 1 stopped earlier. |
| 14 | FAIL | Hit-signal units/conversion lack authoritative evidence. |
| 15 | PARTIAL | Data URI, size, CRC32C, prior SHA, and local evidence exist; no current full SHA recompute. |
| 16 | PASS | Single primary neutron verified for all 764,940 events. |
| 17 | NOT REACHED | No new split frozen under current repo. |
| 18 | NOT REACHED | Duplicate/fingerprint split gates not run under current repo. |
| 19 | NOT REACHED | Feature artifacts not built. |
| 20 | NOT REACHED | No preprocessing/calibration/test access occurred. |
| 21 | NOT REACHED | Baselines not trained under current protocol. |
| 22 | NOT REACHED | Historical log-target model not reproduced under current repo. |
| 23 | NOT REACHED | Raw/residual XGBoost not run. |
| 24 | PASS | Weighting helper tests pass. |
| 25 | NOT REACHED | Neural grids not built because hit-unit gate failed. |
| 26 | NOT REACHED | Neural model not trained. |
| 27 | PASS | Tangent-residual primitive tests pass. |
| 28 | NOT REACHED | Ensemble not evaluated. |
| 29 | NOT REACHED | GNN escalation not evaluated. |
| 30 | NOT REACHED | No champion selection. |
| 31 | PASS | Isotonic primitive tests pass, but no study calibrator fitted. |
| 32 | PASS | Physics primitive recomputes on-shell four-vector. |
| 33 | PASS | Validation reuse caveat is documented. |
| 34 | NOT REACHED | No locked test interval coverage. |
| 35 | PASS | Metric primitive tests cover fixed-bin macro score. |
| 36 | NOT REACHED | Companion metrics not produced under current run. |
| 37 | PASS | Docs prohibit narrow-bin R2 as decision metric. |
| 38 | PASS | Inclusive final-bin test passes. |
| 39 | NOT REACHED | No model comparison bootstrap. |
| 40 | NOT REACHED | Slice materiality not used because no training. |
| 41 | PASS | Historical comparison is not called paired. |
| 42 | NOT REACHED | No candidate models stored. |
| 43 | NOT REACHED | No early stopping histories generated. |
| 44 | NOT REACHED | Feature/grid parity not run. |
| 45 | NOT REACHED | Production artifacts not built. |
| 46 | PARTIAL | Unit/lint/smoke pass; Docker unavailable; integration/tiny ROOT absent. |
| 47 | PARTIAL | New source is not placeholder training, but generated package metadata exists locally. |
| 48 | NOT REACHED | No new Vertex submission; price lookup not needed before blocked Phase 1. |
| 49 | PASS | Actual new Vertex spend is $0. |
| 50 | NOT REACHED | No new Vertex job submitted. |
| 51 | PASS | No new endpoint or persistent resource created. |
| 52 | PASS | No budget alert was treated as a hard cap. |
| 53 | FAIL | No locked 50-250 test performance exists. |
| 54 | NOT REACHED | No final plots generated from current predictions. |
| 55 | PASS | Blocker presentation rendered and `slides_test.py` reported no overflow. |
| 56 | PASS | Limitations and reproduction command are visible in blocker. |
| 57 | PASS | Source tarball clean extract/test passed; final zip contents inspected. |
| 58 | PASS | The one-shot prompt is standalone and fail-closed. |

## Stop Decision

Proceeding to feature production or model training would require guessing hit-signal units. That would
violate the prompt and produce unreliable absolute energy reconstruction. The correct action is to
stop, package the evidence, and request the smallest missing authority.
