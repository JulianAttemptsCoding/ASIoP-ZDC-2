# Raw kinetic-energy MSE Vertex retrain

## Run identity

| Field | Value |
| --- | --- |
| Vertex custom job | `projects/39719277374/locations/us-central1/customJobs/4614982912633208832` |
| Display name | `zdc-reco-raw-kinetic-mse-20260713` |
| State | `JOB_STATE_SUCCEEDED` |
| Runtime | 2026-07-13 02:29:45 UTC to 02:42:51 UTC (13 min 6 sec) |
| Worker | `n1-standard-32`, 300 GB `pd-standard`, CPU-only XGBoost |
| Source artifacts | `gs://asiop-zdc-1-zdc-reco-us-central1/runs/full-cpu-20260710-finalfix2/outputs` |
| New output artifacts | `gs://asiop-zdc-1-zdc-reco-us-central1/runs/raw-kinetic-mse-20260713-51b0ff0/outputs` |
| Container | `us-central1-docker.pkg.dev/asiop-zdc-1/zdc-reco/zdc-reco:kinetic-mse-20260713-51b0ff0` |
| Container digest | `sha256:86c10b5e0b64be7c11134315a006a224bd147ec343441c3bd00813d0f863ebde` |

The run reused the locked preflight, target, split, and feature artifacts. It cleared and rebuilt
only models, predictions, metrics, plots, selection, calibration, test evaluation, and verification.
Therefore the change is isolated to the energy-target parameterization and its induced model fits.

## Objective contract

For detector features `x`, true kinetic energy `K` in GeV, and a true unit direction
`u = (u_x, u_y, u_z)`, the energy head trains directly on `K`:

`K_hat = f_K(x)`

`L_K = sum_i w_i (f_K(x_i) - K_i)^2 + Omega(trees)`

The direction-component heads retain their squared-error targets. At inference, `K_hat` is clipped
to the nonnegative supported range, the predicted direction is normalized, and the final four-vector
is reconstructed on shell. The model metadata confirms:

| Metadata field | Value |
| --- | --- |
| Champion model | `M1_xgb_focus_only` |
| `training_target` | `kinetic_energy_plus_unit_direction` |
| `energy_target` | `kinetic_energy` |
| `energy_head_loss` | `squared error on raw kinetic_energy_gev` |
| Energy booster artifact | `models/M1_xgb_focus_only/kinetic_energy.json` |

## Validation selection

The validation-focus leaderboard selected the focus-only XGBoost candidate using the prespecified
macro RMS relative four-vector error from 50 to 250 GeV.

| Candidate | Macro RMS relative four-vector error | Energy relative RMSE | Energy MAE [GeV] | Angular 68% [mrad] |
| --- | ---: | ---: | ---: | ---: |
| `M1_xgb_focus_only` | 0.215140736 | 0.166153597 | 11.489449753 | 8.038215423 |
| `M1_xgb_full_support` | 0.218896381 | 0.162862556 | 11.859428833 | 8.345325099 |

## Locked focus-test result

| Metric | Direct-kinetic MSE retrain | Accepted `log1p(K)` model | Change |
| --- | ---: | ---: | ---: |
| Macro RMS relative four-vector error | 0.212001123 | 0.204433144 | +3.70% |
| Energy relative RMSE | 0.164703495 | 0.154351824 | +6.71% |
| Energy MAE [GeV] | 11.418698849 | 11.480341759 | -0.54% |
| Mean energy response | 1.023615329 | 1.023760075 | -0.000144746 |
| Angular 68% [mrad] | 7.981126926 | 7.981126926 | unchanged |
| Maximum mass-shell residual [GeV^2] | 2.5497e-11 | 3.2773e-11 | both on shell |

The direct-kinetic objective improves the focus-test absolute energy MAE slightly, but it does not
improve the prespecified primary selection metric or energy relative RMSE. The accepted `log1p(K)`
model remains preferred when the primary metric is macro RMS relative four-vector error.

## Calibration and artifact QA

The empirical energy-interval coverages on the locked focus test are 0.681997, 0.900385, and
0.951781 for nominal 68%, 90%, and 95% intervals respectively. The Vertex verifier completed with
`verified_artifacts: 14` and focus-test-metrics SHA-256
`12ee7718ccf06415f8f366246ff9e60c03f0a7ce8109d8eb2b1c85092c3604fb`.

The reproducible job specification is [raw_kinetic_mse_train.yaml](../vertex/raw_kinetic_mse_train.yaml),
and the training configuration is [vertex_kinetic_mse.yaml](../configs/vertex_kinetic_mse.yaml).
The full actual-energy and momentum-component comparison is in
[FOURVECTOR_COMPONENT_METRICS_COMPARISON.md](FOURVECTOR_COMPONENT_METRICS_COMPARISON.md).
