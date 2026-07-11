# Locked evaluation and calibration protocol

## Split

Freeze one deterministic group-safe 80/10/10 split before feature/model experiments. If simulation
seed, batch, source file, or shower-parent identifiers exist, they define groups. Event-level random
splitting is allowed only after a written independence demonstration. Exact and tolerance-based
detector fingerprints cannot cross splits.

Validation has four declared roles: early stopping, model/HPO selection, final point calibration,
and empirical interval calibration. Test has one role: final evaluation of the complete frozen
pipeline. This is a valid predictive-performance design, but it is not independent calibration for a
formal split-conformal guarantee.

## Population and bins

Headline population: converted raw generator energy `50 ≤ E_gen ≤ 250 GeV`, inclusive. Fixed bins:

```text
[50,75), [75,100), [100,125), [125,150),
[150,175), [175,200), [200,225), [225,250]
```

The 0–50 and 250–300 regions never enter headline selection or results.

## Primary metric

For each event:

```text
r_i = ||q_hat_i - q_true_i||_2 / E_total_true_i
q = (E_total, px, py, pz)
```

Compute RMS within each fixed energy bin and average the eight RMS values. Report micro RMS as a
secondary result. Narrow-bin R² is prohibited as a decision metric because the within-bin target
variance is deliberately small and can make R² strongly negative without answering the physics
question.

## Required companion metrics

- Energy response mean/median, mean bias, relative RMSE, central-68 half-width, MAE, p95/p99 error.
- Angular median/68th/95th percentile in mrad.
- px/py/pz bias, MAE, and RMSE.
- Energy response and four-vector error by energy and theta, plus phi, entry/exit margin, visible
  signal, hit count, ECAL fraction, containment, and no-signal/degenerate categories.
- Maximum and RMS mass-shell residual, with the statement that the constraint is by construction.
- Empirical interval coverage and mean width globally and in prespecified energy×theta cells.

Use group-level paired bootstrap confidence intervals with identical resamples for model differences.

## Selection gates

1. Every candidate must beat `B0` and `B1` on the primary validation score.
2. A neural model or blend must improve its simpler parent by at least 2% relative to justify added
   complexity.
3. No material regression may appear in a prespecified slice. Freeze the numerical materiality rule
   before training; use paired bootstrap differences where possible.
4. Mean absolute response bias above 5% in any focus energy bin is a red flag requiring a written
   exception; it is not silently averaged away.
5. Boundary pileup, calibration clipping, nonfinite output, shell failure, data leakage, or test
   access before freeze is a hard failure.

## Test unlock

Before any test read, persist hashes for data, split, code, environment, feature manifests, candidate
ledger, champion weights, calibration object, selection report, and the exact test query. There is
one test evaluation. A post-test bug fix is labeled a contaminated follow-up study rather than being
silently presented as the original locked result.
