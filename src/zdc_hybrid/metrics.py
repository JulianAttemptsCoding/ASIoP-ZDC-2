from __future__ import annotations

import numpy as np

from .physics import EPS, mass_shell_residual, unit_direction


def focus_mask(
    generator_energy_gev: np.ndarray, low: float = 50.0, high: float = 250.0
) -> np.ndarray:
    energy = np.asarray(generator_energy_gev, dtype=float)
    return np.isfinite(energy) & (energy >= low) & (energy <= high)


def fixed_bin_masks(values: np.ndarray, edges: np.ndarray) -> list[np.ndarray]:
    x = np.asarray(values, dtype=float)
    e = np.asarray(edges, dtype=float)
    if len(e) < 2 or np.any(np.diff(e) <= 0):
        raise ValueError("edges must be strictly increasing")
    masks = []
    for index, (low, high) in enumerate(zip(e[:-1], e[1:], strict=True)):
        mask = (x >= low) & ((x <= high) if index == len(e) - 2 else (x < high))
        masks.append(mask)
    return masks


def relative_fourvector_error(true: np.ndarray, predicted: np.ndarray) -> np.ndarray:
    truth = np.asarray(true, dtype=float)
    pred = np.asarray(predicted, dtype=float)
    if truth.shape != pred.shape or truth.ndim != 2 or truth.shape[1] != 4:
        raise ValueError("four-vectors must have matching shape (n, 4)")
    return np.linalg.norm(pred - truth, axis=1) / np.maximum(truth[:, 0], EPS)


def macro_rms_relative_fourvector(
    true: np.ndarray,
    predicted: np.ndarray,
    generator_energy_gev: np.ndarray,
    edges: np.ndarray,
) -> float:
    errors = relative_fourvector_error(true, predicted)
    scores = []
    for mask in fixed_bin_masks(generator_energy_gev, edges):
        if not np.any(mask):
            raise ValueError("a required evaluation bin is empty")
        scores.append(float(np.sqrt(np.mean(errors[mask] ** 2))))
    return float(np.mean(scores))


def angular_error_mrad(true_direction: np.ndarray, predicted_direction: np.ndarray) -> np.ndarray:
    true_u, true_valid = unit_direction(true_direction)
    pred_u, pred_valid = unit_direction(predicted_direction)
    if not np.all(true_valid & pred_valid):
        raise ValueError("angular error requires valid directions")
    dot = np.sum(true_u * pred_u, axis=1)
    return 1000.0 * np.arccos(np.clip(dot, -1.0, 1.0))


def response_by_bin(
    true_energy: np.ndarray,
    predicted_energy: np.ndarray,
    generator_energy_gev: np.ndarray,
    edges: np.ndarray,
) -> list[dict[str, float]]:
    truth = np.asarray(true_energy, dtype=float)
    pred = np.asarray(predicted_energy, dtype=float)
    response = pred / np.maximum(truth, EPS)
    rows = []
    intervals = zip(edges[:-1], edges[1:], strict=True)
    masks = fixed_bin_masks(generator_energy_gev, edges)
    for (low, high), mask in zip(intervals, masks, strict=True):
        if not np.any(mask):
            raise ValueError("a required response bin is empty")
        residual = response[mask] - 1.0
        q16, q84 = np.quantile(residual, [0.16, 0.84])
        rows.append({
            "low_gev": float(low),
            "high_gev": float(high),
            "n": int(np.sum(mask)),
            "mean_response": float(np.mean(response[mask])),
            "mean_bias": float(np.mean(residual)),
            "rmse": float(np.sqrt(np.mean(residual**2))),
            "central68_half_width": float(0.5 * (q84 - q16)),
        })
    return rows


def assert_physical_predictions(
    predicted: np.ndarray, mass_gev: float, atol_gev2: float = 1e-8
) -> None:
    values = np.asarray(predicted, dtype=float)
    if not np.all(np.isfinite(values)):
        raise ValueError("predictions contain nonfinite values")
    if np.any(values[:, 0] < mass_gev):
        raise ValueError("predicted total energy is below neutron mass")
    if np.max(np.abs(mass_shell_residual(values, mass_gev))) > atol_gev2:
        raise ValueError("predictions fail the neutron mass-shell tolerance")
