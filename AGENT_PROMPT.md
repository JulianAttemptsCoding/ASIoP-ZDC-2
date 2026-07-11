# One-shot coding-agent prompt

You own this repository and must complete, execute, verify, and package the actual single-neutron ZDC
four-vector study end to end. Do not stop at a plan or code skeleton. Do not leave TODOs, executable
placeholders, mock data, fabricated metrics, or commands you did not run. Continue through data
preflight, production features/grids, frozen splits, baselines, model comparisons, bounded Vertex
training, champion freeze, validation calibration, one-time test evaluation, reports, plots, QA, and
clean packaging unless a hard scientific ambiguity makes a valid result impossible.

When blocked by missing authority or an irreducible data-contract ambiguity, stop safely and produce
`outputs/reports/BLOCKED.md` containing the exact failing check, counts/examples that are safe to
share, commands/logs, and the smallest user decision needed. Never guess past an ambiguity.

## Fixed context

- Approximately 765,000 simulated single-neutron events spanning generator energy 0–300 GeV.
- Only 50–250 GeV performance matters for selection and headline results.
- Detector supplied by the user:
  - ECAL: LYSO + SiPM, 20×20 cells, 3×3×7 cm, 60×60 cm face, 6.5 X0.
  - HCAL: steel/scintillator + SiPM, 64 sampling layers × 8 slices, 65×60×163 cm.
- Required output per event: finite on-shell `(E_total_hat, px_hat, py_hat, pz_hat)` in GeV.
- Split: group-safe 80% train, 10% validation, 10% locked test.
- Validation is deliberately reused for early stopping, model/HPO selection, final point calibration,
  and empirical interval calibration. The test fold remains untouched until the complete pipeline is
  frozen. Do not claim an independent split-conformal guarantee.
- Vertex AI: CPUs and one NVIDIA T4 are available. Absolute credit cap is $90. Planned/committed work
  must stay at or below $78, leaving $12 reserve.

The binding sources of truth are, in order:

1. `docs/EVALUATION_PROTOCOL.md`
2. `configs/study.yaml`
3. `docs/MODEL_DESIGN.md`
4. `docs/EXECUTION_PLAN.md`
5. `docs/MASTER_QC_CHECKLIST.md`
6. this prompt

If implementation reality requires a change, make it only before test access, cite evidence, update
all affected documents/config/tests, and record the decision in the QA ledger.

## Continuous QA/QC operating rule

Create `outputs/reports/qa_ledger.md` before any data processing. After every phase and every material
change:

1. rerun all relevant unit/integration/invariant tests;
2. audit the entire pipeline against every item in `docs/MASTER_QC_CHECKLIST.md`, not only the changed
   module;
3. record exact command, exit status, artifact paths/hashes, failure, fix, and rerun evidence;
4. compare code, config, docs, stored metadata, plots, and reported numbers for semantic agreement;
5. refuse to proceed when a hard gate fails.

A checkbox without evidence is a failure. Do not expose private chain-of-thought; record concise
technical judgments, evidence, and actions.

## Phase 0 — understand and validate the repository

Read every tracked file. Create Python 3.11/3.12 environment, install the package, and run:

```bash
python -m compileall -q src tests
python -m unittest discover -s tests -v
python -m pytest -q
ruff check .
PYTHONPATH=src python -m zdc_hybrid.smoke
```

Add missing production modules and a single documented CLI. Required command capabilities:

```text
preflight, validate-schema, build-targets, make-splits, build-scalars, build-grids,
train-baselines, train-xgb, train-dual-grid, evaluate-validation, select-champion,
fit-calibration, freeze-study, unlock-test, evaluate-test, plot, verify, run-all
```

Record Python/packages, OS, CPU/RAM, CUDA/driver/T4 when present, git commit/status, config hash, and
container digest. Generate an exact environment lock from the working environment. Docker must build
and run the tests.

Locate actual ROOT files from the provided path or `rg --files -g '*.root'`. Record absolute logical
input URI, byte size, SHA-256, and source grouping. Do not copy ROOT data into the repo/archive.

Then perform a complete Master Checklist audit and close every Phase 0 finding before Phase 1.

## Phase 1 — inspect and lock the data contract

Inspect deterministic beginning/middle/end and random chunks, then the full-file metadata/counts.
Report:

- all trees/RNTuples, branches, types/forms, entries, file hashes;
- per-event jagged alignment and ECAL/HCAL hit-count distributions;
- truth PDG multiplicity, status/parent candidates, energy/momentum ranges;
- candidate total/kinetic × GeV/MeV mass-shell residual table;
- generator energy support and exact 50/250 boundary counts;
- hit signal finite/negative/zero/saturation-like statistics and authoritative unit evidence;
- coordinate unique-center/clustering, IDs, extents, ECAL-before-HCAL, and local transform;
- source run/seed/file/batch/event identifiers and independence evidence;
- deterministic exact and tolerance-based duplicate detector fingerprints.

Never assume the branch named energy is total energy or in GeV. Resolve energy/momentum semantics
against the neutron shell and require a decisive winner. The converted raw generator branch defines
benchmark membership; canonical truth total energy comes from converted momentum and neutron mass.

Select a primary neutron only through an explicit verified rule. “First neutron” is forbidden. If an
event may contain multiple candidates and status/parent metadata do not identify the intended primary,
stop.

Resolve ECAL/HCAL hit-signal meaning and GeV conversion from authoritative simulation metadata/code or
data documentation, not from whichever scale gives better ML results. If unresolved, stop because
absolute energy reconstruction is undefined.

Prove the cell mapping:

- exactly 20×20 ECAL cells;
- exactly 64 HCAL layers × 8 slices;
- deterministic mapping from IDs or reconciled coordinate centers;
- quantified underflow/overflow/unmapped/duplicate-ID rates;
- truth-free right-handed detector frame and nominal extent agreement.

Write a non-null `schema.lock.yaml` and an independent validator. Do not infer physical layer edges
from shower-occupancy quantiles.

Perform and record a full Master Checklist audit. No unresolved schema item may continue.

## Phase 2 — implement reproducible data artifacts

Use chunked Uproot/Awkward. Never load all jagged hits at once. Build targets and inference inputs into
separate hash-addressed artifacts. Use atomic writes, partition manifests, schemas, row counts, and
checksums. Reuse valid outputs on rerun and invalidate every downstream artifact when data, code,
config, schema, split, or upstream hash changes.

Create:

- deterministic event UID and independent group UID;
- target table with generator axis, total/kinetic energy, momentum, unit direction, theta/phi, validity;
- scalar allowlist with exact source provenance graph;
- ECAL `[3,20,20]` and HCAL `[3,64,8]` tensors using summed signal, train-scaled log signal, and
  occupancy channels;
- flags/counters for empty, degenerate, clipped, unmapped, negative, saturated, and fallback cases.

All scaling/bin edges/statistics used as inputs are fitted on train only after the split. Raw grid
aggregation itself may be deterministic pre-split. Remove algebraic duplicate scalar features unless
a prespecified ablation justifies them. Never train by “all columns except truth.”

Keep no-signal and degenerate events. Negative signals require an explicit noise policy and cannot be
silently clipped. Robustly clip unstable extrapolation features to geometry-derived bounds and retain
validity flags.

Implement a readable scalar/grid reference builder and a production builder. Require numeric parity
on at least 1,000 randomly selected events and benchmark 50,000 before processing all 765k.

Perform and record a full Master Checklist audit.

## Phase 3 — freeze leakage-safe 80/10/10

Use deterministic randomized group-safe stratification over generator energy, true theta, and true
phi only for split balancing. Assign eight of ten folds to train, one to validation, one to test.
Freeze the manifest before any candidate comparison.

Hard tests:

- unique event IDs and exactly one split per row;
- no group, exact fingerprint, or near-duplicate fingerprint crosses splits;
- counts/fractions/focus/shoulder and energy×angle strata are acceptable;
- split is deterministic and independent of row order;
- transforms/models see train statistics only;
- commands before `unlock-test` cannot load test rows;
- validation/calibration commands are proven unable to read test rows.

Write a split report and hash. Perform and record a full Master Checklist audit.

## Phase 4 — baselines and corrected XGBoost family

Train and preserve:

1. `B0`: train-fitted nonnegative ECAL+HCAL calibrated sum and analytic line/PCA direction.
2. `B1`: regularized linear scalar model with train-only preprocessing.
3. `T1-log`: reproduce historical `log1p(K)` XGBoost as closely as the available provenance allows.
4. `T1-raw`: raw nonnegative kinetic energy with Pseudo-Huber objective.
5. `T1-residual`: predict `K−K0`, where `K0` is the train-fitted B0 energy.

For `T1` direction, predict two tangent-plane residuals around the truth-free analytic axis. Compare
against the three-component direction model as an ablation. Normalize direction and construct the
on-shell four-vector.

For every energy variant, test three training supports:

- focus-only 50–250;
- guard band 35–265 with outside-focus multiplier 0.20;
- full 0–300 with shoulder multiplier 0.10.

Use joint energy×theta bin balancing with a maximum weight ratio of 10. Compare total-signal monotonic
constraints against unconstrained trees; preserve both results. Rank on focus validation only.

First run fixed configurations. Only if one beats B0/B1 may you run at most 10 bounded sequential
XGBoost trials. Each head has its own early stopping, nonzero minimum delta, history, best iteration,
and confirmation seed. Do not cite round 2499 as meaningful when the improvement is numerical noise.

Save candidate configuration, hashes, data rows, weight distribution, runtime/memory/hardware, model,
validation predictions, and all metrics. Perform and record a full Master Checklist audit.

## Phase 5 — compact dual-grid network on one T4

Proceed only if Phase 1 proves lossless grid mapping and Phase 2 parity passes.

Implement `N1` exactly as bounded in `docs/MODEL_DESIGN.md`: separate ECAL and anisotropic HCAL
residual encoders, scalar branch, fused heads, fewer than 1.5M parameters, nonnegative raw-K output,
ordered q16/q50/q84 representation, and two tangent direction residuals. Use the configured composite
loss and joint energy×theta weighting. Use deterministic stratified batches that contain all eight
focus energy bins and broad theta coverage so the macro-bin bias term is well-defined; test and log
batch composition. The point-energy head is the primary prediction for RMS-based selection; quantile
heads are auxiliary uncertainty outputs and must not silently replace it.

Before Vertex:

- shape/mask/gradient/finiteness unit tests;
- equivariance/invariance tests only where physically valid—do not invent symmetries;
- tiny-batch and tiny-subset overfit test;
- CPU one-epoch smoke and checkpoint/resume equivalence;
- deterministic seed behavior within documented accelerator tolerance.

Before cloud submission, retrieve current official regional prices and T4 availability. Fill the cost
ledger and templates; placeholder values may never be submitted. Use one replica, one T4, one trial at
a time, mixed precision, checkpoints, explicit timeout, billing labels, and resumable GCS output.

Run one T4 smoke, then at most four bounded trials. Abort optional trials at $78 committed/actual
spend. Do not deploy an endpoint or create an idle persistent resource. Run a second confirmation seed
for a prospective neural champion.

Perform and record a full Master Checklist audit after every neural trial, not only after Phase 5.

## Phase 6 — validation selection, optional blend, and calibration

Evaluate all uncalibrated candidates on validation focus using the locked primary metric and complete
slices. Use paired group bootstrap with common resamples. Freeze numerical slice-regression
materiality before looking at candidate rankings.

Evaluate exactly five convex energy blend weights between the best `T1` and `N1`:
`0, 0.25, 0.5, 0.75, 1`. Blend direction only if a separately prespecified normalized-vector blend
beats both parents; otherwise use the better direction parent. A neural model or blend must improve
the simpler parent by at least 2% relative and pass every slice gate to justify complexity.

Write `selection_decision.md` with all candidates/trials/failures, primary/companion metrics,
bootstrap intervals, support decision, residual-complementarity evidence, selected champion, and all
hashes. State tuning is closed.

Then fit exactly one energy-balanced global isotonic point calibrator on validation focus using only
the champion's uncalibrated predicted energy as input. Compare identity versus calibration under the
same fixed metrics. Reject calibration if it worsens the primary/slices or clips more than 0.5% of
focus predictions. Recompute kinetic energy/momentum after calibration.

Fit empirical 68/90/95% residual intervals/cones from validation and label them empirical. Measure
width as well as coverage later. No ordinary independent split-conformal claim is allowed.

Write complete freeze hashes. Perform and record a full Master Checklist audit. Test must still be
unread.

## Phase 7 — one-time locked test

Create `test_unlock.json` containing timestamp; exact focus query/bin ownership; data/split/code/config/
environment/feature/model/calibrator/selection hashes; ledger hashes; and a statement that no more
tuning is allowed. Make the unlock single-use and auditable.

Read the focus test once and evaluate the complete frozen pipeline. Also compute shoulders separately
as diagnostics. Do not alter the model, blend, calibration, thresholds, slices, plot choices, or metric
definitions after seeing test.

If a genuine software bug appears after unlock, record protocol contamination and create a clearly
named follow-up study. Do not silently rerun and call it untouched test.

Perform and record a full Master Checklist audit.

## Phase 8 — reports, plots, and source-grounded interpretation

The final report leads with exact 50–250 test counts and:

- primary macro and secondary micro relative four-vector RMS with group-bootstrap intervals;
- response mean/median, bias, RMSE, central-68 width, MAE, p95/p99 by fixed energy bins;
- angle median/68/95 by energy and theta;
- component metrics and on-shell invariant checks;
- no-signal/degenerate/fallback fractions;
- full prespecified slice and tail analysis;
- empirical interval/cone coverage and width globally and by energy×theta;
- baseline/tree/neural/blend validation comparison and training-support ablation;
- exact total cloud spend and resource use;
- simulation-only limitations and known failures.

Repeat tail-driver correlations within energy×theta cells or with a documented partial model and
bootstrap uncertainty. Do not use causal wording for marginal correlations. Do not use narrow-bin R²
as a decision metric. Historical supplied results may be contextual, not paired, unless common event
IDs and predictions permit an actual paired comparison.

All plots are regenerated from saved prediction tables, include units/counts/uncertainty/readable
fonts, and use consistent residual definitions and honest axes. Render every final document/deck page
and visually inspect for clipping, overlap, wrapping, unreadable tables, and missing citations.

Perform and record a full Master Checklist audit.

## Phase 9 — final verification and ten fresh-mind QC passes

Run all formatting, lint, unit, integration, tiny ROOT, feature/grid parity, Docker, clean-environment,
resume/hash invalidation, test-lock, CPU/GPU parity/tolerance, and end-to-end smoke tests. Search tracked
files for TODO/FIXME/placeholder executable paths, fake results, secrets, credentials, absolute
personal paths, caches, data, models, and truth-feature/proxy leakage.

Then perform at least 10 complete independent fresh-mind passes over the entire final work using the
exact structure below. Each pass must restart at Master Checklist item 1 and cover all 58 items; do
not split the checklist across passes.

```text
## QC Pass #X of 10+
1. Fresh-Mind Baseline Assessment
2. Benchmark Comparison (specific primary/official sources)
3. Master Checklist Line-by-Line Audit (every item; pass/fail/evidence)
4. Actioned Revisions (exact changes and rerun evidence)
```

Continue beyond 10 if any item remains fixable. Conditional items that require unavailable authority
must be explicit blockers, not false passes. Re-run the entire verification suite after every pass
that changes code/config/artifacts.

## Final packaging and response

Create a source-only tarball with repository manifest and SHA-256. Exclude ROOT data, generated models,
large predictions, credentials, caches, local environments, and cloud secrets. Extract the tarball to
a clean temporary directory, install it, run tests/smoke, inspect the file list, and record evidence.

Your final response must state only what actually ran and include:

- concise champion architecture and why it won;
- locked 50–250 test results and uncertainty/slice caveats;
- 80/10/10 counts and validation-reuse statement;
- actual Vertex spend versus $78/$90;
- limitations/blockers;
- exact paths and SHA-256 hashes for source tarball, final report, model card, selection decision,
  environment lock, predictions/metrics manifests, and QA ledger;
- exact one-command reproduction entry point.

Do not claim completion while any applicable Master Checklist item fails.
