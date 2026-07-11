from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

from .constants import EPS, NEUTRON_MASS_GEV


@dataclass(frozen=True)
class EnergyConvention:
    semantics: str
    energy_scale_to_gev: float
    momentum_scale_to_gev: float
    median_relative_residual: float
    p99_relative_residual: float
    second_best_score_ratio: float

    def to_dict(self) -> dict:
        return asdict(self)


def momentum_magnitude(px: np.ndarray, py: np.ndarray, pz: np.ndarray) -> np.ndarray:
    return np.sqrt(px * px + py * py + pz * pz)


def unit_direction(momentum: np.ndarray, min_norm: float = 0.0) -> tuple[np.ndarray, np.ndarray]:
    p = np.linalg.norm(momentum, axis=-1)
    valid = np.isfinite(p) & (p > max(float(min_norm), EPS))
    out = np.zeros_like(momentum, dtype=float)
    out[valid] = momentum[valid] / p[valid, None]
    return out, valid


def fourvector_from_kinetic_direction(
    kinetic_energy_gev: np.ndarray,
    direction: np.ndarray,
    mass_gev: float = NEUTRON_MASS_GEV,
) -> np.ndarray:
    kinetic = np.maximum(np.asarray(kinetic_energy_gev, dtype=float), 0.0)
    unit, valid = unit_direction(np.asarray(direction, dtype=float))
    if not np.all(valid):
        raise ValueError("Every predicted direction must have finite nonzero norm")
    total = kinetic + mass_gev
    p_mag = np.sqrt(np.maximum(kinetic * (kinetic + 2.0 * mass_gev), 0.0))
    return np.column_stack([total, p_mag[:, None] * unit])


def mass_shell_residual(fourvector: np.ndarray, mass_gev: float = NEUTRON_MASS_GEV) -> np.ndarray:
    fv = np.asarray(fourvector, dtype=float)
    return fv[:, 0] ** 2 - np.sum(fv[:, 1:] ** 2, axis=1) - mass_gev**2


def infer_energy_convention(
    raw_energy: np.ndarray,
    raw_momentum: np.ndarray,
    *,
    mass_gev: float = NEUTRON_MASS_GEV,
    median_tolerance: float = 1e-5,
    p99_tolerance: float = 1e-3,
    min_score_ratio: float = 10.0,
) -> EnergyConvention:
    """Resolve total-vs-kinetic and GeV-vs-MeV without silently guessing.

    A convention is accepted only if it agrees with the on-shell energy and is
    decisively better than every alternative candidate.
    """
    raw_energy = np.asarray(raw_energy, dtype=float).reshape(-1)
    raw_momentum = np.asarray(raw_momentum, dtype=float)
    if raw_momentum.shape != (len(raw_energy), 3):
        raise ValueError("raw_momentum must have shape (n_events, 3)")
    finite = np.isfinite(raw_energy) & np.all(np.isfinite(raw_momentum), axis=1)
    if finite.sum() < 100:
        raise ValueError("At least 100 finite truth rows are required to infer units")
    e0 = raw_energy[finite]
    p0 = raw_momentum[finite]
    candidates: list[tuple[float, float, float, str, float, float]] = []
    for e_scale in (1.0, 1.0e-3):
        for p_scale in (1.0, 1.0e-3):
            on_shell = np.sqrt(np.sum((p0 * p_scale) ** 2, axis=1) + mass_gev**2)
            for semantics in ("total", "kinetic"):
                stated_total = e0 * e_scale + (mass_gev if semantics == "kinetic" else 0.0)
                rel = np.abs(stated_total - on_shell) / np.maximum(on_shell, mass_gev)
                median = float(np.median(rel))
                p99 = float(np.quantile(rel, 0.99))
                score = max(median, p99 / 100.0)
                candidates.append((score, median, e_scale, semantics, p_scale, p99))
    candidates.sort(key=lambda item: item[0])
    best, second = candidates[0], candidates[1]
    score, median, e_scale, semantics, p_scale, p99 = best
    ratio = float(second[0] / max(score, np.finfo(float).tiny))
    if score > median_tolerance or p99 > p99_tolerance:
        raise ValueError(
            "No energy/unit convention passes the mass-shell tolerances; inspect branch mapping "
            f"and units. Best={semantics}, E scale={e_scale}, p scale={p_scale}, "
            f"median={median:.3g}, p99={p99:.3g}."
        )
    if ratio < min_score_ratio:
        raise ValueError(
            "Energy/unit convention is ambiguous; lock it explicitly after inspection. "
            f"Best/second score ratio={ratio:.3g}, required={min_score_ratio:.3g}."
        )
    return EnergyConvention(semantics, e_scale, p_scale, median, p99, ratio)


def canonical_truth(
    raw_generator_energy: np.ndarray,
    raw_momentum: np.ndarray,
    convention: EnergyConvention,
    *,
    mass_gev: float = NEUTRON_MASS_GEV,
    min_direction_p_gev: float = 1e-4,
) -> dict[str, np.ndarray]:
    generator = np.asarray(raw_generator_energy, dtype=float) * convention.energy_scale_to_gev
    momentum = np.asarray(raw_momentum, dtype=float) * convention.momentum_scale_to_gev
    p_mag = np.linalg.norm(momentum, axis=1)
    total = np.sqrt(p_mag**2 + mass_gev**2)
    kinetic = total - mass_gev
    direction, direction_valid = unit_direction(momentum, min_direction_p_gev)
    return {
        "generator_energy_gev": generator,
        "energy_true_gev": total,
        "kinetic_energy_true_gev": kinetic,
        "px_true_gev": momentum[:, 0],
        "py_true_gev": momentum[:, 1],
        "pz_true_gev": momentum[:, 2],
        "ux_true": direction[:, 0],
        "uy_true": direction[:, 1],
        "uz_true": direction[:, 2],
        "theta_true_rad": np.arccos(np.clip(direction[:, 2], -1.0, 1.0)),
        "phi_true_rad": np.arctan2(direction[:, 1], direction[:, 0]),
        "direction_valid": direction_valid,
    }
