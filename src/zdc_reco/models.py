from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .physics import fourvector_from_kinetic_direction

TARGET_NAMES = ("log1p_kinetic", "ux", "uy", "uz")


@dataclass
class ConstrainedRegressor:
    energy_model: object
    direction_models: tuple[object, object, object]
    mass_gev: float
    max_log_kinetic: float | None = None

    def predict(self, features: np.ndarray) -> np.ndarray:
        log_kinetic = np.asarray(self.energy_model.predict(features), dtype=float)
        if self.max_log_kinetic is not None:
            log_kinetic = np.clip(log_kinetic, 0.0, self.max_log_kinetic)
        kinetic = np.maximum(np.expm1(log_kinetic), 0.0)
        direction = np.column_stack([model.predict(features) for model in self.direction_models])
        norm = np.linalg.norm(direction, axis=1)
        bad = ~np.isfinite(norm) | (norm <= 1e-12)
        if np.any(bad):
            raise ValueError(f"Predicted direction is invalid for {int(np.sum(bad))} events")
        return fourvector_from_kinetic_direction(kinetic, direction, self.mass_gev)


def make_training_targets(kinetic_energy_gev: np.ndarray, direction: np.ndarray) -> np.ndarray:
    kinetic = np.asarray(kinetic_energy_gev, dtype=float)
    direction = np.asarray(direction, dtype=float)
    if np.any(kinetic < 0.0) or direction.shape != (len(kinetic), 3):
        raise ValueError("Invalid constrained-model targets")
    return np.column_stack([np.log1p(kinetic), direction])


def energy_balanced_weights(
    generator_energy_gev: np.ndarray,
    *,
    edges: np.ndarray,
    focus_range: tuple[float, float],
    shoulder_weight: float,
) -> np.ndarray:
    energy = np.asarray(generator_energy_gev, dtype=float)
    bins = np.clip(np.digitize(energy, edges[1:-1]), 0, len(edges) - 2)
    counts = np.bincount(bins, minlength=len(edges) - 1).astype(float)
    if np.any(counts == 0.0):
        raise ValueError("Cannot balance empty training energy bins")
    weights = 1.0 / counts[bins]
    in_focus = (energy >= focus_range[0]) & (energy <= focus_range[1])
    weights *= np.where(in_focus, 1.0, float(shoulder_weight))
    if np.sum(weights) <= 0.0:
        raise ValueError("Training weights sum to zero")
    return weights / np.mean(weights[weights > 0.0])


def train_xgboost_constrained(
    train_x: np.ndarray,
    train_y: np.ndarray,
    validation_x: np.ndarray,
    validation_y: np.ndarray,
    *,
    train_weight: np.ndarray,
    params: dict,
    max_rounds: int,
    early_stopping_rounds: int,
    mass_gev: float,
) -> ConstrainedRegressor:
    try:
        import xgboost as xgb
    except ImportError as exc:  # pragma: no cover - dependency gate
        raise RuntimeError("Install the project dependencies to train XGBoost") from exc
    common = dict(params)
    common.setdefault("tree_method", "hist")
    common.setdefault("objective", "reg:pseudohubererror")
    common.setdefault("eval_metric", "rmse")
    models = []
    for target_index in range(4):
        dtrain = xgb.DMatrix(train_x, label=train_y[:, target_index], weight=train_weight)
        dval = xgb.DMatrix(validation_x, label=validation_y[:, target_index])
        booster = xgb.train(
            common,
            dtrain,
            num_boost_round=max_rounds,
            evals=[(dval, "validation")],
            early_stopping_rounds=early_stopping_rounds,
            verbose_eval=False,
        )
        models.append(booster)

    class _BoosterAdapter:
        def __init__(self, booster: object):
            self.booster = booster

        def predict(self, values: np.ndarray) -> np.ndarray:
            return self.booster.predict(xgb.DMatrix(values))

    adapters = [_BoosterAdapter(model) for model in models]
    max_log_kinetic = float(np.nanmax(train_y[:, 0]))
    return ConstrainedRegressor(adapters[0], tuple(adapters[1:]), mass_gev, max_log_kinetic)


def empirical_absolute_error_quantiles(
    true_values: np.ndarray,
    predicted_values: np.ndarray,
    coverages: tuple[float, ...] = (0.68, 0.90, 0.95),
) -> dict[float, float]:
    residual = np.abs(np.asarray(true_values) - np.asarray(predicted_values))
    n = len(residual)
    if n == 0:
        raise ValueError("Validation residuals are empty")
    result = {}
    for coverage in coverages:
        if not 0.0 < coverage < 1.0:
            raise ValueError("Coverage must be between zero and one")
        rank = min(int(np.ceil((n + 1) * coverage)), n)
        result[coverage] = float(np.partition(residual, rank - 1)[rank - 1])
    return result
