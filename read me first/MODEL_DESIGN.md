# Model design and decision record

## Decision

Use a validation-gated hybrid ladder:

1. `B0`: calibrated ECAL+HCAL sum with analytic line/PCA direction.
2. `B1`: regularized linear scalar-feature baseline.
3. `T1`: corrected tabular XGBoost family.
4. `N1`: compact dual-grid calorimeter network.
5. `H1`: discrete convex blend of `T1` and `N1`, only when complementary.
6. `G1`: Deep Sets/GNN escalation only after a residual and cost gate.

The champion is whichever of `T1`, `N1`, or `H1` passes the prespecified validation rules. The plan
does not declare a neural winner before seeing validation data.

## Evidence from the supplied results

- Focus test energy: R² 0.879, MAE 11.48 GeV, RMSE 20.06 GeV.
- Direction: angular median 5.87 mrad, 68th percentile 7.98 mrad, 95th percentile 16.62 mrad.
- Test response changes from 1.158 in 50–75 GeV to 0.941 in 225–250 GeV.
- Test four-vector RMS changes from 0.077 in the lowest-angle quartile to 0.362 in the highest.
- `hcal_total_signal` dominates the reported gain importance, while hit count, visible signal, and
  shower collimation correlate with tail error.

These facts identify energy compensation and angle/containment conditioning as the primary problem.
They do not establish causal tail drivers: the reported correlations and p99 contrasts were not
conditioned on true energy and angle.

## Input representation

### Grid branches

Only after cell/layer/slice mapping is proven from IDs or coordinate centers:

- ECAL tensor: `[3, 20, 20]`.
- HCAL tensor: `[3, 64, 8]`.
- Channels: robustly scaled signal, `log1p` scaled signal, and occupancy/mask.

All channel scales are fitted on train only. Multiple hits in a cell are summed; occupancy records
whether any accepted hit exists. Underflow, overflow, unmapped, duplicate-ID, negative-signal, and
saturation-like hits are counted and governed by the locked data contract. No event is silently
dropped because a section is empty.

### Scalar branch

Use a small allowlisted set, not all 189 supplied engineered variables. Candidate families are:

- ECAL/HCAL/total signal and hit count;
- centroids and robust transverse/longitudinal widths;
- analytic axis, PCA collimation, fit residual, and degeneracy flags;
- ECAL fraction, density summaries, shower start/peak/back fraction;
- robust exit/containment quantities with clipped values plus validity flags.

Remove algebraic duplicates and compositional redundancy: total signal versus duplicate aliases,
both members of fractions that sum to one, duplicate leakage proxies, all profile fractions when one
is implied, and raw/slope/unit-vector copies unless an ablation demonstrates value. The supplied exit
margin has extreme outliers (standard deviation hundreds of cm); use a validity flag and a
prespecified robust clip learned from detector geometry, never z-score it naively.

## `T1`: corrected XGBoost

Reproduce the current `log1p(K)` model, then compare it with two prespecified variants:

- raw nonnegative kinetic energy with Pseudo-Huber loss;
- residual `K − K0`, where `K0` is the train-fitted calibrated-sum baseline.

All use joint energy×theta sample balancing. Compare constrained and unconstrained total-signal
monotonicity; do not assume the constraint wins, because histogram constraints can reduce effective
tree depth. Direction predicts two tangent-plane residuals around the analytic axis rather than three
redundant Cartesian components. Train each head with its own meaningful early stopping and minimum
improvement tolerance.

## `N1`: dual-grid network

Two small encoders preserve the different detector structures:

- ECAL: two residual 2D convolution blocks, downsample, global average/max pooling.
- HCAL: anisotropic residual blocks over depth×slice, with early kernels favoring depth.
- Scalars: LayerNorm → 64 → 64 MLP.
- Fusion: concatenate pooled branches → 128 → 64 with dropout.

Keep the total parameter count below 1.5 million. Use mixed precision on one T4. The energy head
outputs a nonnegative kinetic energy plus ordered q16/q50/q84 information; the direction head outputs
two tangent residuals. Use an explicit analytic-axis fallback for empty/degenerate inputs.

The training objective is:

```text
L = L_relative_pseudo_huber(K)
  + 0.35 * RMS_over_energy_bins(mean relative bias)
  + 0.15 * mean(1 - dot(u_hat, u_true))
  + 0.10 * quantile loss
```

The exact weights are a starting configuration, not hidden degrees of freedom. At most four neural
trials are allowed. Use a deterministic stratified batch sampler so every batch contains every focus
energy bin and broad theta coverage; otherwise the macro-bin term is not defined reliably. Log the
per-batch composition and fall back to an epoch-aggregated differentiable term only if parity tests
show the implementation is equivalent. Validation ranking always uses the physics metrics, not
training loss. For XGBoost, bin bias is a validation/early-stopping metric rather than a custom
non-additive tree objective.

## On-shell output

For neutron mass `m`, predict `K_hat ≥ 0` and unit direction `u_hat`, then compute:

```text
E_total_hat = K_hat + m
|p_hat| = sqrt(K_hat * (K_hat + 2m))
p_hat = |p_hat| * u_hat
```

The shell check is a construction invariant, not evidence of predictive accuracy.

## Calibration

After champion selection is closed, fit exactly one global, energy-balanced isotonic mapping:

```text
E_cal = f_monotone(E_uncalibrated)
```

Inputs are predicted energy only—never true energy bin, true angle, or test information. This
corrects global response compression while preserving ordering. Compare with identity and reject the
calibrator if it worsens the fixed validation score/slices or clips more than 0.5% of focus events.
Recompute kinetic energy and momentum magnitude after calibration, retaining the frozen direction.

Validation reuse makes calibration-dependent validation estimates optimistic; the locked test is the
honest final estimate. The same validation residuals may define empirical 68/90/95% intervals, but no
independent split-conformal claim is permitted.

## Why not default GNN

GNN results in high-granularity calorimeters show that spatial shower structure and leakage can be
learned, but this detector already has small, fixed regular grids. A dual-grid CNN is cheaper,
simpler, and geometry-aligned. Escalate only if `N1` leaves stable residual dependence on within-cell
or irregular hit topology, grid mapping loses material information, and the remaining budget covers
a preregistered comparison.
