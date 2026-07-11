# ZDC hybrid neutron four-vector reconstruction v3

This is a research-backed, QA-gated implementation scaffold for reconstructing one on-shell neutron
four-vector `(E_total, px, py, pz)` from the supplied ZDC ECAL/HCAL response. The only headline
domain is **50–250 GeV**. The full 0–300 GeV sample is retained only for training-support ablations
and boundary diagnostics.

## Recommended model in one paragraph

Run a strong corrected XGBoost baseline and a compact dual-grid neural model. The neural model reads
the detector in its native fixed geometry—three channels over the 20×20 ECAL grid and three channels
over the 64×8 HCAL depth/slice grid—plus a small, nonredundant scalar branch. Energy is trained in
raw kinetic-energy space with joint energy×angle balancing and an explicit bin-linearity penalty;
direction is a two-parameter residual around a truth-free analytic shower axis. The output is mapped
to the neutron mass shell. After the champion is frozen, one global monotone isotonic energy
calibrator is fitted on validation. A discrete convex blend is allowed only if it improves the fixed
validation score by at least 2% without a material slice regression. A GNN is escalation-only.

## Why this replaces the supplied result

The supplied test result is useful but shows a strong response slope: approximately +15.8% mean bias
in 50–75 GeV and −5.9% in 225–250 GeV, with much worse four-vector error in the highest-angle
quartile. The model's direction is already comparatively strong. The redesign therefore targets
energy linearity and angle-dependent compensation rather than spending most compute on a new
direction estimator.

The attached analysis bundle is not reproducible by itself: it contains plots, a deck, and tables,
but no training code, predictions, split manifest, model artifacts, data hashes, or feature builder.
This repository defines the missing reproducibility and acceptance contract. It does not fabricate a
new score without the user's event data.

## Fixed protocol

- Deterministic, group-safe **80/10/10 train/validation/test** split.
- Validation is intentionally reused for early stopping, selection, final point calibration, and
  empirical uncertainty calibration. The untouched test evaluates the complete frozen pipeline.
- This reuse is acceptable for honest test performance, but the resulting uncertainty intervals are
  **empirical**, not an independently calibrated split-conformal guarantee.
- Test is opened once, after champion, calibrator, code, configuration, data, and split hashes exist.
- Planned Vertex spend is at most **$78**, leaving **$12** unused under the user's absolute $90 cap.

## Read order

1. `docs/ATTACHMENT_AUDIT.md`
2. `docs/MODEL_DESIGN.md`
3. `docs/EXECUTION_PLAN.md`
4. `docs/EVALUATION_PROTOCOL.md`
5. `docs/MASTER_QC_CHECKLIST.md`
6. `docs/QC_LEDGER_10_PASSES.md`
7. `AGENT_PROMPT.md`

## Scaffold verification

With NumPy and scikit-learn available:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m zdc_hybrid.smoke
```

The coding agent must extend this scaffold into the actual ROOT-specific production pipeline, execute
it against the data, and leave every artifact listed in `docs/EXECUTION_PLAN.md`. Placeholder Vertex
values are deliberately fail-closed; current regional availability and price must be recorded before
submission.
