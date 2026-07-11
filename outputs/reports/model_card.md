# Model Card: M1_xgb_focus_only

## Model

- Model ID: `M1_xgb_focus_only`
- Family: scalar-feature XGBoost
- Target: `log1p` kinetic-energy head plus direction heads, converted to on-shell neutron
  `(E_total, px, py, pz)` in GeV.
- Selection population: validation focus, 50-250 GeV.
- Accepted test population: locked test focus, 50-250 GeV.

## Inputs

Inputs are scalar features derived from ECAL/HCAL hit positions and accepted calibrated hit-energy
signals:

- `ecal_energy` and `hcal_energy` are treated as ideal simulated deposited/sampling signals in GeV.
- ECAL and HCAL positions are converted to cm with `position_scale_to_cm: 0.1`.
- Geometry frame is inferred truth-free from ECAL-to-HCAL ordering.
- Truth columns are not used as inference features.

## Training And Selection

The validation leaderboard selected `M1_xgb_focus_only` over B0, B1, a direct ridge diagnostic, and a
full-support XGBoost variant. Validation focus macro RMS relative four-vector error:

- B0 visible-sum axis: `0.4511670594377147`
- B1 ridge constrained: `0.3647514684381928`
- M2 ridge direct projected: `0.3032120881165073`
- M1 XGBoost focus-only: `0.2038823903882062`
- M1 XGBoost full-support: `0.22075970994184996`

## Locked Test Performance

- Focus test events: `50,685`
- Macro RMS relative four-vector error: `0.20443314430393622`
- Energy MAE: `11.48034175891426 GeV`
- Energy relative RMSE: `0.1543518245985`
- Angular median: `5.872449369417561 mrad`
- Angular 68/95: `7.98112692599035 / 16.62022486411495 mrad`
- On-shell residual max: `3.2773117553119846e-11 GeV^2`

## Intended Use

Internal simulation-performance review for single-neutron ZDC four-vector reconstruction over the
50-250 GeV focus population.

## Not Intended For

- Real-detector deployment without digitization and calibration validation.
- Claims about an independently calibrated split-conformal interval.
- Claims that the newer dual-grid T4 model has been completed.
