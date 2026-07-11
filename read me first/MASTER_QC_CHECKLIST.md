# Master QC checklist

Target domain: applied machine learning for single-particle calorimeter reconstruction. Target
standard: rigorous, reproducible internal HEP physics-performance review, benchmarked against the
primary calorimeter-ML studies in `RESEARCH.md`.

Every full QC pass must restart at item 1 and audit the complete package. `PASS` requires an artifact,
test, citation, or explicit fail-closed requirement; prose intent alone is not evidence.

## A. Objective and framing

1. The first 30 seconds identify input, output, particle, detector, 50–250 GeV focus, data size, and
   $90 cap.
2. The central novelty/significance is precise: correct response compression and angle-dependent
   compensation with a geometry-aligned hybrid, not “use AI.”
3. Historical numbers are labeled historical; no unrun result is presented as new performance.
4. The simulation-versus-real-detector validity boundary is explicit.

## B. Attachment evidence

5. Both archive hashes and integrity results are recorded.
6. Every ZIP file, workbook sheet, deck slide/layout class, original source file, placeholder, and
   generated cache category is accounted for.
7. All quantitative claims trace to supplied tables or cited sources.
8. Correlation/tail findings are not described causally without conditional analysis.

## C. Physics and detector correctness

9. Neutron energy semantics/units are inferred against the mass shell and fail on ambiguity.
10. Benchmark membership uses the locked converted generator branch; output uses total energy.
11. Direction validity at zero momentum is explicit.
12. Final output is finite, nonnegative in kinetic energy, normalized in direction, and on shell.
13. Detector frame and grid mapping are truth-free and reconcile 20×20 and 64×8 geometry.
14. Hit signal units, thresholds, negatives, saturation, duplicate IDs, empty sections, and unmapped
    hits have locked policies.

## D. Data integrity and leakage

15. Event, group, source, and data hashes exist.
16. Exactly one primary-neutron policy is verified; multi-primary ambiguity stops execution.
17. Split is group-safe 80/10/10, deterministic, order-independent, and frozen before modeling.
18. Exact and near-duplicate detector fingerprints do not cross splits.
19. Features and targets are physically separated; an allowlist/provenance graph replaces a name
    denylist.
20. All preprocessing/scaling/binning is train-fitted; calibration is validation-fitted; test is
    never used until the one-time unlock.

## E. Model logic

21. B0/B1 are credible and use the same postprocessing/evaluation.
22. The current log-target XGBoost is reproduced before claiming improvement.
23. Raw-K and baseline-residual XGBoost variants directly test the compression hypothesis.
24. Joint energy×theta weighting cannot create uncontrolled weights.
25. The neural grid tensors are lossless relative to the locked segmentation or the run stops.
26. The dual-grid model is parameter/budget bounded and passes tiny-set overfit/numerical tests.
27. Direction predicts a minimal tangent residual around an analytic axis with fallback behavior.
28. Ensemble weights are discrete/prespecified and complexity requires ≥2% validation gain.
29. GNN/Deep Sets escalation has residual, information, and cost gates.

## F. Calibration and uncertainty

30. Champion selection closes before point calibration.
31. Calibration uses predicted energy only, is global/monotone, is compared with identity, and tracks
    out-of-domain clipping.
32. Four-vector momentum is recomputed after calibrated energy.
33. Validation reuse is declared; no independent split-conformal guarantee is claimed.
34. Empirical interval coverage and width are reported globally and by energy×theta on locked test.

## G. Metrics and statistics

35. Primary metric is fixed-bin macro RMS relative four-vector error.
36. Companion energy, angular, component, shell, tail, and population metrics are complete.
37. Narrow-bin R² is not a decision metric.
38. Energy-bin boundaries are unambiguous and 250 GeV is included exactly once.
39. Model comparisons use paired independent-group bootstrap with common resamples.
40. Slice materiality rules and 5% bin-bias red flag are frozen before test.
41. Historical comparison is not called paired without common event predictions.

## H. Training and reproducibility

42. Every candidate stores config, seed, split/feature/data/code/environment hashes, train rows,
    weights, history, runtime, hardware, model hash, and predictions.
43. Per-head early stopping has a meaningful minimum delta and confirmation seeds.
44. Optimized feature/grid building matches a scalar reference and has a 50k benchmark.
45. Stages are atomic, resumable, and invalidate downstream artifacts on upstream changes.
46. Unit, integration, tiny ROOT, Docker, clean-environment, and archive tests pass.
47. No TODO, placeholder executable path, secret, absolute personal path, data, model, cache, or fake
    metric is shipped.

## I. Vertex and cost

48. Current official regional price/availability is recorded immediately before submission.
49. Maximum committed cost is ≤$78 and absolute spend is ≤$90.
50. Every job uses one replica/concurrent trial, an explicit timeout, labels, and resumable outputs.
51. No idle persistent resource or online endpoint exists.
52. Budget alerts are not treated as a spending cap; optional work stops at the operational limit.

## J. Final communication and visual QA

53. Final report leads with locked 50–250 test performance and exact counts.
54. Plots use saved predictions, units, readable labels, counts, uncertainty, consistent definitions,
    and no misleading axes.
55. Tables fit their medium; deck/document render checks find no clipping/overlap.
56. Limitations, failures, costs, and exact reproduction commands are visible.
57. The clean tarball extracts, imports, passes tests, and contains a manifest/checksum.
58. The one-shot prompt is standalone, nonambiguous, and requires evidence after every phase.
