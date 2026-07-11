# Ten full independent QC passes

This ledger reports verifiable audit judgments and actioned changes, not private chain-of-thought.
Each pass restarted from the complete Master QC Checklist and reviewed the entire package as it stood
at that pass.

## QC Pass #1 of 10 — objective, evidence boundary, and attachment completeness

1. **Fresh-Mind Baseline Assessment:** The strongest evidence is the historical response slope and
   theta dependence. The work initially risked sounding like a new trained result despite no raw data
   in the audit environment.
2. **Benchmark Comparison:** Compared framing with CALICE software compensation (1207.4210,
   2403.04632) and Akchurin et al. (2107.10207), all of which tie architecture to measurable shower
   information and an executed dataset.
3. **Master Checklist Line-by-Line Audit:** Items 1–8 and 53–58 were checked first, then all remaining
   items for downstream consistency. Failed: no explicit distinction between historical evidence and
   future result; old tarball cache files were not individually accounted for. Passed: focus range,
   output, detector, data size, and budget were visible.
4. **Actioned Revisions:** Added archive hashes, per-file/per-sheet audit, cache-category audit,
   historical-result labels, simulation boundary, and an explicit statement that no new score is
   fabricated.

## QC Pass #2 of 10 — physics and target semantics

1. **Fresh-Mind Baseline Assessment:** An on-shell output is necessary but could be marketed as model
   quality when it is merely parameterization. Energy semantics remain a critical preflight risk.
2. **Benchmark Comparison:** Checked neutron-mass-shell handling against the PDG-based constant and
   calorimeter studies’ separation of measured response from physical constraints.
3. **Master Checklist Line-by-Line Audit:** All 58 items reviewed; items 9–14, 32, 36, and 53 received
   adversarial emphasis. Failed: the narrative did not explicitly require recomputation of momentum
   after point calibration; zero-direction behavior needed a hard error/fallback contract.
4. **Actioned Revisions:** Added kinetic-energy parameterization, tangent-axis validity handling,
   post-calibration momentum recomputation, and wording that shell closure is a construction invariant.
   Added executable shell and tangent-basis tests.

## QC Pass #3 of 10 — split, leakage, and validation/calibration reuse

1. **Fresh-Mind Baseline Assessment:** A random 80/10/10 split is insufficient if simulation batches or
   duplicate showers cross folds. Reusing validation is acceptable for a locked final test but changes
   uncertainty claims.
2. **Benchmark Comparison:** Compared with `StratifiedGroupKFold`, leakage evidence from Tampu et al.,
   and conformalized quantile regression assumptions (Romano et al.).
3. **Master Checklist Line-by-Line Audit:** All items reviewed; 15–20 and 30–34 failed partially. Group
   priority and duplicate fingerprints were not sufficiently fail-closed; calibration language could
   be mistaken for formal coverage.
4. **Actioned Revisions:** Froze group-safe 80/10/10, group-priority resolution, exact/near-duplicate
   gates, target/feature separation, one-time test unlock, and the explicit “empirical, not independent
   split-conformal” label in README, config, evaluation protocol, and prompt.

## QC Pass #4 of 10 — diagnosis of the supplied model

1. **Fresh-Mind Baseline Assessment:** The redesign must follow observed failures, not architecture
   fashion. The supplied direction performance is already much stronger than energy response.
2. **Benchmark Comparison:** Compared supplied slices with CALICE density compensation and HGCAL
   leakage/topology findings.
3. **Master Checklist Line-by-Line Audit:** All items reviewed; 2, 7–8, 21–29, 35–41 were examined
   against workbook values. Failed: tail-driver claims were too causal; theta and energy confounding
   were not explicit; exit-margin instability was underemphasized.
4. **Actioned Revisions:** Made energy linearity/angle compensation the central goal; required
   within-energy×theta tail analyses; added robust clipping plus validity flags for margins; demoted
   feature-gain averages and marginal correlations from causal evidence.

## QC Pass #5 of 10 — tabular baseline and loss design

1. **Fresh-Mind Baseline Assessment:** Replacing XGBoost without reproducing it would prevent causal
   learning about the response slope. The log target may contribute to relative-error compression but
   cannot be blamed without an ablation.
2. **Benchmark Comparison:** Compared XGBoost’s primary paper/current official objectives and tabular
   benchmarks by Grinsztajn et al. and Gorishniy et al.
3. **Master Checklist Line-by-Line Audit:** All items reviewed; 21–24 and 35–45 were emphasized. Failed:
   a single new energy target would not isolate target-transform effects; monotonic constraints were
   initially treated too favorably.
4. **Actioned Revisions:** Required three tree energy variants—historical log1p, raw K, and residual to
   a calibrated-sum baseline—under one protocol. Added bounded joint energy×theta weights and made
   total-signal monotonicity an ablation because histogram constraints can shallow trees.

## QC Pass #6 of 10 — neural representation and compute feasibility

1. **Fresh-Mind Baseline Assessment:** The fixed detector has only 912 grid positions, favoring compact
   dense views over a costly dynamic graph. The HCAL’s depth×slice structure differs from the ECAL face.
2. **Benchmark Comparison:** Compared CNN/GNN high-granularity calorimeter work (2107.10207,
   2406.11937) and Deep Sets (1703.06114).
3. **Master Checklist Line-by-Line Audit:** All items reviewed; 25–29, 42–52 were stressed. Failed: one
   shared image shape would erase detector semantics; trial/parameter limits were missing; grid lossless
   mapping was assumed.
4. **Actioned Revisions:** Specified separate 20×20 and 64×8 encoders, three channels, <1.5M parameters,
   four neural trials, tiny-set overfit/numerical gates, and a hard grid-mapping proof. GNN became
   escalation-only.

## QC Pass #7 of 10 — calibration and uncertainty

1. **Fresh-Mind Baseline Assessment:** Calibration can improve point response without changing trained
   weights, but an overly flexible angle-aware calibrator could simply become a second model and overfit
   validation.
2. **Benchmark Comparison:** Compared official isotonic regression behavior and conformalized quantile
   regression’s independent calibration logic.
3. **Master Checklist Line-by-Line Audit:** All items reviewed; 30–34, 38–41, and 53–56 were emphasized.
   Failed: a proposed angle-binned calibrator introduced discontinuity/complexity and used more degrees
   of freedom than the evidence justified.
4. **Actioned Revisions:** Reduced point calibration to one global energy-balanced isotonic mapping on
   predicted energy only; added identity comparison, 0.5% clipping gate, post-calibration shell rebuild,
   empirical coverage and interval-width tables, and explicit selection-dependence caveats.

## QC Pass #8 of 10 — metrics, slices, and statistical claims

1. **Fresh-Mind Baseline Assessment:** The historical deck overuses R² in contexts where it is not
   stable, and global averages conceal the low-energy and high-angle failures.
2. **Benchmark Comparison:** Compared reporting practices in CALICE/HGCAL studies: response linearity,
   resolution versus energy, leakage, and population-specific results.
3. **Master Checklist Line-by-Line Audit:** All items reviewed; 35–41 and 53–55 were checked metric by
   metric. Failed: final-bin ownership was not executable; historical comparison could be misread as
   paired; slice materiality lacked a freeze requirement.
4. **Actioned Revisions:** Added exact inclusive last-bin masks and tests, fixed-bin macro primary score,
   companion/tail metrics, common group bootstrap resamples, preregistered slice materiality, a 5% bin
   bias red flag, and unpaired historical-comparison wording.

## QC Pass #9 of 10 — Vertex cost, operations, and reproducibility

1. **Fresh-Mind Baseline Assessment:** A $90 credit statement is not a hard cap. Unbounded tuning or an
   idle resource could exhaust it even with good modeling logic.
2. **Benchmark Comparison:** Checked current Google custom-training/configuration documentation and the
   explicit Cloud Billing warning that budgets do not cap spending.
3. **Master Checklist Line-by-Line Audit:** All items reviewed; 42–52 and 57–58 were emphasized. Failed:
   earlier materials still referred to a $100/$80/$20 policy; templates lacked an operational reserve
   tied to the user’s new cap.
4. **Actioned Revisions:** Changed every active limit to $90 absolute, $78 planned, $12 reserve; allocated
   stage ceilings; required current regional rates/availability, one replica/trial, timeouts, labels,
   resumability, and no persistent resources/endpoints. Added executable budget refusal tests.

## QC Pass #10 of 10 — full integration and adversarial handoff

1. **Fresh-Mind Baseline Assessment:** The package is coherent only if the audit, config, model design,
   evaluation rules, code primitives, Vertex templates, and one-shot prompt say the same thing and the
   clean archive runs after extraction.
2. **Benchmark Comparison:** Rechecked every cited primary/official source and compared the artifact
   contract with rigorous applied-ML/HEP reproducibility expectations: frozen data/splits, baselines,
   provenance, uncertainty caveats, group statistics, cost ledger, and executable tests.
3. **Master Checklist Line-by-Line Audit:** All 58 items were re-audited end to end. Remaining conditional
   items—actual ROOT schema, grid mapping, performance, cloud prices/cost, integration/Docker tests, and
   final plot rendering—cannot pass without the user’s data/cloud execution and are explicitly hard
   gates for the coding agent, not falsely marked complete. Scaffold-local physics, metric, boundary,
   objective-weight, empirical-quantile, and budget tests passed before packaging.
4. **Actioned Revisions:** Removed ambiguous winner language; synchronized 50–250, 80/10/10, validation
   reuse, $78/$90, model/trial limits, calibration, and test-lock rules across all files. Added clean
   archive inspection and checksum requirements to the one-shot prompt. Final status: the design is
   internally consistent and evidence-backed; real-data performance remains intentionally unclaimed
   until the agent completes the locked run.
