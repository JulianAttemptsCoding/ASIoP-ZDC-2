from __future__ import annotations

import numpy as np

NEUTRON_MASS_GEV = 0.93956542052
EPS = np.finfo(float).eps


def unit_direction(vectors: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    values = np.asarray(vectors, dtype=float)
    if values.ndim != 2 or values.shape[1] != 3:
        raise ValueError("vectors must have shape (n, 3)")
    norm = np.linalg.norm(values, axis=1)
    valid = np.isfinite(norm) & (norm > EPS)
    result = np.zeros_like(values)
    result[valid] = values[valid] / norm[valid, None]
    return result, valid


def fourvector_from_kinetic_direction(
    kinetic_gev: np.ndarray,
    direction: np.ndarray,
    mass_gev: float = NEUTRON_MASS_GEV,
) -> np.ndarray:
    kinetic = np.asarray(kinetic_gev, dtype=float).reshape(-1)
    if np.any(~np.isfinite(kinetic)) or np.any(kinetic < 0.0):
        raise ValueError("kinetic energy must be finite and nonnegative")
    unit, valid = unit_direction(direction)
    if len(unit) != len(kinetic) or not np.all(valid):
        raise ValueError("every event needs a finite nonzero direction")
    total = kinetic + float(mass_gev)
    momentum = np.sqrt(kinetic * (kinetic + 2.0 * float(mass_gev)))
    return np.column_stack([total, unit * momentum[:, None]])


def mass_shell_residual(fourvector: np.ndarray, mass_gev: float = NEUTRON_MASS_GEV) -> np.ndarray:
    values = np.asarray(fourvector, dtype=float)
    if values.ndim != 2 or values.shape[1] != 4:
        raise ValueError("fourvector must have shape (n, 4)")
    return values[:, 0] ** 2 - np.sum(values[:, 1:] ** 2, axis=1) - mass_gev**2


def tangent_basis(axis: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return normalized axis and a deterministic orthonormal tangent basis per event."""
    u, valid = unit_direction(axis)
    if not np.all(valid):
        raise ValueError("analytic axes must all be valid")
    reference = np.zeros_like(u)
    use_x = np.abs(u[:, 0]) < 0.8
    reference[use_x, 0] = 1.0
    reference[~use_x, 1] = 1.0
    e1, valid_e1 = unit_direction(np.cross(u, reference))
    if not np.all(valid_e1):
        raise RuntimeError("failed to construct tangent basis")
    e2 = np.cross(u, e1)
    return u, e1, e2


def apply_tangent_residual(axis: np.ndarray, residual_ab: np.ndarray) -> np.ndarray:
    residual = np.asarray(residual_ab, dtype=float)
    if residual.ndim != 2 or residual.shape[1] != 2 or len(residual) != len(axis):
        raise ValueError("residual_ab must have shape (n, 2)")
    u, e1, e2 = tangent_basis(axis)
    corrected, valid = unit_direction(
        u + residual[:, :1] * e1 + residual[:, 1:] * e2
    )
    if not np.all(valid):
        raise RuntimeError("direction residual produced an invalid direction")
    return corrected
