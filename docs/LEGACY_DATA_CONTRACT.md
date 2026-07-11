# Data contract

## Hard preflight gates

1. Exactly one intended ROOT TTree/RNTuple is selected and recorded.
2. Required logical branches map to existing physical branches with types recorded.
3. Detector x/y/z/signal arrays have equal per-event lengths.
4. At least one primary neutron is present per included event; the selection is unique and documented.
5. Energy semantics and energy/momentum units pass the configured mass-shell tolerances.
6. The generator-energy support covers the requested 0–300 GeV scan and the 50–250 focus.
7. ECAL/HCAL hit signal units/meaning and conversion to GeV are non-null and documented.
8. Negative, zero, thresholded, saturated, and nonfinite signal policies are explicit.
9. The detector-local transform is truth-free, orthonormal, right-handed, and ECAL→HCAL.
10. Projected geometry reconciles with 20×20 ECAL cells and 64×8 HCAL segmentation, or a documented
    reason explains the ROOT representation.
11. Stable event and source-group identifiers exist; otherwise independence is established and
    event UID grouping is explicitly justified.
12. Detector fingerprints are computed before splitting.

## Target table and feature table separation

`targets.parquet` may contain truth. `features_manifest.parquet` may contain only event ID, detector
features, geometry features, and quality flags. Training joins them by event UID only after split
assignment. The feature manifest is an allowlist; training never says “use every non-truth column.”

## Energy definitions

- `generator_energy_gev`: converted raw generator branch; defines 50–250 benchmark membership.
- `energy_true_gev`: on-shell total neutron energy.
- `kinetic_energy_true_gev`: total energy minus neutron mass; primary energy regression target.
- `px/py/pz_true_gev`: converted truth momentum components.

## Empty and failed events

No-hit and axis-degenerate events are not silently removed. Each receives explicit flags. Report:

- fraction of all generated events passing the task's inclusion contract;
- no-signal fraction;
- direction-valid fraction;
- performance for all included events;
- performance for the prespecified reconstructable subset.

## Simulation validity boundary

If hits are ideal simulation deposits, the model is validated only on that simulation distribution.
Do not claim deployment readiness without electronics digitization and real calibration/validation.
