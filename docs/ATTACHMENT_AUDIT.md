# Exhaustive attachment audit

## Scope and integrity

Two user attachments were available in the conversation and were inspected before redesign:

- `zdc_fourvector_reco_researched_repo.tar(1).gz`, SHA-256
  `0babbd5b70fb612dc043db55ecac2352ffa21cec86e0a2889ca4f9aae3313d0d`.
- `ZDC_all_neutron_analysis_bundle_20260711.zip`, SHA-256
  `b066cdfd239cdb85edbfdb58336ecf60d85fbd2e2d16da4504242e2787a23ed3`.

Both archives passed decompression/integrity checks. The ZIP contains 20 files. The tarball includes
generated `.pytest_cache` and `__pycache__` content; those are packaging defects and are not carried
forward.

## Analysis bundle: every file

| File | Audit finding |
|---|---|
| `analysis_bundle_README.txt` | Useful summary and provenance. Reports 50–250 test metrics and best rounds, but cannot reproduce them because code, model, predictions, split manifest, and hashes are absent. |
| `angular_error.png` | Readable. Shows a skewed angular tail and improving angular performance with energy. Supports keeping a robust angle percentile suite. |
| `component_bias_resolution_slices.png` | E and pz share a strong energy-dependent bias; px/py are much smaller. Confirms the four-vector error is energy-dominated. |
| `component_pred_vs_true.png` | Clear regression-to-the-mean/compressed slope for E and pz; transverse components are more linear. |
| `component_residuals.png` | E/pz have skew/heavy tails. Gaussian sigma alone is inadequate; central-68 and p95/p99 are required. |
| `core_figures_montage.png` | Convenient overview but too small for quantitative review; the source figures were checked individually. |
| `energy_bias_resolution_slices.png` | Most important diagnostic: mean bias decreases monotonically from strong over-response at low energy to under-response at high energy. |
| `energy_response_density.png` | Confirms response compression and heteroscedasticity. A single global score hides this structure. |
| `error_driver_correlations.png` | Hit count, visible signal, and collimation correlate with error, but no conditioning on energy/theta was performed; causal language is unsupported. |
| `feature_importance.png` | `hcal_total_signal` dominates mean gain. Mean gain across four independent heads is not directly comparable unless normalized per head. Algebraically redundant features remain. |
| `final_deck_slide_montage.png` | Exposes general flow but not text defects; all 20 source slides were rendered and reviewed individually. |
| `pencil_vs_all_neutron_energy.png` | The comparison is not apples-to-apples because angle/population conditions differ. It may be context, not a headline model comparison. |
| `research_analysis_notes.txt` | Concise and directionally sound; repeats headline results. It does not resolve validation/calibration dependence or missing reproducibility artifacts. |
| `tail_feature_contrast.png` | p99 events have lower signal/fewer hits/worse margins, but these effects are confounded by energy and angle. Requires within-bin or partial analysis. |
| `test_focus_energy_slice_diagnostics.png` | Confirms the largest defect is the low-to-high energy response slope and corresponding four-vector degradation. |
| `training_validation_loss_components.png` | Best validation overall round differs from energy/pz rounds. The plotted staged curves are reconstructed from boosters rather than original evaluation history. |
| `training_validation_loss_native_heads.png` | Direction improvements at rounds near 2500 are numerically tiny; lack of a minimum-delta rule makes “best at 2499” misleading. Validation ux/uy RMSE being far below train RMSE needs explanation. |
| `training_validation_loss_overall.png` | Overall validation minimum around round 735 is shallow; training continues to improve. A stable early-stopping rule and confirmation seeds are needed. |
| `ZDC_All_Neutron_Four_Vector_Results_vs_Pencil_Beam.pptx` | OOXML integrity passes; 20 slides; no custom speaker notes/comments. Slides 6 and 11 have title/separator collisions; slides 10, 12, and 18 have clipped/wrapped cards/tables; slide 20 clips its title. Slide 13’s shell result is by construction. Slide 19 lacks precise source links. Not presentation-ready. |
| `zdc_analysis_tables.xlsx` | OOXML integrity passes. Thirteen visible sheets, no hidden rows/columns/sheets, formulas, charts, tables, or merged cells. Useful static evidence, but not an executable analysis workbook. |

## Workbook: every sheet and material findings

| Sheet | Audit finding |
|---|---|
| `json_summaries` | 764,940 events; 612,825/76,010/76,105 train/validation/test, already approximately 80/10/10. Contains job and best-round summaries. |
| `component_metrics` | Focus test E RMSE 20.06 GeV and normalized bias +2.38%; px/py much better than E/pz. |
| `slice_metrics` | Narrow-bin R² is often very negative because target variance is narrow; it must not be used for slice ranking. Outside-focus results are catastrophically poor for the focus-only model, as expected. |
| `angular_metrics` | Median/68/95 angle metrics are present and useful; retain them. |
| `pencil_comparison` | Populations are not matched; contextual only. |
| `feature_importance` | 189 features. Gain averaged over four heads without per-head normalization; many exact or compositional redundancies. No obvious truth-named feature, but provenance cannot be verified without code. |
| `loss_physics` | Validation overall best round 735; E/pz best about 980; px/py changes at ~2499 are negligible. Common-round and per-head histories must be distinguished. |
| `loss_native_heads` | Energy head best validation RMSE occurs around round 917 while effective saved round differs; direction train/validation discrepancy requires data/weight audit. |
| `advanced_components` | Validation and test response differ materially. P99 component errors are large. A paired prediction table is needed to identify whether this is split drift, calibration overfit, or both. |
| `advanced_slices` | Test 50–75 bias +15.76%, 225–250 bias −5.95%. Highest theta quartile four-vector RMS 0.362 versus 0.077 in the lowest. Dominant redesign evidence. |
| `error_correlations` | Hit count correlation with relative four-vector error about −0.54; visible signal about −0.38. These are marginal correlations, not independent drivers. |
| `tail_contrast` | p99 events have lower signal/hits and worse exit margin. Must be repeated within energy×theta cells and with bootstrap uncertainty. |
| `feature_summary` | Visible signal averages only ~4.3 GeV for much larger neutron energy, consistent with a sampling/deposit observable. Exit-margin standard deviations of hundreds of cm show unstable extrapolation/outliers requiring validity flags and robust clipping. |

## Original tarball: every tracked/source file

| File | Audit finding |
|---|---|
| `.gitignore` | Incomplete packaging discipline because caches were nevertheless shipped. |
| `README.md` | Clearly calls itself a scaffold, but points to an unimplemented pipeline. |
| `PLAN.md` | Long research plan with useful model ladder; duplicated by `plan.md` and internally retained the old 70/15/15 split. |
| `plan.md` | Duplicate source of truth; removal required. |
| `AGENT_PROMPT.md` | Broad instructions, but it could not overcome ten unconditional placeholder scripts without implementation work. |
| `configs/default.yaml` | Encodes assumptions and the old split; schema/units remain unresolved. |
| `docs/DATA_CONTRACT.md` | Helpful intent, insufficient fail-closed implementation. |
| `docs/FEATURE_POLICY.md` | Useful feature tiers; name-substring leakage denial is bypassable by aliases/proxies. |
| `docs/QC_CHECKLIST.md` | Checklist exists, but evidence binding and repeated end-to-end passes are absent. |
| `docs/SOURCES.md` | Useful bibliography; several claims need tighter source-to-decision mapping. |
| `pyproject.toml` | Minimal package metadata; dependencies were split into a loose requirements file. |
| `requirements.txt` | Only lower bounds; not reproducible and can resolve to incompatible future combinations. |
| `scripts/00_inspect_root.py` | Placeholder; cannot inspect data. |
| `scripts/01_build_targets.py` | Placeholder; cannot establish labels. |
| `scripts/02_make_splits.py` | Placeholder; cannot enforce leakage-safe split. |
| `scripts/03_build_features.py` | Placeholder; cannot create the stated features. |
| `scripts/04_train_baselines.py` | Placeholder; no baseline evidence. |
| `scripts/05_train_xgb_constrained.py` | Placeholder; no model training. |
| `scripts/06_train_xgb_direct.py` | Placeholder; no ablation. |
| `scripts/07_evaluate.py` | Placeholder; no locked evaluation. |
| `scripts/08_plot_diagnostics.py` | Placeholder; no plots from predictions. |
| `scripts/09_verify.py` | Placeholder; no final verification. |
| `scripts/run_all_local.sh` | Orchestrates placeholders and therefore cannot complete. |
| `scripts/validate_repo.py` | Validates scaffold presence, not scientific execution. |
| `src/zdc_fourvector/__init__.py` | Version marker only. |
| `src/zdc_fourvector/constants.py` | Neutron mass constant is reasonable. |
| `src/zdc_fourvector/features.py` | Family declarations only; leakage check relies on names rather than source provenance. |
| `src/zdc_fourvector/metrics.py` | Basic metrics, but standard deviation/R² can mislead; lacks group bootstrap, fixed-bin macro score, validity populations, and robust tails. |
| `src/zdc_fourvector/targets.py` | Normalizes directions, but zero momentum lacks a validity mask; `E<m` silently creates zero momentum and an off-shell output except at `E=m`. |
| `tests/conftest.py` | Import-path setup only. |
| `tests/test_features.py` | Small name-based leakage test; does not catch provenance aliases. |
| `tests/test_targets.py` | Covers a nominal shell case but not zero momentum, sub-mass energy, units, ambiguity, or support boundaries. |
| `vertex/README.md` | General cloud guidance; no hard operational $90 plan. |
| `vertex/custom_job_template.yaml` | Template only; region, image, data, current price, timeout, and availability unresolved. |

## Generated files/directories inside the tarball

Every `.pytest_cache` entry (`.gitignore`, `CACHEDIR.TAG`, `README.md`, `lastfailed`, `nodeids`) and
every `.pyc` under the source/test `__pycache__` directories was identified as generated local state.
These files are not authoritative source, can expose stale test outcomes/interpreter versions, and
must be excluded. Empty output directories contain no evidence.

## Cross-file/system findings

1. The historical bundle's current model is a credible baseline, not a finished solution.
2. Its response compression is consistent with an objective/model-selection mismatch and incomplete
   angle/containment compensation; the available artifacts cannot isolate the cause.
3. Validation and test low-energy response differ materially despite large sample counts. Possible
   causes include calibration selection dependence, split distribution mismatch, grouping leakage,
   or unrecorded processing differences. Only predictions plus split/calibration artifacts can decide.
4. The feature list is overcomplete and contains unstable geometry extrapolations.
5. No claim about improved performance can be made until the actual data pipeline is executed under a
   frozen protocol. The new repository is therefore explicit about what is implemented versus what
   the coding agent must run.
