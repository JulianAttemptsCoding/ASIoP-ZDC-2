from __future__ import annotations

import numpy as np


def finite_sample_absolute_residual_quantile(
    true_values: np.ndarray,
    predicted_values: np.ndarray,
    coverage: float,
) -> float:
    """Finite-sample order statistic; interpretation is empirical after validation reuse."""
    if not 0.0 < coverage < 1.0:
        raise ValueError("coverage must lie strictly between zero and one")
    true = np.asarray(true_values, dtype=float)
    predicted = np.asarray(predicted_values, dtype=float)
    residual = np.abs(true - predicted)
    if residual.ndim != 1 or len(residual) == 0 or not np.all(np.isfinite(residual)):
        raise ValueError("residuals must be a nonempty finite vector")
    rank = min(int(np.ceil((len(residual) + 1) * coverage)), len(residual))
    return float(np.partition(residual, rank - 1)[rank - 1])


class EnergyBalancedIsotonicCalibrator:
    """Prespecified monotone point calibrator fitted only after champion freeze."""

    def __init__(self, energy_edges: np.ndarray):
        self.energy_edges = np.asarray(energy_edges, dtype=float)
        self._model = None
        self.prediction_domain_: tuple[float, float] | None = None

    def fit(
        self, predicted_energy: np.ndarray, true_energy: np.ndarray
    ) -> EnergyBalancedIsotonicCalibrator:
        from sklearn.isotonic import IsotonicRegression

        pred = np.asarray(predicted_energy, dtype=float)
        truth = np.asarray(true_energy, dtype=float)
        if pred.shape != truth.shape or pred.ndim != 1 or not np.all(np.isfinite(pred + truth)):
            raise ValueError("calibration arrays must be matching finite vectors")
        bins = np.clip(np.digitize(truth, self.energy_edges[1:-1]), 0, len(self.energy_edges) - 2)
        counts = np.bincount(bins, minlength=len(self.energy_edges) - 1).astype(float)
        if np.any(counts == 0):
            raise ValueError("calibration energy bins must all be populated")
        weight = 1.0 / counts[bins]
        model = IsotonicRegression(increasing=True, out_of_bounds="clip")
        model.fit(pred, truth, sample_weight=weight)
        self._model = model
        self.prediction_domain_ = (float(np.min(pred)), float(np.max(pred)))
        return self

    def predict(self, predicted_energy: np.ndarray) -> np.ndarray:
        if self._model is None:
            raise RuntimeError("calibrator has not been fitted")
        pred = np.asarray(predicted_energy, dtype=float)
        return np.asarray(self._model.predict(pred), dtype=float)

    def clipped_fraction(self, predicted_energy: np.ndarray) -> float:
        if self.prediction_domain_ is None:
            raise RuntimeError("calibrator has not been fitted")
        pred = np.asarray(predicted_energy, dtype=float)
        low, high = self.prediction_domain_
        return float(np.mean((pred < low) | (pred > high)))
