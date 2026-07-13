# Direct kinetic-energy MSE retrain

This Vertex retrain changes only the energy-head parameterization relative to the accepted
`log1p(K)` model. It reuses the locked preflight, target, split, and feature artifacts from
`full-cpu-20260710-finalfix2` and writes results to a separate GCS output prefix.

For an event with detector features `x`, true kinetic energy `K`, and true unit direction
`u = (u_x, u_y, u_z)`, XGBoost trains four independent scalar heads:

`K_hat = f_K(x)`, `u_hat_j_raw = f_j(x)` for `j in {x, y, z}`.

The energy-head objective is weighted squared error in GeV:

`L_K = sum_i w_i (f_K(x_i) - K_i)^2 + Omega(trees)`.

The three direction heads retain their squared-error objectives on the unit-direction
components. At inference, `K_hat` is clipped to the supported nonnegative range, the direction
is normalized, and the final four-vector is reconstructed on shell. The selection metric remains
the prespecified macro RMS relative four-vector error on validation events from 50 to 250 GeV.
