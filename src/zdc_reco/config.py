from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml


def load_config(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(cfg, dict):
        raise ValueError(f"Configuration must be a mapping: {path}")
    validate_config(cfg)
    return cfg


def validate_config(cfg: dict[str, Any]) -> None:
    focus = cfg["physics"]["focus_energy_gev"]
    support = cfg["physics"]["training_support_gev"]
    if not (support[0] <= focus[0] < focus[1] <= support[1]):
        raise ValueError("focus_energy_gev must be strictly ordered inside training_support_gev")
    fractions = cfg["split"]["fractions"]
    if abs(sum(float(v) for v in fractions.values()) - 1.0) > 1e-12:
        raise ValueError("split fractions must sum to one")
    if cfg["compute"]["planned_spend_limit_usd"] > cfg["compute"]["credit_limit_usd"]:
        raise ValueError("planned spend cannot exceed the credit limit")
    if cfg["features"].get("allow_truth_features", False):
        raise ValueError("Truth features are forbidden")
    target = cfg["training"].get("target")
    allowed_targets = {
        "log1p_kinetic_energy_plus_unit_direction",
        "kinetic_energy_plus_unit_direction",
    }
    if target not in allowed_targets:
        raise ValueError(f"training.target must be one of {sorted(allowed_targets)}")
    if (
        target == "kinetic_energy_plus_unit_direction"
        and cfg["training"]["xgboost"].get("objective") != "reg:squarederror"
    ):
        raise ValueError("Raw kinetic-energy training requires XGBoost reg:squarederror")


def canonical_json_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
