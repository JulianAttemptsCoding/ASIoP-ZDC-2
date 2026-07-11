from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from .config import canonical_json_hash, load_config
from .geometry import infer_detector_frame, validate_frame
from .physics import infer_energy_convention


def _imports():
    try:
        import awkward as ak
        import uproot
    except ImportError as exc:  # pragma: no cover - dependency gate
        raise RuntimeError(
            "ROOT inspection requires uproot and awkward; install the project"
        ) from exc
    return uproot, ak


def resolve_tree(root_file: Any, requested: str) -> tuple[str, Any]:
    if requested != "auto_strict":
        if requested not in root_file:
            raise ValueError(f"Configured tree not found: {requested}")
        return requested, root_file[requested]
    candidates = []
    for key, classname in root_file.classnames(recursive=True).items():
        if classname in {"TTree", "ROOT::RNTuple"}:
            candidates.append(key.split(";")[0])
    candidates = sorted(set(candidates))
    if len(candidates) != 1:
        raise ValueError(f"auto_strict requires exactly one TTree/RNTuple; found {candidates}")
    return candidates[0], root_file[candidates[0]]


def validate_branch_mapping(tree: Any, mapping: dict[str, str | None]) -> dict[str, str]:
    available = {str(name) for name in tree.keys()}
    required_keys = {
        "ecal_x",
        "ecal_y",
        "ecal_z",
        "ecal_signal",
        "hcal_x",
        "hcal_y",
        "hcal_z",
        "hcal_signal",
        "truth_pdg",
        "truth_energy",
        "truth_px",
        "truth_py",
        "truth_pz",
    }
    resolved = {}
    for logical, physical in mapping.items():
        if logical in required_keys and not physical:
            raise ValueError(f"Required logical branch has no mapping: {logical}")
        if physical is not None:
            if physical not in available:
                suggestions = sorted(
                    name for name in available if logical.split("_")[-1].lower() in name.lower()
                )
                raise ValueError(
                    f"Mapped branch {physical!r} for {logical} is missing. "
                    f"Suggestions (not accepted automatically): {suggestions[:10]}"
                )
            resolved[logical] = physical
    return resolved


def _as_event_list(array: Any, ak: Any) -> list:
    return ak.to_list(array)


def _sha256_file(path: Path, chunk_size: int = 16 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def select_exactly_one_neutron(
    pdg: Any,
    energy: Any,
    px: Any,
    py: Any,
    pz: Any,
    *,
    neutron_pdg: int,
    ak: Any,
) -> tuple[np.ndarray, np.ndarray]:
    values = [_as_event_list(item, ak) for item in (pdg, energy, px, py, pz)]
    selected_energy = []
    selected_momentum = []
    for event_index, event_values in enumerate(zip(*values, strict=True)):
        event_pdg = event_values[0]
        if isinstance(event_pdg, (int, float)):
            pdgs = [event_pdg]
            fields = [[value] for value in event_values[1:]]
        else:
            pdgs = list(event_pdg)
            fields = [list(value) for value in event_values[1:]]
        if any(len(field) != len(pdgs) for field in fields):
            raise ValueError(f"Truth jagged lengths disagree in event {event_index}")
        indices = [index for index, value in enumerate(pdgs) if int(value) == neutron_pdg]
        if len(indices) != 1:
            raise ValueError(
                f"Event {event_index} contains {len(indices)} truth neutrons; "
                "exactly-one policy cannot identify the primary without status/parent metadata"
            )
        index = indices[0]
        selected_energy.append(float(fields[0][index]))
        selected_momentum.append(
            [float(fields[1][index]), float(fields[2][index]), float(fields[3][index])]
        )
    return np.asarray(selected_energy), np.asarray(selected_momentum)


def inspect_root(
    data_path: str | Path,
    config_path: str | Path,
    output_dir: str | Path,
) -> dict:
    uproot, ak = _imports()
    cfg = load_config(config_path)
    data_path = Path(data_path).resolve()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    with uproot.open(data_path) as root_file:
        tree_name, tree = resolve_tree(root_file, cfg["data"]["tree_name"])
        mapping = validate_branch_mapping(tree, cfg["data"]["branches"])
        position_scale_to_cm = float(cfg["geometry"].get("position_scale_to_cm", 1.0))
        required = [mapping[key] for key in mapping if key.startswith(("ecal_", "hcal_", "truth_"))]
        stop = min(int(cfg["data"]["inspection_events"]), int(tree.num_entries))
        arrays = tree.arrays(required, entry_start=0, entry_stop=stop, library="ak")
        truth_energy, truth_momentum = select_exactly_one_neutron(
            arrays[mapping["truth_pdg"]],
            arrays[mapping["truth_energy"]],
            arrays[mapping["truth_px"]],
            arrays[mapping["truth_py"]],
            arrays[mapping["truth_pz"]],
            neutron_pdg=int(cfg["physics"]["particle_pdg"]),
            ak=ak,
        )
        convention = infer_energy_convention(
            truth_energy,
            truth_momentum,
            mass_gev=float(cfg["physics"]["neutron_mass_gev"]),
            median_tolerance=float(cfg["physics"]["convention_median_relative_tolerance"]),
            p99_tolerance=float(cfg["physics"]["convention_p99_relative_tolerance"]),
            min_score_ratio=float(cfg["physics"]["convention_min_score_ratio"]),
        )
        e_points = (
            np.column_stack(
                [
                    ak.to_numpy(ak.flatten(arrays[mapping[key]], axis=None))
                    for key in ("ecal_x", "ecal_y", "ecal_z")
                ]
            )
            * position_scale_to_cm
        )
        h_points = (
            np.column_stack(
                [
                    ak.to_numpy(ak.flatten(arrays[mapping[key]], axis=None))
                    for key in ("hcal_x", "hcal_y", "hcal_z")
                ]
            )
            * position_scale_to_cm
        )
        frame = infer_detector_frame(
            e_points,
            h_points,
            minimum_center_separation_cm=float(
                cfg["geometry"]["minimum_ecal_hcal_center_separation_cm"]
            ),
            nominal_ecal_depth_cm=float(cfg["geometry"]["ecal"]["cell_cm"][2]),
            nominal_hcal_depth_cm=float(cfg["geometry"]["hcal"]["volume_cm"][2]),
        )
        validate_frame(frame)
        e_local = frame.transform(e_points)
        h_local = frame.transform(h_points)
        geometry_observation = {
            "ecal_projected_hit_span_cm": [float(v) for v in np.ptp(e_local, axis=0)],
            "hcal_projected_hit_span_cm": [float(v) for v in np.ptp(h_local, axis=0)],
            "nominal_ecal_face_depth_cm": [
                *[float(v) for v in cfg["geometry"]["ecal"]["face_cm"]],
                float(cfg["geometry"]["ecal"]["cell_cm"][2]),
            ],
            "nominal_hcal_volume_cm": [float(v) for v in cfg["geometry"]["hcal"]["volume_cm"]],
            "note": (
                "Observed hit spans are occupancy diagnostics, not automatically "
                "accepted geometry. Reconcile coordinate centers/IDs with the nominal "
                "segmentation before training."
            ),
        }
        report = {
            "data_path": str(data_path),
            "data_size_bytes": data_path.stat().st_size,
            "data_sha256": _sha256_file(data_path),
            "tree_name": tree_name,
            "entries": int(tree.num_entries),
            "branch_mapping": mapping,
            "branch_types": {name: str(tree[name].typename) for name in mapping.values()},
            "truth_energy_convention": convention.to_dict(),
            "position_scale_to_cm": position_scale_to_cm,
            "detector_frame": frame.to_dict(),
            "geometry_observation": geometry_observation,
            "inspection_entries": stop,
            "config_sha256": canonical_json_hash(cfg),
        }
    (output_dir / "inspection_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    lock = {
        "source_config": str(Path(config_path).resolve()),
        "data_path": str(data_path),
        "tree_name": report["tree_name"],
        "branch_mapping": report["branch_mapping"],
        "truth_energy_convention": report["truth_energy_convention"],
        "position_scale_to_cm": report["position_scale_to_cm"],
        "detector_frame": report["detector_frame"],
        "hit_signal_scale_to_gev": cfg["data"]["hit_signal_scale_to_gev"],
        "requires_human_or_documented_signal_unit_resolution": any(
            value is None for value in cfg["data"]["hit_signal_scale_to_gev"].values()
        ),
    }
    (output_dir / "schema.lock.yaml").write_text(
        yaml.safe_dump(lock, sort_keys=False), encoding="utf-8"
    )
    return report
