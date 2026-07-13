from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .physics import fourvector_from_kinetic_direction

LOG1P_KINETIC_TARGET = "log1p_kinetic_energy_plus_unit_direction"
RAW_KINETIC_TARGET = "kinetic_energy_plus_unit_direction"

_ENERGY_TARGET_NAMES = {
    LOG1P_KINETIC_TARGET: "log1p_kinetic",
    RAW_KINETIC_TARGET: "kinetic_energy",
}
_CANONICAL_ENERGY_TARGETS = set(_ENERGY_TARGET_NAMES.values())


def energy_target_name(target: str) -> str:
    """Return the persisted energy-head name for a configured training target."""
    if target in _ENERGY_TARGET_NAMES:
        return _ENERGY_TARGET_NAMES[target]
    if target in _CANONICAL_ENERGY_TARGETS:
        return target
    raise ValueError(f"Unsupported constrained-model target: {target}")


def kinetic_from_energy_prediction(prediction: np.ndarray, target: str) -> np.ndarray:
    """Decode a nonnegative kinetic-energy prediction from the energy-head scale."""
    values = np.asarray(prediction, dtype=float)
    name = energy_target_name(target)
    if name == "log1p_kinetic":
        return np.maximum(np.expm1(values), 0.0)
    return np.maximum(values, 0.0)


@dataclass
class ConstrainedRegressor:
    energy_model: object
    direction_models: tuple[object, object, object]
    mass_gev: float
    energy_target: str = "log1p_kinetic"
    max_energy_target: float | None = None

    def predict(self, features: np.ndarray) -> np.ndarray:
        energy_prediction = np.asarray(self.energy_model.predict(features), dtype=float)
        if self.max_energy_target is not None:
            energy_prediction = np.clip(energy_prediction, 0.0, self.max_energy_target)
        kinetic = kinetic_from_energy_prediction(energy_prediction, self.energy_target)
        direction = np.column_stack([model.predict(features) for model in self.direction_models])
        norm = np.linalg.norm(direction, axis=1)
        bad = ~np.isfinite(norm) | (norm <= 1e-12)
        if np.any(bad):
            raise ValueError(f"Predicted direction is invalid for {int(np.sum(bad))} events")
        return fourvector_from_kinetic_direction(kinetic, direction, self.mass_gev)


def make_training_targets(
    kinetic_energy_gev: np.ndarray,
    direction: np.ndarray,
    *,
    target: str = LOG1P_KINETIC_TARGET,
) -> np.ndarray:
    kinetic = np.asarray(kinetic_energy_gev, dtype=float)
    direction = np.asarray(direction, dtype=float)
    if np.any(kinetic < 0.0) or direction.shape != (len(kinetic), 3):
        raise ValueError("Invalid constrained-model targets")
    energy_name = energy_target_name(target)
    energy = np.log1p(kinetic) if energy_name == "log1p_kinetic" else kinetic
    return np.column_stack([energy, direction])


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
    energy_target: str = LOG1P_KINETIC_TARGET,
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
    canonical_energy_target = energy_target_name(energy_target)
    max_energy_target = float(np.nanmax(train_y[:, 0]))
    return ConstrainedRegressor(
        adapters[0],
        tuple(adapters[1:]),
        mass_gev,
        canonical_energy_target,
        max_energy_target,
    )


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
