# Locked evaluation protocol

## Populations

- Training support: 0–300 GeV after convention conversion.
- Focus validation: 50–250 GeV inclusive; only population used for model/HPO selection.
- Validation calibration: the same validation fold is reused after selection for a prespecified final
  response correction and empirical uncertainty quantiles.
- Focus test: 50–250 GeV inclusive; opened once after champion freeze.
- Shoulders: 0–50 and 250–300 GeV; diagnostic only.

Use a single, consistent boundary ownership rule in code. Recommended fixed focus bins are
`[50,75), [75,100), …, [225,250]`, with the final upper edge inclusive.

## Primary validation score

For event `i`:

```text
r_i = ||q_hat_i - q_true_i||_2 / E_total_true_i
q = (E_total, px, py, pz)
```

Compute RMS within every fixed focus energy bin, then average those bin RMS values. Empty bins are a
hard failure. This score combines energy and direction in the units of the actual four-vector while
preventing the training distribution from setting implicit energy weights. It is deliberately a
Euclidean lab-frame reconstruction score, not a Lorentz-invariant physics observable; energy,
momentum-component, angle, and mass-shell metrics remain separately mandatory.

## Required slice veto

Before any test access, freeze a material-regression rule for energy, theta, phi, containment margin,
back-leakage proxy, shower start, and hit count. Prefer a paired group-bootstrap confidence interval
over arbitrary single-number thresholds. A model cannot win by improving the aggregate while
damaging a physically important slice.

## Statistical reporting

- Point estimates plus group-level paired bootstrap 95% confidence intervals.
- Same bootstrap resamples across compared models.
- Report micro and macro metrics; primary is macro.
- Do not fit Gaussian widths without a goodness-of-fit statement; always include central-68 width
  and tails.
- Empirical interval coverage is reported on the untouched test set globally and by energy-angle
  slice. Because validation controlled model selection and interval calibration, do not claim an
  ordinary split-conformal finite-sample guarantee.

## Test unlock

`test_unlock.json` must include timestamp, champion model/config/code/data hashes, fitted calibration
hash, exact test query, validation leaderboard hash, selection-decision hash, and a statement that no
further tuning is allowed. Any post-test change creates a new study and cannot reuse the test as
untouched evidence.
