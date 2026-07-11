from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from .constants import EPS
from .contracts import validate_hit_event
from .geometry import DetectorFrame


def _weighted_mean(values: np.ndarray, weights: np.ndarray) -> np.ndarray:
    return np.sum(values * weights[:, None], axis=0) / max(float(np.sum(weights)), EPS)


def _weighted_line_axis(points: np.ndarray, weights: np.ndarray) -> dict[str, float]:
    centroid = _weighted_mean(points, weights)
    centered = points - centroid
    z = centered[:, 2]
    denom = float(np.sum(weights * z * z))
    if len(points) < 2 or denom <= EPS:
        return {
            "axis_slope_xz": 0.0,
            "axis_slope_yz": 0.0,
            "axis_u_x": 0.0,
            "axis_u_y": 0.0,
            "axis_u_z": 1.0,
            "axis_residual_rms_cm": 0.0,
            "axis_degenerate": 1.0,
        }
    sx = float(np.sum(weights * z * centered[:, 0]) / denom)
    sy = float(np.sum(weights * z * centered[:, 1]) / denom)
    direction = np.asarray([sx, sy, 1.0])
    direction /= np.linalg.norm(direction)
    fit_x = centroid[0] + sx * centered[:, 2]
    fit_y = centroid[1] + sy * centered[:, 2]
    residual2 = (points[:, 0] - fit_x) ** 2 + (points[:, 1] - fit_y) ** 2
    residual = np.sqrt(np.sum(weights * residual2) / max(float(np.sum(weights)), EPS))
    return {
        "axis_slope_xz": sx,
        "axis_slope_yz": sy,
        "axis_u_x": float(direction[0]),
        "axis_u_y": float(direction[1]),
        "axis_u_z": float(direction[2]),
        "axis_residual_rms_cm": float(residual),
        "axis_degenerate": 0.0,
    }


def _weighted_pca(points: np.ndarray, weights: np.ndarray) -> dict[str, float]:
    if len(points) < 3 or float(np.sum(weights)) <= EPS:
        return {
            "pca_u_x": 0.0,
            "pca_u_y": 0.0,
            "pca_u_z": 1.0,
            "pca_lambda1_frac": 0.0,
            "pca_lambda2_frac": 0.0,
            "pca_lambda3_frac": 0.0,
            "pca_degenerate": 1.0,
        }
    centroid = _weighted_mean(points, weights)
    centered = points - centroid
    covariance = (centered * weights[:, None]).T @ centered / max(float(np.sum(weights)), EPS)
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    order = np.argsort(eigenvalues)[::-1]
    eigenvalues = np.maximum(eigenvalues[order], 0.0)
    axis = eigenvectors[:, order[0]]
    if axis[2] < 0.0:
        axis = -axis
    fractions = eigenvalues / max(float(np.sum(eigenvalues)), EPS)
    return {
        "pca_u_x": float(axis[0]),
        "pca_u_y": float(axis[1]),
        "pca_u_z": float(axis[2]),
        "pca_lambda1_frac": float(fractions[0]),
        "pca_lambda2_frac": float(fractions[1]),
        "pca_lambda3_frac": float(fractions[2]),
        "pca_degenerate": 0.0,
    }


def _profile_features(
    z: np.ndarray,
    signal: np.ndarray,
    bounds: tuple[float, float],
    groups: int,
) -> dict[str, float]:
    if groups <= 0:
        return {}
    lo, hi = bounds
    span = max(hi - lo, EPS)
    index = np.clip(((z - lo) / span * groups).astype(int), 0, groups - 1)
    energy = np.bincount(index, weights=signal, minlength=groups).astype(float)
    hits = np.bincount(index, minlength=groups).astype(float)
    total = max(float(np.sum(energy)), EPS)
    n_hits = max(float(np.sum(hits)), 1.0)
    out: dict[str, float] = {}
    for group in range(groups):
        out[f"depth_g{group:02d}_energy_frac"] = float(energy[group] / total)
        out[f"depth_g{group:02d}_hit_frac"] = float(hits[group] / n_hits)
    cumulative = np.cumsum(energy) / total
    for quantile in (0.10, 0.50, 0.90):
        out[f"depth_cum{int(quantile * 100):02d}_group"] = float(
            np.searchsorted(cumulative, quantile)
        )
    out["depth_peak_group"] = float(np.argmax(energy))
    out["front_energy_frac"] = float(energy[0] / total)
    out["back_energy_frac"] = float(energy[-1] / total)
    return out


def _subdetector_features(
    prefix: str,
    points: np.ndarray,
    signal: np.ndarray,
    *,
    z_bounds: tuple[float, float],
    depth_groups: int,
    top_hit_counts: Sequence[int],
    density_edges_gev: Sequence[float],
) -> dict[str, float]:
    out: dict[str, float] = {}
    if len(signal) == 0 or float(np.sum(signal)) <= EPS:
        base_names = [
            "total_signal_gev",
            "max_hit_gev",
            "n_hits",
            "centroid_x_cm",
            "centroid_y_cm",
            "centroid_z_cm",
            "rms_x_cm",
            "rms_y_cm",
            "rms_z_cm",
            "effective_n_hits",
        ]
        out.update({f"{prefix}_{name}": 0.0 for name in base_names})
        out[f"{prefix}_empty"] = 1.0
        for count in top_hit_counts:
            out[f"{prefix}_top{count}_energy_frac"] = 0.0
        for index in range(len(density_edges_gev) + 1):
            out[f"{prefix}_density_bin{index:02d}_hit_frac"] = 0.0
            out[f"{prefix}_density_bin{index:02d}_energy_frac"] = 0.0
        axis = _weighted_line_axis(np.empty((0, 3)), np.empty(0))
        pca = _weighted_pca(np.empty((0, 3)), np.empty(0))
        out.update({f"{prefix}_{k}": v for k, v in axis.items()})
        out.update({f"{prefix}_{k}": v for k, v in pca.items()})
        out.update(
            {
                f"{prefix}_{k}": v
                for k, v in _profile_features(
                    np.empty(0), np.empty(0), z_bounds, depth_groups
                ).items()
            }
        )
        return out
    total = float(np.sum(signal))
    centroid = _weighted_mean(points, signal)
    centered = points - centroid
    rms = np.sqrt(np.sum(centered**2 * signal[:, None], axis=0) / total)
    effective_n = total**2 / max(float(np.sum(signal**2)), EPS)
    out.update(
        {
            f"{prefix}_total_signal_gev": total,
            f"{prefix}_max_hit_gev": float(np.max(signal)),
            f"{prefix}_n_hits": float(len(signal)),
            f"{prefix}_centroid_x_cm": float(centroid[0]),
            f"{prefix}_centroid_y_cm": float(centroid[1]),
            f"{prefix}_centroid_z_cm": float(centroid[2]),
            f"{prefix}_rms_x_cm": float(rms[0]),
            f"{prefix}_rms_y_cm": float(rms[1]),
            f"{prefix}_rms_z_cm": float(rms[2]),
            f"{prefix}_effective_n_hits": float(effective_n),
            f"{prefix}_empty": 0.0,
        }
    )
    sorted_signal = np.sort(signal)[::-1]
    for count in top_hit_counts:
        out[f"{prefix}_top{count}_energy_frac"] = float(np.sum(sorted_signal[:count]) / total)
    density_counts, _ = np.histogram(signal, bins=[-np.inf, *density_edges_gev, np.inf])
    density_energy, _ = np.histogram(
        signal, bins=[-np.inf, *density_edges_gev, np.inf], weights=signal
    )
    for index, (count, energy) in enumerate(zip(density_counts, density_energy, strict=True)):
        out[f"{prefix}_density_bin{index:02d}_hit_frac"] = float(count / len(signal))
        out[f"{prefix}_density_bin{index:02d}_energy_frac"] = float(energy / total)
    out.update({f"{prefix}_{k}": v for k, v in _weighted_line_axis(points, signal).items()})
    out.update({f"{prefix}_{k}": v for k, v in _weighted_pca(points, signal).items()})
    out.update(
        {
            f"{prefix}_{k}": v
            for k, v in _profile_features(points[:, 2], signal, z_bounds, depth_groups).items()
        }
    )
    return out


def build_event_features(
    *,
    ecal_x: np.ndarray,
    ecal_y: np.ndarray,
    ecal_z: np.ndarray,
    ecal_signal_gev: np.ndarray,
    hcal_x: np.ndarray,
    hcal_y: np.ndarray,
    hcal_z: np.ndarray,
    hcal_signal_gev: np.ndarray,
    frame: DetectorFrame,
    ecal_threshold_gev: float = 0.0,
    hcal_threshold_gev: float = 0.0,
    ecal_depth_groups: int = 2,
    hcal_depth_groups: int = 8,
    top_hit_counts: Sequence[int] = (1, 3, 5, 10, 20),
    density_edges_gev: Sequence[float] = (0.0001, 0.001, 0.01, 0.1, 1.0),
) -> dict[str, float]:
    validate_hit_event(ecal_x, ecal_y, ecal_z, ecal_signal_gev)
    validate_hit_event(hcal_x, hcal_y, hcal_z, hcal_signal_gev)
    e_signal = np.asarray(ecal_signal_gev, dtype=float)
    h_signal = np.asarray(hcal_signal_gev, dtype=float)
    if np.any(e_signal < 0.0) or np.any(h_signal < 0.0):
        raise ValueError("Negative calibrated hit signals require an explicit noise policy")
    e_keep = e_signal > ecal_threshold_gev
    h_keep = h_signal > hcal_threshold_gev
    e_points_global = np.column_stack([ecal_x, ecal_y, ecal_z]).astype(float)[e_keep]
    h_points_global = np.column_stack([hcal_x, hcal_y, hcal_z]).astype(float)[h_keep]
    e_points = frame.transform(e_points_global) if len(e_points_global) else np.empty((0, 3))
    h_points = frame.transform(h_points_global) if len(h_points_global) else np.empty((0, 3))
    e_signal = e_signal[e_keep]
    h_signal = h_signal[h_keep]
    out = _subdetector_features(
        "ecal",
        e_points,
        e_signal,
        z_bounds=frame.ecal_z_bounds,
        depth_groups=ecal_depth_groups,
        top_hit_counts=top_hit_counts,
        density_edges_gev=density_edges_gev,
    )
    out.update(
        _subdetector_features(
            "hcal",
            h_points,
            h_signal,
            z_bounds=frame.hcal_z_bounds,
            depth_groups=hcal_depth_groups,
            top_hit_counts=top_hit_counts,
            density_edges_gev=density_edges_gev,
        )
    )
    all_points = np.vstack([e_points, h_points])
    all_signal = np.concatenate([e_signal, h_signal])
    combined = _subdetector_features(
        "all",
        all_points,
        all_signal,
        z_bounds=(frame.ecal_z_bounds[0], frame.hcal_z_bounds[1]),
        depth_groups=0,
        top_hit_counts=top_hit_counts,
        density_edges_gev=density_edges_gev,
    )
    out.update(combined)
    visible = out["ecal_total_signal_gev"] + out["hcal_total_signal_gev"]
    out["visible_signal_gev"] = visible
    out["log1p_visible_signal"] = float(np.log1p(max(visible, 0.0)))
    out["ecal_signal_fraction"] = out["ecal_total_signal_gev"] / max(visible, EPS)
    out["hcal_signal_fraction"] = out["hcal_total_signal_gev"] / max(visible, EPS)
    out["no_detector_signal"] = float(visible <= EPS)
    axis_cos = max(out["all_axis_u_z"], 0.05)
    out["axis_sec_theta_clipped"] = 1.0 / axis_cos
    out["visible_signal_times_axis_cos"] = visible * axis_cos
    out["hcal_back_leakage_proxy"] = out.get("hcal_back_energy_frac", 0.0)
    half_x, half_y = 32.5, 30.0
    back_z = frame.hcal_z_bounds[1]
    dz = back_z - out["all_centroid_z_cm"]
    exit_x = out["all_centroid_x_cm"] + out["all_axis_slope_xz"] * dz
    exit_y = out["all_centroid_y_cm"] + out["all_axis_slope_yz"] * dz
    out["axis_exit_x_cm"] = float(exit_x)
    out["axis_exit_y_cm"] = float(exit_y)
    out["axis_exit_margin_x_cm"] = float(half_x - abs(exit_x))
    out["axis_exit_margin_y_cm"] = float(half_y - abs(exit_y))
    out["axis_exit_min_margin_cm"] = min(out["axis_exit_margin_x_cm"], out["axis_exit_margin_y_cm"])
    if not all(np.isfinite(value) for value in out.values()):
        raise ValueError("Feature builder produced NaN or infinity")
    return out


def feature_manifest(feature_names: Sequence[str]) -> list[dict]:
    manifest = []
    for name in feature_names:
        kind = (
            "quality_flag"
            if any(token in name for token in ("empty", "degenerate", "no_"))
            else "detector"
        )
        manifest.append(
            {
                "feature": name,
                "source_kind": kind,
                "source_branches": ["ECAL/HCAL hit positions and calibrated signals"],
            }
        )
    return manifest
