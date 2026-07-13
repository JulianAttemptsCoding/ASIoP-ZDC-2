# Four-vector component metrics: direct kinetic MSE vs. accepted log1p(K)

## Evaluation definition

This comparison uses the **final calibrated reconstructed four-vectors** from both Vertex jobs.
All `E`, `px`, `py`, and `pz` values below are physical GeV values; none are in `log1p(K)` or
any other transformed training space.

The accepted model is `full-cpu-20260710-finalfix2/M1_xgb_focus_only`. The direct-kinetic
model is `raw-kinetic-mse-20260713-51b0ff0/M1_xgb_focus_only`. Both test files contain the same
76,105 event IDs, with the same 50,685 events in the 50--250 GeV focus range. The calibrated
validation files likewise contain the same 76,010 event IDs and 50,626 focus events.

For component `c`, the physical residual is `r_c = c_hat - c_true` in GeV. The unnormalized loss
is `MSE_c = mean(r_c^2)` in GeV^2. Since component-relative quantities are ill-defined when a
momentum component is near zero, every normalized result uses the well-defined four-vector scale
`r_c / E_true`. `R^2`, Pearson `r`, and the linear fit `c_hat = slope * c_true + intercept` are
computed directly from the calibrated outputs.

Regression has no single classification-style accuracy. The tolerance fractions below are the
explicit accuracy definitions: fraction of events within 1, 5, or 10 GeV and within 1%, 5%, or
10% of true total energy.

## Locked focus test: physical-unit loss and residual widths

| Component | Model | MSE [GeV^2] | RMSE [GeV] | MAE [GeV] | Bias [GeV] | Residual SD [GeV] | Abs. error 68% [GeV] | 90% [GeV] | 95% [GeV] |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| E | accepted log1p(K) | 402.369455 | 20.059149 | 11.480342 | -0.005072 | 20.059148 | 9.988402 | 27.606080 | 42.856956 |
| E | direct kinetic MSE | 397.043857 | 19.925959 | 11.418699 | +0.014918 | 19.925954 | 9.872899 | 28.576895 | 43.140247 |
| px | accepted log1p(K) | 25.619128 | 5.061534 | 2.369773 | +0.082407 | 5.060863 | 1.648557 | 5.881707 | 9.850720 |
| px | direct kinetic MSE | 25.262630 | 5.026194 | 2.382663 | +0.070316 | 5.025703 | 1.644102 | 6.043622 | 10.096170 |
| py | accepted log1p(K) | 25.597048 | 5.059353 | 2.375367 | +0.083983 | 5.058655 | 1.640271 | 5.862774 | 10.114193 |
| py | direct kinetic MSE | 25.241993 | 5.024141 | 2.387567 | -0.004889 | 5.024139 | 1.641052 | 6.044853 | 10.298996 |
| pz | accepted log1p(K) | 353.841597 | 18.810678 | 10.891486 | +0.057195 | 18.810591 | 9.622322 | 25.891312 | 40.242318 |
| pz | direct kinetic MSE | 349.318286 | 18.690058 | 10.825934 | +0.038301 | 18.690019 | 9.537346 | 26.761869 | 40.376345 |

## Locked focus test: energy-normalized error and fitted response

| Component | Model | Normalized MSE | Normalized RMSE | Normalized MAE | Normalized bias | Abs. normalized 68% | 95% | R^2 | Pearson r | Slope | Intercept [GeV] |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| E | accepted log1p(K) | 0.02382449 | 0.15435182 | 0.08641124 | +0.02376007 | 0.07684881 | 0.32328398 | 0.87889837 | 0.93749842 | 0.87682489 | 18.494818 |
| E | direct kinetic MSE | 0.02712724 | 0.16470349 | 0.08723350 | +0.02361533 | 0.07279467 | 0.33364495 | 0.88050122 | 0.93835303 | 0.87838498 | 18.280495 |
| px | accepted log1p(K) | 0.00151413 | 0.03891181 | 0.01771692 | +0.00039432 | 0.01216546 | 0.07436537 | 0.96764094 | 0.98372098 | 0.96025111 | 0.080076 |
| px | direct kinetic MSE | 0.00173763 | 0.04168491 | 0.01822460 | +0.00029745 | 0.01208790 | 0.07630795 | 0.96809123 | 0.98392120 | 0.96627289 | 0.068338 |
| py | accepted log1p(K) | 0.00152962 | 0.03911034 | 0.01782079 | -0.00125816 | 0.01223093 | 0.07686400 | 0.96709514 | 0.98345325 | 0.95860160 | -0.001633 |
| py | direct kinetic MSE | 0.00177537 | 0.04213511 | 0.01834255 | -0.00209971 | 0.01203982 | 0.07951274 | 0.96755156 | 0.98364616 | 0.96474652 | -0.077797 |
| pz | accepted log1p(K) | 0.02093098 | 0.14467544 | 0.08200518 | +0.02284288 | 0.07402343 | 0.30225871 | 0.88724711 | 0.94193875 | 0.88661239 | 16.553886 |
| pz | direct kinetic MSE | 0.02377066 | 0.15417736 | 0.08266048 | +0.02233961 | 0.07007388 | 0.31202537 | 0.88868848 | 0.94270475 | 0.88698110 | 16.481349 |

## Locked focus test: tolerance accuracy

| Component | Model | <= 1 GeV | <= 5 GeV | <= 10 GeV | <= 1% E_true | <= 5% E_true | <= 10% E_true |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| E | accepted log1p(K) | 9.658% | 44.037% | 68.022% | 14.150% | 54.712% | 75.127% |
| E | direct kinetic MSE | 10.778% | 46.270% | 68.338% | 15.216% | 57.031% | 75.997% |
| px | accepted log1p(K) | 53.562% | 87.993% | 95.101% | 63.027% | 91.408% | 96.881% |
| px | direct kinetic MSE | 53.787% | 87.653% | 94.904% | 63.236% | 91.114% | 96.747% |
| py | accepted log1p(K) | 53.598% | 88.060% | 94.924% | 62.806% | 91.248% | 96.685% |
| py | direct kinetic MSE | 53.929% | 87.669% | 94.738% | 63.208% | 91.009% | 96.514% |
| pz | accepted log1p(K) | 9.857% | 44.812% | 69.222% | 14.397% | 55.606% | 76.220% |
| pz | direct kinetic MSE | 11.019% | 47.148% | 69.303% | 15.543% | 57.964% | 77.023% |

## Calibrated validation check

Validation is shown for diagnostics only because its energy response calibration is fitted on that
same split. The locked test above is the unbiased final comparison.

| Component | Model | MSE [GeV^2] | RMSE [GeV] | MAE [GeV] | Normalized RMSE | R^2 | Pearson r |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| E | accepted log1p(K) | 414.279591 | 20.353859 | 11.584899 | 0.15594118 | 0.87544048 | 0.93564977 |
| E | direct kinetic MSE | 409.218863 | 20.229159 | 11.499976 | 0.16636276 | 0.87696207 | 0.93646253 |
| px | accepted log1p(K) | 26.595441 | 5.157077 | 2.385802 | 0.04016884 | 0.96619853 | 0.98297587 |
| px | direct kinetic MSE | 26.311625 | 5.129486 | 2.395595 | 0.04296198 | 0.96655924 | 0.98313792 |
| py | accepted log1p(K) | 26.907627 | 5.187256 | 2.394932 | 0.03969890 | 0.96552820 | 0.98263518 |
| py | direct kinetic MSE | 26.632244 | 5.160644 | 2.406269 | 0.04278535 | 0.96588100 | 0.98279278 |
| pz | accepted log1p(K) | 364.477432 | 19.091292 | 10.994331 | 0.14612352 | 0.88399814 | 0.94021293 |
| pz | direct kinetic MSE | 360.136121 | 18.977253 | 10.905963 | 0.15567159 | 0.88537984 | 0.94094633 |

## Interpretation

Direct kinetic-energy MSE reduces unnormalized test MSE/RMSE for all four final components and
improves absolute-energy tolerance accuracy. It gives slightly worse energy-normalized RMSE for
all four components, which explains the worse macro RMS relative four-vector score used for model
selection. The directional angular metric is unchanged to displayed precision because the direction
heads and their targets are unchanged; the momentum-component differences arise from the changed
predicted energy magnitude used by the on-shell four-vector reconstruction.
