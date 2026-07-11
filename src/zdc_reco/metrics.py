from __future__ import annotations

import numpy as np

from .constants import EPS
from .physics import mass_shell_residual, unit_direction


def angular_error_mrad(true_direction: np.ndarray, predicted_direction: np.ndarray) -> np.ndarray:
    true_unit, true_valid = unit_direction(np.asarray(true_direction, dtype=float))
    pred_unit, pred_valid = unit_direction(np.asarray(predicted_direction, dtype=float))
    if not np.all(true_valid & pred_valid):
        raise ValueError("Angular metrics require valid true and predicted directions")
    dot = np.sum(true_unit * pred_unit, axis=1)
    return 1000.0 * np.arccos(np.clip(dot, -1.0, 1.0))


def relative_fourvector_error(
    true_fourvector: np.ndarray, predicted_fourvector: np.ndarray
) -> np.ndarray:
    true = np.asarray(true_fourvector, dtype=float)
    predicted = np.asarray(predicted_fourvector, dtype=float)
    numerator = np.linalg.norm(predicted - true, axis=1)
    return numerator / np.maximum(true[:, 0], EPS)


def robust_width68(values: np.ndarray) -> float:
    q16, q84 = np.quantile(np.asarray(values, dtype=float), [0.16, 0.84])
    return float(0.5 * (q84 - q16))


def evaluate_fourvectors(
    true_fourvector: np.ndarray,
    predicted_fourvector: np.ndarray,
    *,
    mass_gev: float,
) -> dict[str, float]:
    true = np.asarray(true_fourvector, dtype=float)
    predicted = np.asarray(predicted_fourvector, dtype=float)
    if true.shape != predicted.shape or true.ndim != 2 or true.shape[1] != 4:
        raise ValueError("Four-vector arrays must both have shape (n_events, 4)")
    response = predicted[:, 0] / true[:, 0]
    relative_energy = response - 1.0
    true_u, valid_true = unit_direction(true[:, 1:])
    pred_u, valid_pred = unit_direction(predicted[:, 1:])
    direction_mask = valid_true & valid_pred
    angle = angular_error_mrad(true_u[direction_mask], pred_u[direction_mask])
    fv_error = relative_fourvector_error(true, predicted)
    shell = mass_shell_residual(predicted, mass_gev)
    return {
        "n_events": int(len(true)),
        "energy_response_mean": float(np.mean(response)),
        "energy_response_median": float(np.median(response)),
        "energy_relative_bias_mean": float(np.mean(relative_energy)),
        "energy_relative_rmse": float(np.sqrt(np.mean(relative_energy**2))),
        "energy_relative_width68": robust_width68(relative_energy),
        "energy_mae_gev": float(np.mean(np.abs(predicted[:, 0] - true[:, 0]))),
        "angular_valid_fraction": float(np.mean(direction_mask)),
        "angular_median_mrad": float(np.median(angle)) if len(angle) else float("nan"),
        "angular_68_mrad": float(np.quantile(angle, 0.68)) if len(angle) else float("nan"),
        "angular_95_mrad": float(np.quantile(angle, 0.95)) if len(angle) else float("nan"),
        "relative_fourvector_error_mean": float(np.mean(fv_error)),
        "relative_fourvector_error_rms": float(np.sqrt(np.mean(fv_error**2))),
        "mass_shell_residual_abs_max_gev2": float(np.max(np.abs(shell))),
    }


def macro_rms_by_energy_bin(
    errors: np.ndarray,
    generator_energy_gev: np.ndarray,
    edges: np.ndarray,
) -> float:
    errors = np.asarray(errors, dtype=float)
    energy = np.asarray(generator_energy_gev, dtype=float)
    values = []
    for lo, hi in zip(edges[:-1], edges[1:], strict=True):
        mask = (energy >= lo) & (energy < hi)
        if np.sum(mask) == 0:
            raise ValueError(f"Empty required energy bin [{lo}, {hi})")
        values.append(float(np.sqrt(np.mean(errors[mask] ** 2))))
    return float(np.mean(values))
