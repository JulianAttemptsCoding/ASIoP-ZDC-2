# Hit Unit Resolution

Created UTC: 2026-07-11

## Decision

`ecal_energy` and `hcal_energy` are locked as calibrated ideal simulated detector hit-energy
deposits in GeV with scale 1.0 for this run.

This is recorded as a data-owner/user override plus prior-pipeline evidence, not as ROOT-embedded
unit metadata. The ROOT branch titles alone still only contain names.

## Evidence Used

- User continuation instruction on 2026-07-11: use common-sense ZDC branch/spec mapping and inspect
  `C:\Users\Julia\OneDrive\Desktop\coding\ASIoP\ML ZDC all`.
- Prior implementation config:
  `C:\Users\Julia\OneDrive\Desktop\coding\ASIoP\ML ZDC all\configs\default.yaml`.
  It maps `ecal_signal: ecal_energy`, `hcal_signal: hcal_energy`, and sets
  `hit_signal_scale_to_gev: {ecal: 1.0, hcal: 1.0}`.
- Prior evidence artifact:
  `outputs/preflight/hit_unit_evidence.json`.
  It verifies in beginning, middle, and end windows that:
  - `energySum_ecal` equals the sum of `ecal_energy` to numerical precision.
  - `energySum_hcal` equals the sum of `hcal_energy` to numerical precision.
  - `energySum_ZDC` equals ECAL plus HCAL sums to numerical precision.
  - `energyRatio_*` equals the corresponding sum divided by `mcPar_mom`.
- The truth pass resolves `mcPar_mom` in GeV by neutron mass-shell closure, so the stored sums are
  consistent with GeV-valued ideal deposited/sampling signals.

## Resulting Lock

- ECAL signal branch: `ecal_energy`
- HCAL signal branch: `hcal_energy`
- ECAL scale to GeV: `1.0`
- HCAL scale to GeV: `1.0`
- Negative signal policy: disallowed by prior pipeline; sampled windows found no negative values.
- Threshold: `0.0 GeV`

## Caveat

This resolves the practical branch scale for the simulation run. It does not establish real-detector
SiPM digitization, electronics calibration, or deployment readiness.
