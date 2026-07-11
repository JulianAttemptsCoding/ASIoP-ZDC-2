from __future__ import annotations

import numpy as np


def joint_energy_theta_weights(
    energy_gev: np.ndarray,
    theta_mrad: np.ndarray,
    energy_edges: np.ndarray,
    theta_edges: np.ndarray,
    *,
    maximum_weight_ratio: float = 10.0,
) -> np.ndarray:
    """Equalize occupied energy×theta cells without allowing tiny cells to dominate."""
    energy = np.asarray(energy_gev, dtype=float)
    theta = np.asarray(theta_mrad, dtype=float)
    if energy.shape != theta.shape:
        raise ValueError("energy and theta must have the same shape")
    ebin = np.clip(np.digitize(energy, energy_edges[1:-1]), 0, len(energy_edges) - 2)
    tbin = np.clip(np.digitize(theta, theta_edges[1:-1]), 0, len(theta_edges) - 2)
    key = ebin * (len(theta_edges) - 1) + tbin
    counts = np.bincount(key, minlength=(len(energy_edges) - 1) * (len(theta_edges) - 1))
    if np.any(counts[key] <= 0):
        raise RuntimeError("invalid occupied joint-bin count")
    weights = 1.0 / counts[key]
    positive = weights[weights > 0]
    floor = np.max(positive) / float(maximum_weight_ratio)
    weights = np.maximum(weights, floor)
    return weights / np.mean(weights)


def energy_objective_diagnostics(
    true_kinetic_gev: np.ndarray,
    predicted_kinetic_gev: np.ndarray,
    sample_weight: np.ndarray,
    energy_edges: np.ndarray,
) -> dict[str, float]:
    """Numpy reference for the energy loss terms used by both tree and neural studies."""
    truth = np.asarray(true_kinetic_gev, dtype=float)
    pred = np.asarray(predicted_kinetic_gev, dtype=float)
    weight = np.asarray(sample_weight, dtype=float)
    scale = np.maximum(truth, 25.0)
    relative = (pred - truth) / scale
    point = float(np.average(np.sqrt(1.0 + relative**2) - 1.0, weights=weight))
    bin_bias = []
    for index, (low, high) in enumerate(zip(energy_edges[:-1], energy_edges[1:], strict=True)):
        upper = (truth <= high) if index == len(energy_edges) - 2 else (truth < high)
        mask = (truth >= low) & upper
        if not np.any(mask):
            raise ValueError("an objective bin is empty")
        relative_bin = (pred[mask] - truth[mask]) / np.maximum(truth[mask], 1.0)
        bin_bias.append(float(np.average(relative_bin, weights=weight[mask])))
    return {
        "weighted_relative_pseudo_huber": point,
        "macro_bin_bias_rms": float(np.sqrt(np.mean(np.asarray(bin_bias) ** 2))),
        "max_abs_bin_bias": float(np.max(np.abs(bin_bias))),
    }
