from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np


@dataclass(frozen=True)
class DetectorFrame:
    origin: tuple[float, float, float]
    x_axis: tuple[float, float, float]
    y_axis: tuple[float, float, float]
    z_axis: tuple[float, float, float]
    ecal_z_bounds: tuple[float, float]
    hcal_z_bounds: tuple[float, float]

    @property
    def rotation(self) -> np.ndarray:
        return np.asarray([self.x_axis, self.y_axis, self.z_axis], dtype=float)

    def transform(self, points: np.ndarray) -> np.ndarray:
        return (np.asarray(points, dtype=float) - np.asarray(self.origin)) @ self.rotation.T

    def to_dict(self) -> dict:
        return asdict(self)


def _unit(vector: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(vector))
    if not np.isfinite(norm) or norm <= 0.0:
        raise ValueError("Cannot normalize detector-frame axis")
    return vector / norm


def _float_tuple(values: np.ndarray) -> tuple[float, ...]:
    return tuple(float(v) for v in values)


def infer_detector_frame(
    ecal_points: np.ndarray,
    hcal_points: np.ndarray,
    *,
    minimum_center_separation_cm: float = 5.0,
    nominal_ecal_depth_cm: float | None = None,
    nominal_hcal_depth_cm: float | None = None,
) -> DetectorFrame:
    """Infer a truth-free right-handed local frame from ECAL-before-HCAL ordering."""
    ecal = np.asarray(ecal_points, dtype=float)
    hcal = np.asarray(hcal_points, dtype=float)
    if ecal.ndim != 2 or ecal.shape[1] != 3 or hcal.ndim != 2 or hcal.shape[1] != 3:
        raise ValueError("Point arrays must have shape (n_hits, 3)")
    if len(ecal) < 20 or len(hcal) < 20:
        raise ValueError("Too few sampled hits to infer detector frame")
    e_center = np.median(ecal, axis=0)
    h_center = np.median(hcal, axis=0)
    z_axis = _unit(h_center - e_center)
    separation = float(np.linalg.norm(h_center - e_center))
    if separation < minimum_center_separation_cm:
        raise ValueError("ECAL and HCAL centers are not sufficiently separated")
    basis = np.eye(3)
    projections = basis - np.outer(basis @ z_axis, z_axis)
    x_axis = _unit(projections[np.argmax(np.linalg.norm(projections, axis=1))])
    y_axis = _unit(np.cross(z_axis, x_axis))
    x_axis = _unit(np.cross(y_axis, z_axis))
    origin = e_center
    e_local = (ecal - origin) @ np.asarray([x_axis, y_axis, z_axis]).T
    h_local = (hcal - origin) @ np.asarray([x_axis, y_axis, z_axis]).T
    e_mid = float(0.5 * (np.min(e_local[:, 2]) + np.max(e_local[:, 2])))
    h_mid = float(0.5 * (np.min(h_local[:, 2]) + np.max(h_local[:, 2])))
    e_half = (
        0.5 * float(nominal_ecal_depth_cm)
        if nominal_ecal_depth_cm is not None
        else 0.5 * float(np.ptp(e_local[:, 2]))
    )
    h_half = (
        0.5 * float(nominal_hcal_depth_cm)
        if nominal_hcal_depth_cm is not None
        else 0.5 * float(np.ptp(h_local[:, 2]))
    )
    return DetectorFrame(
        _float_tuple(origin),
        _float_tuple(x_axis),
        _float_tuple(y_axis),
        _float_tuple(z_axis),
        (e_mid - e_half, e_mid + e_half),
        (h_mid - h_half, h_mid + h_half),
    )


def validate_frame(frame: DetectorFrame, atol: float = 1e-10) -> None:
    rotation = frame.rotation
    if not np.allclose(rotation @ rotation.T, np.eye(3), atol=atol):
        raise ValueError("Detector frame is not orthonormal")
    if np.linalg.det(rotation) < 0.0:
        raise ValueError("Detector frame is not right-handed")
    if frame.hcal_z_bounds[0] <= frame.ecal_z_bounds[0]:
        raise ValueError("HCAL must lie downstream of ECAL in the locked local frame")
