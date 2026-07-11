from __future__ import annotations

import csv
import hashlib
import json
import pickle
import shutil
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

from .config import canonical_json_hash, load_config
from .contracts import assert_feature_provenance
from .features import build_event_features, feature_manifest
from .geometry import DetectorFrame, validate_frame
from .metrics import evaluate_fourvectors, macro_rms_by_energy_bin, relative_fourvector_error
from .models import energy_balanced_weights, make_training_targets, train_xgboost_constrained
from .physics import (
    EnergyConvention,
    canonical_truth,
    fourvector_from_kinetic_direction,
    unit_direction,
)
from .rootio import inspect_root, resolve_tree, select_exactly_one_neutron, validate_branch_mapping
from .splits import (
    assert_no_duplicate_fingerprint_leakage,
    assert_split_integrity,
    make_grouped_splits,
)


def _imports():
    try:
        import awkward as ak
        import uproot
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("ROOT pipeline stages require uproot and awkward") from exc
    return uproot, ak


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def load_schema(path: str | Path) -> dict[str, Any]:
    schema = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    payload = json.dumps(schema, default=str)
    forbidden = ("auto_strict", "unresolved")
    if any(token in payload for token in forbidden):
        raise ValueError(f"Schema lock contains unresolved token in {path}")
    if schema.get("requires_human_or_documented_signal_unit_resolution"):
        raise ValueError("Hit signal unit resolution is still marked unresolved")
    for section in ("branch_mapping", "truth_energy_convention", "detector_frame"):
        if section not in schema:
            raise ValueError(f"Schema lock is missing {section}")
    scales = schema.get("hit_signal_scale_to_gev", {})
    if any(scales.get(det) is None for det in ("ecal", "hcal")):
        raise ValueError("ECAL/HCAL hit scales must be non-null in schema lock")
    return schema


def frame_from_schema(schema: dict[str, Any]) -> DetectorFrame:
    raw = schema["detector_frame"]
    frame = DetectorFrame(
        origin=tuple(float(v) for v in raw["origin"]),
        x_axis=tuple(float(v) for v in raw["x_axis"]),
        y_axis=tuple(float(v) for v in raw["y_axis"]),
        z_axis=tuple(float(v) for v in raw["z_axis"]),
        ecal_z_bounds=tuple(float(v) for v in raw["ecal_z_bounds"]),
        hcal_z_bounds=tuple(float(v) for v in raw["hcal_z_bounds"]),
    )
    validate_frame(frame)
    return frame


def convention_from_schema(schema: dict[str, Any]) -> EnergyConvention:
    raw = schema["truth_energy_convention"]
    return EnergyConvention(
        semantics=str(raw["semantics"]),
        energy_scale_to_gev=float(raw["energy_scale_to_gev"]),
        momentum_scale_to_gev=float(raw["momentum_scale_to_gev"]),
        median_relative_residual=float(raw["median_relative_residual"]),
        p99_relative_residual=float(raw["p99_relative_residual"]),
        second_best_score_ratio=float(raw["second_best_score_ratio"]),
    )


def file_sha256(path: str | Path, chunk_size: int = 16 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact_sha256(path: str | Path) -> str:
    path = Path(path)
    digest = hashlib.sha256()
    if path.is_file():
        digest.update(path.read_bytes())
    else:
        for item in sorted(p for p in path.rglob("*") if p.is_file()):
            digest.update(str(item.relative_to(path)).replace("\\", "/").encode("utf-8"))
            digest.update(item.read_bytes())
    return digest.hexdigest()


def write_json(path: str | Path, value: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True, default=str), encoding="utf-8")
    tmp.replace(path)


def write_parquet_atomic(frame: pd.DataFrame, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.tmp")
    frame.to_parquet(tmp, index=False)
    tmp.replace(path)


def _safe_generated_rmtree(path: Path, output_root: Path) -> None:
    resolved = path.resolve()
    root = output_root.resolve()
    if root not in resolved.parents and resolved != root:
        raise ValueError(f"Refusing to remove path outside output root: {resolved}")
    if path.exists():
        shutil.rmtree(path)


def _atomic_replace_dir(tmp: Path, final: Path, output_root: Path) -> None:
    if final.exists():
        raise FileExistsError(f"Artifact already exists; refusing to overwrite {final}")
    final.parent.mkdir(parents=True, exist_ok=True)
    tmp.replace(final)


def _event_values(ak: Any, array: Any, index: int) -> np.ndarray:
    return np.asarray(ak.to_numpy(array[index]))


def _hash_array(digest: Any, values: np.ndarray, *, is_float: bool) -> None:
    if is_float:
        arr = np.round(np.asarray(values, dtype=np.float64), 8).astype("<f8", copy=False)
    else:
        arr = np.asarray(values, dtype=np.int64).astype("<i8", copy=False)
    digest.update(np.asarray([len(arr)], dtype="<i8").tobytes())
    digest.update(arr.tobytes())


def detector_event_fingerprint(ak: Any, arrays: Any, mapping: dict[str, str], index: int) -> str:
    digest = hashlib.sha256()
    for logical in (
        "ecal_x",
        "ecal_y",
        "ecal_z",
        "ecal_signal",
        "hcal_x",
        "hcal_y",
        "hcal_z",
        "hcal_signal",
    ):
        _hash_array(digest, _event_values(ak, arrays[mapping[logical]], index), is_float=True)
    for logical in ("ecal_cell_id", "hcal_cell_id", "hcal_layer_id"):
        physical = mapping.get(logical)
        if physical:
            _hash_array(digest, _event_values(ak, arrays[physical], index), is_float=False)
    return digest.hexdigest()


def _jagged_content(ak: Any, array: Any, *, is_float: bool) -> tuple[np.ndarray, np.ndarray]:
    layout = ak.to_layout(array)
    if not hasattr(layout, "offsets") or not hasattr(layout, "content"):
        raise ValueError("Expected a jagged ROOT branch")
    offsets = np.asarray(layout.offsets, dtype=np.int64)
    content = ak.to_numpy(layout.content)
    if is_float:
        encoded = np.round(np.asarray(content, dtype=np.float64), 8).astype("<f8", copy=False)
    else:
        encoded = np.asarray(content, dtype=np.int64).astype("<i8", copy=False)
    return offsets, encoded


def fingerprint_payloads(
    ak: Any, arrays: Any, mapping: dict[str, str]
) -> list[tuple[np.ndarray, np.ndarray]]:
    payloads: list[tuple[np.ndarray, np.ndarray]] = []
    for logical in (
        "ecal_x",
        "ecal_y",
        "ecal_z",
        "ecal_signal",
        "hcal_x",
        "hcal_y",
        "hcal_z",
        "hcal_signal",
    ):
        payloads.append(_jagged_content(ak, arrays[mapping[logical]], is_float=True))
    for logical in ("ecal_cell_id", "hcal_cell_id", "hcal_layer_id"):
        physical = mapping.get(logical)
        if physical:
            payloads.append(_jagged_content(ak, arrays[physical], is_float=False))
    return payloads


def detector_fingerprint_from_payloads(
    payloads: list[tuple[np.ndarray, np.ndarray]], index: int
) -> str:
    digest = hashlib.sha256()
    for offsets, encoded in payloads:
        start = int(offsets[index])
        stop = int(offsets[index + 1])
        digest.update(np.asarray([stop - start], dtype="<i8").tobytes())
        digest.update(encoded[start:stop].tobytes())
    return digest.hexdigest()


def focus_edges() -> np.ndarray:
    return np.asarray([50.0, 75.0, 100.0, 125.0, 150.0, 175.0, 200.0, 225.0, 250.0])


def focus_mask(values: pd.Series | np.ndarray) -> np.ndarray:
    energy = np.asarray(values, dtype=float)
    return (energy >= 50.0) & (energy <= 250.0)


def build_targets(
    *,
    data: str | Path,
    config: str | Path,
    schema_path: str | Path,
    output_dir: str | Path,
    limit: int | None = None,
) -> dict[str, Any]:
    uproot, ak = _imports()
    cfg = load_config(config)
    schema = load_schema(schema_path)
    convention = convention_from_schema(schema)
    output_dir = Path(output_dir)
    data_dir = output_dir / "data"
    reports_dir = output_dir / "reports"
    targets_path = data_dir / "targets.parquet"
    if targets_path.exists():
        return {
            "status": "reused",
            "path": str(targets_path),
            "sha256": artifact_sha256(targets_path),
        }

    data_path = Path(data).resolve()
    rows: list[dict[str, Any]] = []
    with uproot.open(data_path) as root_file:
        tree_name, tree = resolve_tree(root_file, schema["tree_name"])
        mapping = validate_branch_mapping(tree, schema["branch_mapping"])
        branches = list(dict.fromkeys(mapping.values()))
        for arrays, report in tree.iterate(
            branches,
            library="ak",
            step_size=cfg["data"]["step_size"],
            report=True,
        ):
            start = int(report.start)
            truth_energy, truth_momentum = select_exactly_one_neutron(
                arrays[mapping["truth_pdg"]],
                arrays[mapping["truth_energy"]],
                arrays[mapping["truth_px"]],
                arrays[mapping["truth_py"]],
                arrays[mapping["truth_pz"]],
                neutron_pdg=int(cfg["physics"]["particle_pdg"]),
                ak=ak,
            )
            truth = canonical_truth(
                truth_energy,
                truth_momentum,
                convention,
                mass_gev=float(cfg["physics"]["neutron_mass_gev"]),
                min_direction_p_gev=float(cfg["physics"]["direction_valid_min_p_gev"]),
            )
            ecal_sum = ak.to_numpy(ak.sum(arrays[mapping["ecal_signal"]], axis=1)) * float(
                schema["hit_signal_scale_to_gev"]["ecal"]
            )
            hcal_sum = ak.to_numpy(ak.sum(arrays[mapping["hcal_signal"]], axis=1)) * float(
                schema["hit_signal_scale_to_gev"]["hcal"]
            )
            ecal_hits = ak.to_numpy(ak.num(arrays[mapping["ecal_signal"]]))
            hcal_hits = ak.to_numpy(ak.num(arrays[mapping["hcal_signal"]]))
            payloads = fingerprint_payloads(ak, arrays, mapping)
            for i in range(len(truth_energy)):
                event_index = start + i
                if limit is not None and event_index >= limit:
                    break
                fingerprint = detector_fingerprint_from_payloads(payloads, i)
                event_uid = f"{tree_name}:{event_index:09d}"
                row = {
                    "event_uid": event_uid,
                    "event_index": event_index,
                    "source_file": data_path.name,
                    "group_uid": f"detector:{fingerprint}",
                    "detector_fingerprint": fingerprint,
                    "ecal_hit_count": int(ecal_hits[i]),
                    "hcal_hit_count": int(hcal_hits[i]),
                    "ecal_signal_sum_gev": float(ecal_sum[i]),
                    "hcal_signal_sum_gev": float(hcal_sum[i]),
                    "visible_signal_gev": float(ecal_sum[i] + hcal_sum[i]),
                    "no_detector_signal": bool((ecal_sum[i] + hcal_sum[i]) <= 1e-12),
                }
                for key, value in truth.items():
                    item = value[i]
                    row[key] = bool(item) if key == "direction_valid" else float(item)
                rows.append(row)
            if limit is not None and len(rows) >= limit:
                break

    frame = pd.DataFrame(rows)
    if frame["event_uid"].duplicated().any():
        raise ValueError("event_uid is not unique after target build")
    write_parquet_atomic(frame, targets_path)
    duplicate_counts = frame["detector_fingerprint"].value_counts()
    duplicate_report = {
        "events": int(len(frame)),
        "unique_detector_fingerprints": int(duplicate_counts.size),
        "duplicate_fingerprint_groups": int((duplicate_counts > 1).sum()),
        "duplicate_events": int(duplicate_counts[duplicate_counts > 1].sum()),
        "group_policy": (
            "No run/seed/source-group branch is present. group_uid is detector "
            "fingerprint so exact duplicate detector observations cannot cross splits; "
            "unique fingerprints act as event-level independent groups."
        ),
    }
    reports_dir.mkdir(parents=True, exist_ok=True)
    write_json(reports_dir / "duplicate_report.json", duplicate_report)
    write_json(
        output_dir / "preflight" / "data_fingerprint.json",
        {
            "path": str(data_path),
            "size_bytes": data_path.stat().st_size,
            "sha256": schema.get("data_sha256") or file_sha256(data_path),
            "tree_name": schema["tree_name"],
            "entries": int(len(frame)),
            "created_utc": utc_now(),
        },
    )
    return {
        "status": "built",
        "path": str(targets_path),
        "rows": int(len(frame)),
        "sha256": artifact_sha256(targets_path),
    }


def make_splits(
    *,
    config: str | Path,
    output_dir: str | Path,
) -> dict[str, Any]:
    cfg = load_config(config)
    output_dir = Path(output_dir)
    targets_path = output_dir / "data" / "targets.parquet"
    splits_path = output_dir / "data" / "splits.parquet"
    if splits_path.exists():
        return {
            "status": "reused",
            "path": str(splits_path),
            "sha256": artifact_sha256(splits_path),
        }
    targets = pd.read_parquet(targets_path)
    split = make_grouped_splits(
        targets,
        seed=int(cfg["project"]["seed"]),
        energy_edges=list(cfg["split"]["stratify_energy_edges_gev"]),
        theta_bins=int(cfg["split"]["theta_bins"]),
        phi_bins=int(cfg["split"]["phi_bins"]),
    )
    frame = targets[
        ["event_uid", "group_uid", "detector_fingerprint", "generator_energy_gev"]
    ].copy()
    frame["split"] = split.to_numpy()
    assert_split_integrity(frame)
    assert_no_duplicate_fingerprint_leakage(frame)
    write_parquet_atomic(frame[["event_uid", "split"]], splits_path)
    report = {
        "rows": int(len(frame)),
        "split_counts": {str(k): int(v) for k, v in frame["split"].value_counts().items()},
        "focus_counts": {
            str(k): int(v)
            for k, v in frame.loc[focus_mask(frame["generator_energy_gev"]), "split"]
            .value_counts()
            .items()
        },
        "shoulder_counts": {
            str(k): int(v)
            for k, v in frame.loc[~focus_mask(frame["generator_energy_gev"]), "split"]
            .value_counts()
            .items()
        },
        "group_policy": (
            "group_uid comes from detector fingerprint because no run/seed branch exists."
        ),
        "split_sha256": artifact_sha256(splits_path),
    }
    write_json(output_dir / "reports" / "split_report.json", report)
    return {"status": "built", "path": str(splits_path), **report}


def build_features(
    *,
    data: str | Path,
    config: str | Path,
    schema_path: str | Path,
    output_dir: str | Path,
    limit: int | None = None,
) -> dict[str, Any]:
    uproot, ak = _imports()
    cfg = load_config(config)
    schema = load_schema(schema_path)
    output_dir = Path(output_dir)
    final_dir = output_dir / "data" / "features_manifest.parquet"
    if final_dir.exists():
        return {"status": "reused", "path": str(final_dir), "sha256": artifact_sha256(final_dir)}
    tmp_dir = output_dir / "data" / f".features_tmp_{int(time.time())}"
    _safe_generated_rmtree(tmp_dir, output_dir)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    targets = pd.read_parquet(
        output_dir / "data" / "targets.parquet", columns=["event_uid", "event_index"]
    )
    event_uids = targets.sort_values("event_index")["event_uid"].to_numpy()
    frame = frame_from_schema(schema)
    mapping = schema["branch_mapping"]
    position_scale = float(schema.get("position_scale_to_cm", 1.0))
    ecal_signal_scale = float(schema["hit_signal_scale_to_gev"]["ecal"])
    hcal_signal_scale = float(schema["hit_signal_scale_to_gev"]["hcal"])
    branches = [
        mapping["ecal_x"],
        mapping["ecal_y"],
        mapping["ecal_z"],
        mapping["ecal_signal"],
        mapping["hcal_x"],
        mapping["hcal_y"],
        mapping["hcal_z"],
        mapping["hcal_signal"],
    ]
    feature_names: list[str] | None = None
    total_rows = 0
    part_index = 0
    data_path = Path(data).resolve()
    with uproot.open(data_path) as root_file:
        _, tree = resolve_tree(root_file, schema["tree_name"])
        for arrays, report in tree.iterate(
            branches,
            library="ak",
            step_size=cfg["data"]["step_size"],
            report=True,
        ):
            start = int(report.start)
            rows: list[dict[str, Any]] = []
            events = len(arrays[mapping["ecal_signal"]])
            for i in range(events):
                event_index = start + i
                if limit is not None and event_index >= limit:
                    break
                features = build_event_features(
                    ecal_x=_event_values(ak, arrays[mapping["ecal_x"]], i) * position_scale,
                    ecal_y=_event_values(ak, arrays[mapping["ecal_y"]], i) * position_scale,
                    ecal_z=_event_values(ak, arrays[mapping["ecal_z"]], i) * position_scale,
                    ecal_signal_gev=_event_values(ak, arrays[mapping["ecal_signal"]], i)
                    * ecal_signal_scale,
                    hcal_x=_event_values(ak, arrays[mapping["hcal_x"]], i) * position_scale,
                    hcal_y=_event_values(ak, arrays[mapping["hcal_y"]], i) * position_scale,
                    hcal_z=_event_values(ak, arrays[mapping["hcal_z"]], i) * position_scale,
                    hcal_signal_gev=_event_values(ak, arrays[mapping["hcal_signal"]], i)
                    * hcal_signal_scale,
                    frame=frame,
                    ecal_threshold_gev=float(cfg["data"]["hit_threshold_gev"]["ecal"]),
                    hcal_threshold_gev=float(cfg["data"]["hit_threshold_gev"]["hcal"]),
                    ecal_depth_groups=int(cfg["features"]["ecal_depth_groups"]),
                    hcal_depth_groups=int(cfg["features"]["hcal_depth_groups"]),
                    top_hit_counts=tuple(int(v) for v in cfg["features"]["top_hit_counts"]),
                    density_edges_gev=tuple(
                        float(v) for v in cfg["features"]["hit_energy_density_edges_gev"]
                    ),
                )
                if feature_names is None:
                    feature_names = list(features)
                    manifest = feature_manifest(feature_names)
                    assert_feature_provenance(manifest)
                    with (output_dir / "reports" / "feature_manifest.csv").open(
                        "w", newline="", encoding="utf-8"
                    ) as handle:
                        writer = csv.DictWriter(
                            handle, fieldnames=["feature", "source_kind", "source_branches"]
                        )
                        writer.writeheader()
                        for row in manifest:
                            writer.writerow(
                                {
                                    "feature": row["feature"],
                                    "source_kind": row["source_kind"],
                                    "source_branches": json.dumps(row["source_branches"]),
                                }
                            )
                elif list(features) != feature_names:
                    raise ValueError("Feature columns changed during feature build")
                row = {"event_uid": str(event_uids[event_index])}
                row.update(features)
                rows.append(row)
            if rows:
                pd.DataFrame(rows).to_parquet(
                    tmp_dir / f"part-{part_index:05d}.parquet", index=False
                )
                total_rows += len(rows)
                part_index += 1
            if limit is not None and total_rows >= limit:
                break
    _atomic_replace_dir(tmp_dir, final_dir, output_dir)
    report = {
        "rows": int(total_rows),
        "feature_count": int(len(feature_names or [])),
        "path": str(final_dir),
        "sha256": artifact_sha256(final_dir),
    }
    write_json(output_dir / "reports" / "feature_build_report.json", report)
    return {"status": "built", **report}


def validate_schema_command(schema_path: str | Path) -> dict[str, Any]:
    schema = load_schema(schema_path)
    frame_from_schema(schema)
    return {
        "status": "ok",
        "schema": str(Path(schema_path)),
        "schema_sha256": file_sha256(schema_path),
        "tree_name": schema["tree_name"],
    }


def _load_model_table(output_dir: Path) -> tuple[pd.DataFrame, list[str]]:
    features = pd.read_parquet(output_dir / "data" / "features_manifest.parquet")
    manifest = pd.read_csv(output_dir / "reports" / "feature_manifest.csv")
    feature_cols = manifest["feature"].astype(str).tolist()
    targets = pd.read_parquet(output_dir / "data" / "targets.parquet")
    duplicate_target_cols = [col for col in targets.columns if col in set(feature_cols)]
    if duplicate_target_cols:
        targets = targets.drop(columns=duplicate_target_cols)
    splits = pd.read_parquet(output_dir / "data" / "splits.parquet")
    table = features.merge(targets, on="event_uid", validate="one_to_one").merge(
        splits, on="event_uid", validate="one_to_one"
    )
    if table[feature_cols].isna().any().any():
        raise ValueError("Feature table contains NaN")
    return table, feature_cols


def _true_fourvector(frame: pd.DataFrame) -> np.ndarray:
    return frame[["energy_true_gev", "px_true_gev", "py_true_gev", "pz_true_gev"]].to_numpy(float)


def _pred_frame(base: pd.DataFrame, model_id: str, pred: np.ndarray) -> pd.DataFrame:
    out = base[["event_uid", "split", "generator_energy_gev"]].copy()
    out["model_id"] = model_id
    out["E_total_hat"] = pred[:, 0]
    out["px_hat"] = pred[:, 1]
    out["py_hat"] = pred[:, 2]
    out["pz_hat"] = pred[:, 3]
    return out


def _score_predictions(base: pd.DataFrame, pred: np.ndarray, mass_gev: float) -> dict[str, float]:
    true = _true_fourvector(base)
    errors = relative_fourvector_error(true, pred)
    mask = focus_mask(base["generator_energy_gev"])
    metrics = evaluate_fourvectors(true[mask], pred[mask], mass_gev=mass_gev)
    metrics["macro_rms_relative_fourvector_error"] = macro_rms_by_energy_bin(
        errors[mask], base.loc[mask, "generator_energy_gev"].to_numpy(float), focus_edges()
    )
    metrics["focus_events"] = int(mask.sum())
    return metrics


def _metrics_are_deployable(metrics: dict[str, float]) -> bool:
    numeric = [float(value) for value in metrics.values() if isinstance(value, (int, float))]
    if not numeric or not np.all(np.isfinite(numeric)):
        return False
    return (
        metrics["macro_rms_relative_fourvector_error"] < 10.0
        and metrics["energy_relative_rmse"] < 10.0
        and abs(metrics["energy_response_mean"]) < 10.0
        and metrics["mass_shell_residual_abs_max_gev2"] < 1e-4
    )


def _save_pickle(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        pickle.dump(value, handle)


def train_baselines(*, config: str | Path, schema_path: str | Path, output_dir: str | Path) -> dict:
    from sklearn.linear_model import LinearRegression, Ridge
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    cfg = load_config(config)
    schema = load_schema(schema_path)
    mass = float(cfg["physics"]["neutron_mass_gev"])
    output_dir = Path(output_dir)
    table, feature_cols = _load_model_table(output_dir)
    train = table["split"].eq("train")
    validation = table["split"].eq("validation")
    leaderboard_rows = []

    x_b0 = table[["ecal_total_signal_gev", "hcal_total_signal_gev"]].to_numpy(float)
    y_k = table["kinetic_energy_true_gev"].to_numpy(float)
    b0 = LinearRegression(positive=True)
    b0.fit(x_b0[train], y_k[train])
    direction = table[["all_axis_u_x", "all_axis_u_y", "all_axis_u_z"]].to_numpy(float)
    pred_b0 = fourvector_from_kinetic_direction(np.maximum(b0.predict(x_b0), 0.0), direction, mass)
    model_id = "B0_visible_sum_axis"
    model_dir = output_dir / "models" / model_id
    _save_pickle(
        model_dir / "model.pkl",
        {
            "model": b0,
            "feature_cols": ["ecal_total_signal_gev", "hcal_total_signal_gev"],
            "direction_cols": ["all_axis_u_x", "all_axis_u_y", "all_axis_u_z"],
            "prediction_kind": "visible_sum_axis",
        },
    )
    val_pred = _pred_frame(table.loc[validation], model_id, pred_b0[validation])
    write_parquet_atomic(val_pred, output_dir / "predictions" / f"validation_{model_id}.parquet")
    metrics = _score_predictions(table.loc[validation], pred_b0[validation], mass)
    leaderboard_rows.append(
        {"model_id": model_id, "deployable": _metrics_are_deployable(metrics), **metrics}
    )

    y = make_training_targets(
        table["kinetic_energy_true_gev"].to_numpy(float),
        table[["ux_true", "uy_true", "uz_true"]].to_numpy(float),
    )
    b1 = make_pipeline(StandardScaler(), Ridge(alpha=1.0))
    x = table[feature_cols].to_numpy(float)
    b1.fit(x[train], y[train])
    raw = b1.predict(x)
    pred_b1 = fourvector_from_kinetic_direction(
        np.maximum(np.expm1(raw[:, 0]), 0.0), raw[:, 1:], mass
    )
    model_id = "B1_ridge_constrained"
    model_dir = output_dir / "models" / model_id
    _save_pickle(
        model_dir / "model.pkl",
        {"model": b1, "feature_cols": feature_cols, "prediction_kind": "kinetic_direction"},
    )
    val_pred = _pred_frame(table.loc[validation], model_id, pred_b1[validation])
    write_parquet_atomic(val_pred, output_dir / "predictions" / f"validation_{model_id}.parquet")
    metrics = _score_predictions(table.loc[validation], pred_b1[validation], mass)
    leaderboard_rows.append(
        {"model_id": model_id, "deployable": _metrics_are_deployable(metrics), **metrics}
    )

    m2 = make_pipeline(StandardScaler(), Ridge(alpha=1.0))
    y_direct = _true_fourvector(table)
    m2.fit(x[train], y_direct[train])
    raw_direct = m2.predict(x)
    direction_direct, valid = unit_direction(raw_direct[:, 1:])
    direction_direct[~valid] = np.asarray([0.0, 0.0, 1.0])
    kinetic_direct = np.maximum(
        np.sqrt(np.sum(raw_direct[:, 1:] ** 2, axis=1) + mass**2) - mass, 0.0
    )
    pred_m2 = fourvector_from_kinetic_direction(kinetic_direct, direction_direct, mass)
    model_id = "M2_ridge_direct_projected"
    model_dir = output_dir / "models" / model_id
    _save_pickle(
        model_dir / "model.pkl",
        {
            "model": m2,
            "feature_cols": feature_cols,
            "diagnostic": True,
            "prediction_kind": "direct_fourvector_projected",
        },
    )
    val_pred = _pred_frame(table.loc[validation], model_id, pred_m2[validation])
    write_parquet_atomic(val_pred, output_dir / "predictions" / f"validation_{model_id}.parquet")
    metrics = _score_predictions(table.loc[validation], pred_m2[validation], mass)
    leaderboard_rows.append({"model_id": model_id, "deployable": False, **metrics})

    existing = output_dir / "metrics" / "validation_leaderboard.csv"
    leaderboard = pd.DataFrame(leaderboard_rows)
    if existing.exists():
        prior = pd.read_csv(existing)
        prior = prior[~prior["model_id"].isin(set(leaderboard["model_id"]))]
        leaderboard = pd.concat([prior, leaderboard], ignore_index=True)
    existing.parent.mkdir(parents=True, exist_ok=True)
    leaderboard.to_csv(existing, index=False)
    write_json(
        output_dir / "models" / "baseline_training_report.json",
        {
            "models": leaderboard_rows,
            "feature_manifest_hash": artifact_sha256(
                output_dir / "reports" / "feature_manifest.csv"
            ),
            "schema_hash": file_sha256(schema_path),
            "config_hash": canonical_json_hash(cfg),
            "schema": schema,
        },
    )
    return {"status": "built", "models": [row["model_id"] for row in leaderboard_rows]}


def _save_xgb_model(
    model: Any, model_dir: Path, feature_cols: list[str], metadata: dict[str, Any]
) -> None:
    model_dir.mkdir(parents=True, exist_ok=True)
    boosters = [
        model.energy_model.booster,
        model.direction_models[0].booster,
        model.direction_models[1].booster,
        model.direction_models[2].booster,
    ]
    for name, booster in zip(("log1p_kinetic", "ux", "uy", "uz"), boosters, strict=True):
        booster.save_model(model_dir / f"{name}.json")
        write_json(model_dir / "metadata.json", {"feature_cols": feature_cols, **metadata})


def _markdown_table(frame: pd.DataFrame) -> str:
    columns = [str(col) for col in frame.columns]
    rows = [["" if pd.isna(value) else str(value) for value in row] for row in frame.to_numpy()]
    widths = [
        max(len(columns[i]), *(len(row[i]) for row in rows)) if rows else len(columns[i])
        for i in range(len(columns))
    ]
    header = "| " + " | ".join(col.ljust(widths[i]) for i, col in enumerate(columns)) + " |"
    sep = "| " + " | ".join("-" * widths[i] for i in range(len(columns))) + " |"
    body = [
        "| " + " | ".join(row[i].ljust(widths[i]) for i in range(len(columns))) + " |"
        for row in rows
    ]
    return "\n".join([header, sep, *body])


def train_xgb(*, config: str | Path, schema_path: str | Path, output_dir: str | Path) -> dict:
    cfg = load_config(config)
    load_schema(schema_path)
    mass = float(cfg["physics"]["neutron_mass_gev"])
    output_dir = Path(output_dir)
    table, feature_cols = _load_model_table(output_dir)
    validation = table["split"].eq("validation")
    validation_focus = validation & focus_mask(table["generator_energy_gev"])
    x = table[feature_cols].to_numpy(float)
    y = make_training_targets(
        table["kinetic_energy_true_gev"].to_numpy(float),
        table[["ux_true", "uy_true", "uz_true"]].to_numpy(float),
    )
    params = dict(cfg["training"]["xgboost"])
    max_rounds = int(params.pop("max_rounds"))
    early = int(params.pop("early_stopping_rounds"))
    params.pop("max_first_sweep_trials", None)
    rows = []
    for candidate in cfg["training"]["support_candidates"]:
        name = str(candidate["name"])
        train_mask = table["split"].eq("train")
        shoulder_weight = float(candidate["shoulder_weight"])
        if name == "focus_only":
            train_mask &= focus_mask(table["generator_energy_gev"])
            edges = focus_edges()
        else:
            edges = np.asarray(cfg["split"]["stratify_energy_edges_gev"], dtype=float)
        weights = energy_balanced_weights(
            table.loc[train_mask, "generator_energy_gev"].to_numpy(float),
            edges=edges,
            focus_range=(50.0, 250.0),
            shoulder_weight=shoulder_weight,
        )
        started = time.time()
        model = train_xgboost_constrained(
            x[train_mask],
            y[train_mask],
            x[validation_focus],
            y[validation_focus],
            train_weight=weights,
            params=params,
            max_rounds=max_rounds,
            early_stopping_rounds=early,
            mass_gev=mass,
        )
        pred = model.predict(x[validation])
        model_id = f"M1_xgb_{name}"
        model_dir = output_dir / "models" / model_id
        _save_xgb_model(
            model,
            model_dir,
            feature_cols,
            {
                "model_id": model_id,
                "prediction_kind": "kinetic_direction",
                "max_log_kinetic": model.max_log_kinetic,
                "support_candidate": candidate,
                "train_rows": int(train_mask.sum()),
                "validation_focus_rows": int(validation_focus.sum()),
                "wall_time_seconds": time.time() - started,
                "params": params,
            },
        )
        write_parquet_atomic(
            _pred_frame(table.loc[validation], model_id, pred),
            output_dir / "predictions" / f"validation_{model_id}.parquet",
        )
        metrics = _score_predictions(table.loc[validation], pred, mass)
        rows.append(
            {"model_id": model_id, "deployable": _metrics_are_deployable(metrics), **metrics}
        )
    leaderboard_path = output_dir / "metrics" / "validation_leaderboard.csv"
    leaderboard = pd.DataFrame(rows)
    if leaderboard_path.exists():
        prior = pd.read_csv(leaderboard_path)
        prior = prior[~prior["model_id"].isin(set(leaderboard["model_id"]))]
        leaderboard = pd.concat([prior, leaderboard], ignore_index=True)
    leaderboard_path.parent.mkdir(parents=True, exist_ok=True)
    leaderboard.to_csv(leaderboard_path, index=False)
    return {"status": "built", "models": [row["model_id"] for row in rows]}


def select_model(*, output_dir: str | Path) -> dict[str, Any]:
    output_dir = Path(output_dir)
    leaderboard = pd.read_csv(output_dir / "metrics" / "validation_leaderboard.csv")
    deployable = leaderboard[leaderboard["deployable"].astype(bool)].copy()
    if deployable.empty:
        raise ValueError("No deployable validation candidates are available")
    deployable = deployable.sort_values("macro_rms_relative_fourvector_error")
    champion = deployable.iloc[0].to_dict()
    champion_id = str(champion["model_id"])
    decision = {
        "created_utc": utc_now(),
        "champion_model_id": champion_id,
        "ranking_metric": "macro_rms_relative_fourvector_error on validation focus 50-250 GeV",
        "tuning_is_over": True,
        "material_slice_regression_rule": (
            "Reject a candidate before test if required validation slices show a larger than 0.5% "
            "relative regression in primary score without compensating physics justification."
        ),
        "leaderboard": leaderboard.to_dict(orient="records"),
        "leaderboard_sha256": artifact_sha256(
            output_dir / "metrics" / "validation_leaderboard.csv"
        ),
    }
    write_json(output_dir / "reports" / "champion.json", decision)
    markdown = [
        "# Selection decision",
        "",
        f"Created UTC: {decision['created_utc']}",
        "",
        f"Champion: `{champion_id}`",
        "",
        "Ranking metric: validation-focus macro RMS relative four-vector error.",
        "",
        "Tuning is over before calibration or test access.",
        "",
        "## Validation leaderboard",
        "",
        _markdown_table(leaderboard),
        "",
        "## Prespecified material slice rule",
        "",
        decision["material_slice_regression_rule"],
    ]
    path = output_dir / "reports" / "selection_decision.md"
    path.write_text("\n".join(markdown), encoding="utf-8")
    return {
        "status": "selected",
        "champion_model_id": champion_id,
        "selection_sha256": file_sha256(path),
    }


def calibrate(*, config: str | Path, output_dir: str | Path) -> dict[str, Any]:
    cfg = load_config(config)
    output_dir = Path(output_dir)
    champion = json.loads((output_dir / "reports" / "champion.json").read_text(encoding="utf-8"))
    model_id = champion["champion_model_id"]
    mass = float(cfg["physics"]["neutron_mass_gev"])
    pred = pd.read_parquet(output_dir / "predictions" / f"validation_{model_id}.parquet")
    targets = pd.read_parquet(output_dir / "data" / "targets.parquet")
    frame = pred.merge(targets, on="event_uid", validate="one_to_one")
    mask = focus_mask(frame["generator_energy_gev_x"])
    x = frame.loc[mask, "E_total_hat"].to_numpy(float)
    y = frame.loc[mask, "energy_true_gev"].to_numpy(float)
    slope, intercept = np.polyfit(x, y, 1)
    raw_pred = frame[["E_total_hat", "px_hat", "py_hat", "pz_hat"]].to_numpy(float)
    direction, valid = unit_direction(raw_pred[:, 1:])
    direction[~valid] = np.asarray([0.0, 0.0, 1.0])
    corrected_total = np.maximum(float(slope) * raw_pred[:, 0] + float(intercept), mass)
    corrected = fourvector_from_kinetic_direction(corrected_total - mass, direction, mass)
    out = pred.copy()
    out[["E_total_hat", "px_hat", "py_hat", "pz_hat"]] = corrected
    path = output_dir / "predictions" / f"validation_calibrated_{model_id}.parquet"
    write_parquet_atomic(out, path)
    residual = np.abs(frame["energy_true_gev"].to_numpy(float) - corrected[:, 0])
    quantiles = {
        str(c): float(np.quantile(residual[mask], c))
        for c in cfg["uncertainty"]["marginal_coverages"]
    }
    calibration = {
        "created_utc": utc_now(),
        "model_id": model_id,
        "source": "validation focus reused after model selection; empirical only",
        "energy_response_slope": float(slope),
        "energy_response_intercept": float(intercept),
        "energy_abs_error_quantiles_gev": quantiles,
        "validation_calibrated_prediction_sha256": artifact_sha256(path),
    }
    write_json(output_dir / "models" / model_id / "calibration.json", calibration)
    return {"status": "calibrated", "model_id": model_id, "calibration": calibration}


def unlock_test(*, output_dir: str | Path) -> dict[str, Any]:
    output_dir = Path(output_dir)
    path = output_dir / "reports" / "test_unlock.json"
    if path.exists():
        return {"status": "already_unlocked", "path": str(path), "sha256": file_sha256(path)}
    champion = json.loads((output_dir / "reports" / "champion.json").read_text(encoding="utf-8"))
    model_id = champion["champion_model_id"]
    required = [
        output_dir / "reports" / "selection_decision.md",
        output_dir / "models" / model_id / "calibration.json",
        output_dir / "metrics" / "validation_leaderboard.csv",
    ]
    for item in required:
        if not item.exists():
            raise FileNotFoundError(f"Cannot unlock test before artifact exists: {item}")
    record = {
        "created_utc": utc_now(),
        "champion_model_id": model_id,
        "selection_decision_hash": file_sha256(required[0]),
        "calibration_hash": file_sha256(required[1]),
        "validation_leaderboard_hash": file_sha256(required[2]),
        "test_query": "split == 'test' and 50 <= generator_energy_gev <= 250",
        "statement": "No further tuning is allowed after this unlock.",
    }
    write_json(path, record)
    return {"status": "unlocked", "path": str(path), "sha256": file_sha256(path)}


def _load_prediction_model(output_dir: Path, model_id: str) -> tuple[Any, dict[str, Any], str]:
    model_dir = output_dir / "models" / model_id
    if (model_dir / "model.pkl").exists():
        with (model_dir / "model.pkl").open("rb") as handle:
            payload = pickle.load(handle)
        return payload["model"], payload, "pickle"
    metadata = json.loads((model_dir / "metadata.json").read_text(encoding="utf-8"))
    import xgboost as xgb

    boosters = []
    for name in ("log1p_kinetic", "ux", "uy", "uz"):
        booster = xgb.Booster()
        booster.load_model(model_dir / f"{name}.json")
        boosters.append(booster)
    return boosters, metadata, "xgb"


def _predict_loaded(
    model: Any, metadata: dict[str, Any], kind: str, frame: pd.DataFrame, mass: float
) -> np.ndarray:
    feature_cols = list(metadata["feature_cols"])
    x = frame[feature_cols].to_numpy(float)
    if kind == "pickle":
        prediction_kind = str(metadata.get("prediction_kind", "kinetic_direction"))
        raw = model.predict(x)
        if prediction_kind == "visible_sum_axis":
            direction_cols = list(metadata["direction_cols"])
            direction = frame[direction_cols].to_numpy(float)
            return fourvector_from_kinetic_direction(np.maximum(raw, 0.0), direction, mass)
        if raw.ndim == 1:
            raise ValueError(f"Loaded {prediction_kind} model does not contain enough outputs")
        if prediction_kind == "direct_fourvector_projected":
            direction, valid = unit_direction(raw[:, 1:])
            direction[~valid] = np.asarray([0.0, 0.0, 1.0])
            kinetic = np.sqrt(np.sum(raw[:, 1:] ** 2, axis=1) + mass**2) - mass
            return fourvector_from_kinetic_direction(kinetic, direction, mass)
        if prediction_kind != "kinetic_direction":
            raise ValueError(f"Unknown pickle prediction_kind: {prediction_kind}")
        return fourvector_from_kinetic_direction(
            np.maximum(np.expm1(raw[:, 0]), 0.0), raw[:, 1:], mass
        )
    import xgboost as xgb

    dmatrix = xgb.DMatrix(x)
    raw = np.column_stack([booster.predict(dmatrix) for booster in model])
    max_log_kinetic = metadata.get("max_log_kinetic")
    log_kinetic = raw[:, 0]
    if max_log_kinetic is not None:
        log_kinetic = np.clip(log_kinetic, 0.0, float(max_log_kinetic))
    kinetic = np.maximum(np.expm1(log_kinetic), 0.0)
    return fourvector_from_kinetic_direction(kinetic, raw[:, 1:], mass)


def evaluate_test(*, config: str | Path, output_dir: str | Path) -> dict[str, Any]:
    cfg = load_config(config)
    output_dir = Path(output_dir)
    unlock = output_dir / "reports" / "test_unlock.json"
    if not unlock.exists():
        raise FileNotFoundError("Refusing to read test rows before test_unlock.json exists")
    champion = json.loads((output_dir / "reports" / "champion.json").read_text(encoding="utf-8"))
    model_id = champion["champion_model_id"]
    mass = float(cfg["physics"]["neutron_mass_gev"])
    table, _ = _load_model_table(output_dir)
    test = table["split"].eq("test")
    model, metadata, kind = _load_prediction_model(output_dir, model_id)
    pred = _predict_loaded(model, metadata, kind, table.loc[test], mass)
    calibration = json.loads(
        (output_dir / "models" / model_id / "calibration.json").read_text(encoding="utf-8")
    )
    direction, valid = unit_direction(pred[:, 1:])
    direction[~valid] = np.asarray([0.0, 0.0, 1.0])
    corrected_total = np.maximum(
        calibration["energy_response_slope"] * pred[:, 0]
        + calibration["energy_response_intercept"],
        mass,
    )
    corrected = fourvector_from_kinetic_direction(corrected_total - mass, direction, mass)
    pred_frame = _pred_frame(table.loc[test], model_id, corrected)
    pred_path = output_dir / "predictions" / f"test_{model_id}.parquet"
    write_parquet_atomic(pred_frame, pred_path)
    metrics = _score_predictions(table.loc[test], corrected, mass)
    write_json(output_dir / "metrics" / "focus_test_metrics.json", metrics)
    coverage = {}
    abs_energy_error = np.abs(table.loc[test, "energy_true_gev"].to_numpy(float) - corrected[:, 0])
    focus = focus_mask(table.loc[test, "generator_energy_gev"])
    for cov, width in calibration["energy_abs_error_quantiles_gev"].items():
        coverage[cov] = float(np.mean(abs_energy_error[focus] <= float(width)))
    write_json(output_dir / "metrics" / "empirical_interval_coverage.json", coverage)
    return {"status": "evaluated", "model_id": model_id, "metrics": metrics}


def plot_outputs(*, output_dir: str | Path) -> dict[str, Any]:
    import matplotlib.pyplot as plt

    output_dir = Path(output_dir)
    metrics_path = output_dir / "metrics" / "focus_test_metrics.json"
    if not metrics_path.exists():
        raise FileNotFoundError("Run evaluate-test before plot")
    champion = json.loads((output_dir / "reports" / "champion.json").read_text(encoding="utf-8"))
    model_id = champion["champion_model_id"]
    pred = pd.read_parquet(output_dir / "predictions" / f"test_{model_id}.parquet")
    targets = pd.read_parquet(output_dir / "data" / "targets.parquet")
    frame = pred.merge(targets, on="event_uid", validate="one_to_one")
    plots = output_dir / "plots"
    plots.mkdir(parents=True, exist_ok=True)
    focus = focus_mask(frame["generator_energy_gev_x"])
    plt.figure(figsize=(6, 5))
    plt.scatter(
        frame.loc[focus, "energy_true_gev"], frame.loc[focus, "E_total_hat"], s=2, alpha=0.25
    )
    lim = [50, 250]
    plt.plot(lim, lim, color="black", linewidth=1)
    plt.xlabel("True total energy [GeV]")
    plt.ylabel("Predicted total energy [GeV]")
    plt.title("Focus test energy response")
    plt.tight_layout()
    energy_plot = plots / "focus_test_energy_response.png"
    plt.savefig(energy_plot, dpi=160)
    plt.close()
    response = frame.loc[focus, "E_total_hat"].to_numpy(float) / frame.loc[
        focus, "energy_true_gev"
    ].to_numpy(float)
    plt.figure(figsize=(6, 4))
    plt.hist(response - 1.0, bins=80)
    plt.xlabel("Relative energy response minus 1")
    plt.ylabel("Events")
    plt.title("Focus test residuals")
    plt.tight_layout()
    residual_plot = plots / "focus_test_energy_residual.png"
    plt.savefig(residual_plot, dpi=160)
    plt.close()
    return {"status": "plotted", "plots": [str(energy_plot), str(residual_plot)]}


def verify_outputs(*, output_dir: str | Path, schema_path: str | Path) -> dict[str, Any]:
    output_dir = Path(output_dir)
    validate_schema_command(schema_path)
    required = [
        output_dir / "preflight" / "inspection_report.json",
        output_dir / "preflight" / "schema.lock.yaml",
        output_dir / "preflight" / "data_fingerprint.json",
        output_dir / "data" / "targets.parquet",
        output_dir / "data" / "splits.parquet",
        output_dir / "data" / "features_manifest.parquet",
        output_dir / "reports" / "feature_manifest.csv",
        output_dir / "reports" / "split_report.json",
        output_dir / "reports" / "duplicate_report.json",
        output_dir / "metrics" / "validation_leaderboard.csv",
        output_dir / "reports" / "selection_decision.md",
        output_dir / "reports" / "test_unlock.json",
        output_dir / "metrics" / "focus_test_metrics.json",
        output_dir / "metrics" / "empirical_interval_coverage.json",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing required artifacts: {missing}")
    return {
        "status": "ok",
        "verified_artifacts": len(required),
        "metrics_sha256": file_sha256(output_dir / "metrics" / "focus_test_metrics.json"),
    }


def append_qa_ledger(output_dir: str | Path, text: str) -> None:
    path = Path(output_dir) / "reports" / "qa_ledger.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write("\n" + text.rstrip() + "\n")


def _parse_gcs_uri(uri: str) -> tuple[str, str]:
    if not uri.startswith("gs://"):
        raise ValueError(f"Expected gs:// URI, got {uri}")
    rest = uri[5:]
    bucket, _, blob = rest.partition("/")
    if not bucket or not blob:
        raise ValueError(f"GCS URI must include bucket and object prefix: {uri}")
    return bucket, blob


def _storage_client() -> Any:
    try:
        from google.cloud import storage
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("google-cloud-storage is required for GCS pipeline stages") from exc
    return storage.Client()


def download_gcs_file(uri: str, destination: str | Path) -> dict[str, Any]:
    client = _storage_client()
    bucket_name, blob_name = _parse_gcs_uri(uri)
    blob = client.bucket(bucket_name).blob(blob_name)
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    blob.download_to_filename(destination)
    return {
        "uri": uri,
        "destination": str(destination),
        "size_bytes": destination.stat().st_size,
        "sha256": file_sha256(destination),
    }


def download_gcs_prefix(gcs_prefix: str, destination: str | Path) -> dict[str, Any]:
    client = _storage_client()
    bucket_name, prefix = _parse_gcs_uri(gcs_prefix.rstrip("/") + "/sentinel")
    prefix = prefix.rsplit("/", 1)[0]
    bucket = client.bucket(bucket_name)
    destination = Path(destination)
    downloaded = []
    for blob in client.list_blobs(bucket, prefix=prefix.rstrip("/") + "/"):
        rel = blob.name.removeprefix(prefix.rstrip("/") + "/")
        if not rel or rel.endswith("/"):
            continue
        path = destination / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        blob.download_to_filename(path)
        downloaded.append({"uri": f"gs://{bucket_name}/{blob.name}", "path": str(path)})
    return {
        "gcs_prefix": gcs_prefix,
        "destination": str(destination),
        "downloaded_files": len(downloaded),
        "files": downloaded,
    }


def upload_dir_to_gcs(local_dir: str | Path, gcs_prefix: str) -> dict[str, Any]:
    client = _storage_client()
    bucket_name, prefix = _parse_gcs_uri(gcs_prefix.rstrip("/") + "/sentinel")
    prefix = prefix.rsplit("/", 1)[0]
    bucket = client.bucket(bucket_name)
    local_dir = Path(local_dir)
    uploaded = []
    for path in sorted(item for item in local_dir.rglob("*") if item.is_file()):
        rel = path.relative_to(local_dir).as_posix()
        blob_name = f"{prefix}/{rel}"
        bucket.blob(blob_name).upload_from_filename(path)
        uploaded.append({"path": str(path), "uri": f"gs://{bucket_name}/{blob_name}"})
    return {"gcs_prefix": gcs_prefix, "uploaded_files": len(uploaded), "files": uploaded}


def upload_file_to_gcs(local_path: str | Path, gcs_uri: str) -> dict[str, Any]:
    client = _storage_client()
    bucket_name, blob_name = _parse_gcs_uri(gcs_uri)
    local_path = Path(local_path)
    client.bucket(bucket_name).blob(blob_name).upload_from_filename(local_path)
    return {
        "path": str(local_path),
        "uri": gcs_uri,
        "size_bytes": local_path.stat().st_size,
        "sha256": file_sha256(local_path),
    }


def run_all_gcs(
    *,
    data_gcs: str,
    output_gcs: str,
    config: str | Path,
    workdir: str | Path,
) -> dict[str, Any]:
    workdir = Path(workdir)
    output_dir = workdir / "outputs"
    data_path = workdir / "data" / Path(_parse_gcs_uri(data_gcs)[1]).name
    output_dir.mkdir(parents=True, exist_ok=True)
    state: dict[str, Any] = {
        "state_schema_version": 1,
        "created_utc": utc_now(),
        "data_gcs": data_gcs,
        "output_gcs": output_gcs,
        "workdir": str(workdir),
        "status": "running",
        "current_stage": "initializing",
        "stage_history": [],
        "stage_results": {},
    }

    state_path = output_dir / "reports" / "vertex_job_state.json"
    state_gcs = output_gcs.rstrip("/") + "/reports/vertex_job_state.json"

    def publish_state(event: str) -> None:
        state["updated_utc"] = utc_now()
        write_json(state_path, state)
        print(
            json.dumps(
                {
                    "event": event,
                    "status": state["status"],
                    "current_stage": state.get("current_stage"),
                    "updated_utc": state["updated_utc"],
                },
                sort_keys=True,
            ),
            flush=True,
        )
        try:
            upload_file_to_gcs(state_path, state_gcs)
        except Exception as exc:  # pragma: no cover - best-effort progress breadcrumb
            print(
                json.dumps(
                    {
                        "event": "state_upload_warning",
                        "error": repr(exc),
                        "state_gcs": state_gcs,
                    },
                    sort_keys=True,
                ),
                flush=True,
            )

    def run_stage(name: str, callback: Any) -> Any:
        entry = {"stage": name, "status": "running", "started_utc": utc_now()}
        state["stage_history"].append(entry)
        state["current_stage"] = name
        publish_state("stage_started")
        result = callback()
        entry["status"] = "complete"
        entry["completed_utc"] = utc_now()
        state["stage_results"][name] = result
        publish_state("stage_completed")
        return result

    try:
        publish_state("job_started")
        state["download"] = run_stage(
            "download-root",
            lambda: download_gcs_file(data_gcs, data_path),
        )
        preflight = output_dir / "preflight"
        run_stage("inspect-root", lambda: inspect_root(data_path, config, preflight))
        schema_path = preflight / "schema.lock.yaml"
        run_stage("validate-schema", lambda: validate_schema_command(schema_path))
        run_stage(
            "build-targets",
            lambda: build_targets(
                data=data_path,
                config=config,
                schema_path=schema_path,
                output_dir=output_dir,
            ),
        )
        run_stage("make-splits", lambda: make_splits(config=config, output_dir=output_dir))
        run_stage(
            "build-features",
            lambda: build_features(
                data=data_path,
                config=config,
                schema_path=schema_path,
                output_dir=output_dir,
            ),
        )
        run_stage(
            "train-baselines",
            lambda: train_baselines(config=config, schema_path=schema_path, output_dir=output_dir),
        )
        run_stage(
            "train-xgb",
            lambda: train_xgb(config=config, schema_path=schema_path, output_dir=output_dir),
        )
        run_stage("select-model", lambda: select_model(output_dir=output_dir))
        run_stage("calibrate", lambda: calibrate(config=config, output_dir=output_dir))
        run_stage("unlock-test", lambda: unlock_test(output_dir=output_dir))
        run_stage(
            "evaluate-test",
            lambda: evaluate_test(config=config, output_dir=output_dir),
        )
        run_stage("plot", lambda: plot_outputs(output_dir=output_dir))
        run_stage(
            "verify",
            lambda: verify_outputs(output_dir=output_dir, schema_path=schema_path),
        )
        state["status"] = "complete"
        state["current_stage"] = "complete"
        state["completed_utc"] = utc_now()
        publish_state("job_completed")
        return state
    except Exception as exc:
        for entry in reversed(state["stage_history"]):
            if entry["status"] == "running":
                entry["status"] = "failed"
                entry["failed_utc"] = utc_now()
                break
        state["status"] = "failed"
        state["failed_utc"] = utc_now()
        state["error"] = repr(exc)
        publish_state("job_failed")
        raise
    finally:
        if output_dir.exists():
            upload_dir_to_gcs(output_dir, output_gcs)


def _clear_training_artifacts(output_dir: Path) -> None:
    for dirname in ("models", "predictions", "metrics", "plots"):
        path = output_dir / dirname
        if path.exists():
            _safe_generated_rmtree(path, output_dir)
    for path in (
        output_dir / "reports" / "champion.json",
        output_dir / "reports" / "selection_decision.md",
        output_dir / "reports" / "test_unlock.json",
    ):
        if path.exists():
            path.unlink()


def resume_training_gcs(
    *,
    source_gcs: str,
    output_gcs: str,
    config: str | Path,
    workdir: str | Path,
) -> dict[str, Any]:
    workdir = Path(workdir)
    output_dir = workdir / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    state: dict[str, Any] = {
        "state_schema_version": 1,
        "created_utc": utc_now(),
        "source_gcs": source_gcs,
        "output_gcs": output_gcs,
        "workdir": str(workdir),
        "status": "running",
        "current_stage": "initializing",
        "stage_history": [],
        "stage_results": {},
    }
    state_path = output_dir / "reports" / "vertex_job_state.json"
    state_gcs = output_gcs.rstrip("/") + "/reports/vertex_job_state.json"

    def publish_state(event: str) -> None:
        state["updated_utc"] = utc_now()
        write_json(state_path, state)
        print(
            json.dumps(
                {
                    "event": event,
                    "status": state["status"],
                    "current_stage": state.get("current_stage"),
                    "updated_utc": state["updated_utc"],
                },
                sort_keys=True,
            ),
            flush=True,
        )
        try:
            upload_file_to_gcs(state_path, state_gcs)
        except Exception as exc:  # pragma: no cover
            print(
                json.dumps(
                    {
                        "event": "state_upload_warning",
                        "error": repr(exc),
                        "state_gcs": state_gcs,
                    },
                    sort_keys=True,
                ),
                flush=True,
            )

    def run_stage(name: str, callback: Any) -> Any:
        entry = {"stage": name, "status": "running", "started_utc": utc_now()}
        state["stage_history"].append(entry)
        state["current_stage"] = name
        publish_state("stage_started")
        result = callback()
        entry["status"] = "complete"
        entry["completed_utc"] = utc_now()
        state["stage_results"][name] = result
        publish_state("stage_completed")
        return result

    try:
        publish_state("job_started")
        run_stage(
            "download-existing-artifacts", lambda: download_gcs_prefix(source_gcs, output_dir)
        )
        run_stage(
            "clear-training-artifacts",
            lambda: _clear_training_artifacts(output_dir) or {"status": "cleared"},
        )
        schema_path = output_dir / "preflight" / "schema.lock.yaml"
        run_stage("validate-schema", lambda: validate_schema_command(schema_path))
        run_stage(
            "train-baselines",
            lambda: train_baselines(config=config, schema_path=schema_path, output_dir=output_dir),
        )
        run_stage(
            "train-xgb",
            lambda: train_xgb(config=config, schema_path=schema_path, output_dir=output_dir),
        )
        run_stage("select-model", lambda: select_model(output_dir=output_dir))
        run_stage("calibrate", lambda: calibrate(config=config, output_dir=output_dir))
        run_stage("unlock-test", lambda: unlock_test(output_dir=output_dir))
        run_stage("evaluate-test", lambda: evaluate_test(config=config, output_dir=output_dir))
        run_stage("plot", lambda: plot_outputs(output_dir=output_dir))
        run_stage(
            "verify",
            lambda: verify_outputs(output_dir=output_dir, schema_path=schema_path),
        )
        state["status"] = "complete"
        state["current_stage"] = "complete"
        state["completed_utc"] = utc_now()
        publish_state("job_completed")
        return state
    except Exception as exc:
        for entry in reversed(state["stage_history"]):
            if entry["status"] == "running":
                entry["status"] = "failed"
                entry["failed_utc"] = utc_now()
                break
        state["status"] = "failed"
        state["failed_utc"] = utc_now()
        state["error"] = repr(exc)
        publish_state("job_failed")
        raise
    finally:
        if output_dir.exists():
            upload_dir_to_gcs(output_dir, output_gcs)
