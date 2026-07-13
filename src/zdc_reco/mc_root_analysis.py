"""Chunked full-file ROOT analysis for the ZDC single-neutron MC sample.

This module is designed for Vertex execution. It reads the ROOT object directly from
Google Cloud Storage, keeps only compact event summaries in memory, and writes the
analysis report and figures to a GCS output prefix.
"""

from __future__ import annotations

import argparse
import collections
import json
import math
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import awkward as ak
import fsspec
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import uproot

from .physics import canonical_truth, infer_energy_convention

NEUTRON_MASS_GEV = 0.93956542052
ECAL_BRANCHES = ("ecal_cellID", "ecal_energy", "ecal_posX", "ecal_posY", "ecal_posZ")
HCAL_BRANCHES = (
    "hcal_cellID",
    "hcal_LayerID",
    "hcal_energy",
    "hcal_posX",
    "hcal_posY",
    "hcal_posZ",
)
TRUTH_BRANCHES = ("mcPar_PDG", "mcPar_energy", "mcPar_momX", "mcPar_momY", "mcPar_momZ")
SUMMARY_BRANCHES = (
    "energySum_ecal",
    "energySum_hcal",
    "energySum_ZDC",
    "energyRatio_ecal",
    "energyRatio_hcal",
    "energyRatio_ZDC",
    "energyRatio_ecal_emax",
)
REQUIRED_BRANCHES = ECAL_BRANCHES + HCAL_BRANCHES + TRUTH_BRANCHES + SUMMARY_BRANCHES


@dataclass
class NumericStats:
    count: int = 0
    finite: int = 0
    nonfinite: int = 0
    negative: int = 0
    zero: int = 0
    positive: int = 0
    sum_value: float = 0.0
    sum_square: float = 0.0
    minimum: float = math.inf
    maximum: float = -math.inf
    _sample: list[np.ndarray] = field(default_factory=list, repr=False)
    _sample_size: int = field(default=0, repr=False)

    def update(self, values: np.ndarray, sample_cap: int = 50_000) -> None:
        values = np.asarray(values, dtype=float).reshape(-1)
        self.count += len(values)
        finite = values[np.isfinite(values)]
        self.finite += len(finite)
        self.nonfinite += len(values) - len(finite)
        if not len(finite):
            return
        self.negative += int(np.sum(finite < 0.0))
        self.zero += int(np.sum(finite == 0.0))
        self.positive += int(np.sum(finite > 0.0))
        self.sum_value += float(np.sum(finite))
        self.sum_square += float(np.sum(finite**2))
        self.minimum = min(self.minimum, float(np.min(finite)))
        self.maximum = max(self.maximum, float(np.max(finite)))
        remaining = sample_cap - self._sample_size
        if remaining <= 0:
            return
        stride = max(1, math.ceil(len(finite) / remaining))
        sample = finite[::stride][:remaining]
        self._sample.append(sample)
        self._sample_size += len(sample)

    def to_dict(self) -> dict[str, float | int | None]:
        sample = np.concatenate(self._sample) if self._sample else np.array([], dtype=float)
        mean = self.sum_value / self.finite if self.finite else None
        variance = (
            self.sum_square / self.finite - mean**2 if self.finite and mean is not None else None
        )
        return {
            "count": self.count,
            "finite": self.finite,
            "nonfinite": self.nonfinite,
            "negative": self.negative,
            "zero": self.zero,
            "positive": self.positive,
            "minimum": None if not self.finite else self.minimum,
            "maximum": None if not self.finite else self.maximum,
            "mean": mean,
            "standard_deviation": None
            if variance is None
            else float(math.sqrt(max(variance, 0.0))),
            "sample_quantiles": {
                "q01": None if not len(sample) else float(np.quantile(sample, 0.01)),
                "q50": None if not len(sample) else float(np.quantile(sample, 0.50)),
                "q99": None if not len(sample) else float(np.quantile(sample, 0.99)),
            },
        }


@dataclass
class CenterMap:
    entries: dict[int, tuple[float, float, float]] = field(default_factory=dict)
    conflicts: int = 0

    def update(self, keys: np.ndarray, x: np.ndarray, y: np.ndarray, z: np.ndarray) -> None:
        keys = np.asarray(keys, dtype=np.int64)
        coordinates = np.column_stack([x, y, z]).astype(float, copy=False)
        if not len(keys):
            return
        unique, first, inverse = np.unique(keys, return_index=True, return_inverse=True)
        representatives = coordinates[first]
        if not np.allclose(coordinates, representatives[inverse], rtol=0.0, atol=1e-9):
            self.conflicts += 1
        for key, point in zip(unique, representatives, strict=True):
            point_tuple = tuple(float(value) for value in point)
            previous = self.entries.get(int(key))
            if previous is None:
                self.entries[int(key)] = point_tuple
            elif not np.allclose(previous, point_tuple, rtol=0.0, atol=1e-9):
                self.conflicts += 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-uri", required=True, help="gs:// URI of the ROOT file")
    parser.add_argument("--output-uri", required=True, help="gs:// URI prefix for compact outputs")
    parser.add_argument(
        "--tree-name", default="myTree", help="Latest ROOT cycle is selected by default"
    )
    parser.add_argument("--step-size", default="100 MB", help="Uproot iterate chunk size")
    parser.add_argument("--position-scale-to-cm", type=float, default=0.1)
    parser.add_argument("--decompression-workers", type=int, default=16)
    return parser.parse_args()


def split_gcs_uri(uri: str) -> tuple[str, str]:
    if not uri.startswith("gs://"):
        raise ValueError(f"Expected gs:// URI, got {uri!r}")
    bucket_and_path = uri[5:].split("/", 1)
    if len(bucket_and_path) != 2 or not bucket_and_path[1]:
        raise ValueError(f"Expected gs://bucket/path URI, got {uri!r}")
    return bucket_and_path[0], bucket_and_path[1]


def scalar_from_jagged(values: ak.Array) -> np.ndarray:
    return ak.to_numpy(ak.fill_none(ak.firsts(values), np.nan)).astype(float, copy=False)


def update_alignment(reference: ak.Array, candidate: ak.Array) -> int:
    return int(np.sum(ak.to_numpy(ak.num(reference, axis=1) != ak.num(candidate, axis=1))))


def selected_neutron_truth(arrays: ak.Array) -> dict[str, np.ndarray]:
    mask = arrays["mcPar_PDG"] == 2112
    neutron_counts = ak.to_numpy(ak.sum(mask, axis=1))
    selected = {}
    for logical, branch in (
        ("raw_mcpar_energy", "mcPar_energy"),
        ("raw_mcpar_px", "mcPar_momX"),
        ("raw_mcpar_py", "mcPar_momY"),
        ("raw_mcpar_pz", "mcPar_momZ"),
    ):
        selected[logical] = ak.to_numpy(ak.fill_none(ak.firsts(arrays[branch][mask]), np.nan))
    selected["neutron_count"] = neutron_counts
    return selected


def update_event_vectors(store: dict[str, list[np.ndarray]], values: dict[str, np.ndarray]) -> None:
    for key, value in values.items():
        store.setdefault(key, []).append(np.asarray(value))


def concat_event_vectors(store: dict[str, list[np.ndarray]]) -> dict[str, np.ndarray]:
    return {key: np.concatenate(value) for key, value in store.items()}


def summarize_values(values: np.ndarray) -> dict[str, float | int | None]:
    stats = NumericStats()
    stats.update(values)
    return stats.to_dict()


def branch_catalog(tree: Any) -> list[dict[str, Any]]:
    rows = []
    for name in tree.keys():
        branch = tree[name]
        rows.append(
            {
                "branch": name,
                "typename": str(branch.typename),
                "compressed_bytes": int(branch.compressed_bytes),
                "uncompressed_bytes": int(branch.uncompressed_bytes),
                "baskets": int(branch.num_baskets),
            }
        )
    return rows


def histogram_metadata(root_file: Any) -> list[dict[str, Any]]:
    rows = []
    for key, classname in root_file.classnames(recursive=True).items():
        if not classname.startswith("TH"):
            continue
        obj = root_file[key]
        axes = []
        for axis in obj.axes:
            edges = axis.edges()
            axes.append(
                {
                    "bins": int(len(edges) - 1),
                    "minimum": float(edges[0]),
                    "maximum": float(edges[-1]),
                }
            )
        rows.append({"key": key, "classname": classname, "title": str(obj.title), "axes": axes})
    return rows


def centers_dataframe(center_map: CenterMap, scale: float, *, include_layer: bool) -> pd.DataFrame:
    rows = []
    for key, (x, y, z) in sorted(center_map.entries.items()):
        row = {
            "x_raw": x,
            "y_raw": y,
            "z_raw": z,
            "x_cm": x * scale,
            "y_cm": y * scale,
            "z_cm": z * scale,
        }
        if include_layer:
            row["layer_id"] = key // 1_000_000
            row["cell_id"] = key % 1_000_000
        else:
            row["cell_id"] = key
        rows.append(row)
    return pd.DataFrame(rows)


def center_axis_summary(frame: pd.DataFrame) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for axis in ("x_cm", "y_cm", "z_cm"):
        values = np.sort(frame[axis].unique())
        differences = np.diff(values)
        output[axis] = {
            "unique_centers": int(len(values)),
            "minimum_cm": None if not len(values) else float(values.min()),
            "maximum_cm": None if not len(values) else float(values.max()),
            "median_nonzero_pitch_cm": None
            if not len(differences[differences > 1e-12])
            else float(np.median(differences[differences > 1e-12])),
        }
    return output


def make_plots(
    events: dict[str, np.ndarray],
    ecal_centers: pd.DataFrame,
    hcal_centers: pd.DataFrame,
    output_dir: Path,
) -> None:
    plt.rcParams.update({"axes.grid": True, "axes.spines.top": False, "axes.spines.right": False})
    energy = events["energy_true_gev"]
    visible = events["ecal_sum_gev"] + events["hcal_sum_gev"]
    response = visible / np.maximum(energy, NEUTRON_MASS_GEV)

    figure, axes = plt.subplots(2, 3, figsize=(15, 8))
    axes[0, 0].hist(energy, bins=np.linspace(0, 300, 61), color="#1976d2")
    axes[0, 0].set(title="True neutron energy", xlabel="GeV", ylabel="events")
    axes[0, 1].hist(events["theta_true_rad"] * 1000.0, bins=80, color="#e26d24")
    axes[0, 1].set(title="True polar angle", xlabel="theta [mrad]", ylabel="events")
    axes[0, 2].hist(events["phi_true_rad"], bins=80, color="#2e8b57")
    axes[0, 2].set(title="True azimuth", xlabel="phi [rad]", ylabel="events")
    axes[1, 0].hist(events["ecal_hits"], bins=np.logspace(0, 4, 81), color="#1976d2")
    axes[1, 0].set_xscale("log")
    axes[1, 0].set(title="ECAL hit multiplicity", xlabel="hits/event", ylabel="events")
    axes[1, 1].hist(events["hcal_hits"], bins=np.logspace(0, 5, 81), color="#e26d24")
    axes[1, 1].set_xscale("log")
    axes[1, 1].set(title="HCAL hit multiplicity", xlabel="hits/event", ylabel="events")
    axes[1, 2].hist(
        visible, bins=np.linspace(0, max(300.0, np.quantile(visible, 0.999)), 81), color="#2e8b57"
    )
    axes[1, 2].set(title="Visible ECAL+HCAL signal", xlabel="stored energy units", ylabel="events")
    figure.suptitle("Full ROOT sample: event and hit population")
    figure.tight_layout()
    figure.savefig(output_dir / "01_event_and_hit_distributions.png", dpi=180)
    plt.close(figure)

    figure, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    image = axes[0].hexbin(energy, visible, gridsize=75, mincnt=1, bins="log", cmap="Blues")
    axes[0].set(
        title="Visible signal versus true energy",
        xlabel="true energy [GeV]",
        ylabel="visible signal",
    )
    figure.colorbar(image, ax=axes[0], label="log10(events)")
    image = axes[1].hexbin(
        energy, events["ecal_sum_gev"], gridsize=75, mincnt=1, bins="log", cmap="Blues"
    )
    axes[1].set(
        title="ECAL signal versus true energy", xlabel="true energy [GeV]", ylabel="ECAL signal"
    )
    figure.colorbar(image, ax=axes[1], label="log10(events)")
    image = axes[2].hexbin(
        energy, events["hcal_sum_gev"], gridsize=75, mincnt=1, bins="log", cmap="Blues"
    )
    axes[2].set(
        title="HCAL signal versus true energy", xlabel="true energy [GeV]", ylabel="HCAL signal"
    )
    figure.colorbar(image, ax=axes[2], label="log10(events)")
    figure.suptitle("Full ROOT sample: calorimeter response inputs")
    figure.tight_layout()
    figure.savefig(output_dir / "02_signal_response.png", dpi=180)
    plt.close(figure)

    figure, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    image = axes[0].hexbin(energy, response, gridsize=75, mincnt=1, bins="log", cmap="Blues")
    axes[0].axhline(1.0, color="#c62828", linewidth=1.0)
    axes[0].set(
        title="Raw visible response", xlabel="true energy [GeV]", ylabel="(ECAL+HCAL)/E_true"
    )
    figure.colorbar(image, ax=axes[0], label="log10(events)")
    image = axes[1].hexbin(
        events["theta_true_rad"] * 1000.0, response, gridsize=75, mincnt=1, bins="log", cmap="Blues"
    )
    axes[1].axhline(1.0, color="#c62828", linewidth=1.0)
    axes[1].set(
        title="Raw visible response versus angle",
        xlabel="theta [mrad]",
        ylabel="(ECAL+HCAL)/E_true",
    )
    figure.colorbar(image, ax=axes[1], label="log10(events)")
    figure.suptitle("Full ROOT sample: raw response conditioning variables")
    figure.tight_layout()
    figure.savefig(output_dir / "03_raw_response_slices.png", dpi=180)
    plt.close(figure)

    figure, axes = plt.subplots(1, 2, figsize=(12, 5))
    axes[0].scatter(ecal_centers["x_cm"], ecal_centers["y_cm"], s=16, color="#1976d2")
    axes[0].set(title="ECAL unique cell centers", xlabel="x [cm]", ylabel="y [cm]", aspect="equal")
    axes[1].scatter(
        hcal_centers["x_cm"], hcal_centers["z_cm"], c=hcal_centers["layer_id"], s=14, cmap="viridis"
    )
    axes[1].set(
        title="HCAL representative locations (not stable ID centers)",
        xlabel="x [cm]",
        ylabel="z [cm]",
    )
    figure.suptitle("Full ROOT sample: coordinate-mapping validation")
    figure.tight_layout()
    figure.savefig(output_dir / "04_coordinate_centers.png", dpi=180)
    plt.close(figure)


def fast_mc_contract(report: dict[str, Any]) -> dict[str, Any]:
    geometry = report["geometry"]
    return {
        "source": {
            "file_uri": report["input_uri"],
            "tree": report["selected_tree"],
            "events": report["events"],
            "event_unit": (
                "one simulated event with jagged ECAL/HCAL hit deposits and MC particle truth"
            ),
        },
        "truth_conditioning": {
            "required": ["generator_energy_gev", "px_true_gev", "py_true_gev", "pz_true_gev"],
            "derived": [
                "energy_true_gev",
                "kinetic_energy_true_gev",
                "theta_true_rad",
                "phi_true_rad",
            ],
            "primary_particle_rule": "exactly one MC particle with PDG 2112 per selected event",
            "neutron_mass_gev": NEUTRON_MASS_GEV,
        },
        "generated_response": {
            "ecal": ["ecal_cellID", "ecal_posX", "ecal_posY", "ecal_posZ", "ecal_energy"],
            "hcal": [
                "hcal_cellID",
                "hcal_LayerID",
                "hcal_posX",
                "hcal_posY",
                "hcal_posZ",
                "hcal_energy",
            ],
            "preserve": [
                "hit multiplicity conditional on energy and direction",
                "ECAL/HCAL total-signal correlation",
                "cell/layer occupancy and energy-fraction correlations",
                "zero-hit and zero-signal events",
                "nonnegative deposit convention and coordinate/cell mapping",
            ],
            "mapping_validation": {
                "ecal": {
                    "unique_cell_ids": geometry["ecal_unique_cell_ids"],
                    "position_conflicts": geometry["ecal_cell_position_conflicts"],
                    "interpretation": (
                        "The 400 ECAL cell identifiers have stable recorded positions and support "
                        "an ID-derived 20x20 tensor."
                    ),
                },
                "hcal": {
                    "unique_layer_cell_pairs": geometry["hcal_unique_layer_cell_pairs"],
                    "layers": geometry["hcal_unique_layers"],
                    "position_conflicts": geometry["hcal_cell_position_conflicts"],
                    "interpretation": (
                        "Recorded positions are not stable for an HCAL (layer_id, cell_id) pair. "
                        "Do not infer a fixed ID-derived HCAL grid from this file."
                    ),
                },
            },
        },
        "recommended_fast_mc_levels": [
            {
                "level": "response",
                "output": (
                    "ECAL/HCAL total deposited energy, hit counts, and low-order shower moments"
                ),
                "use": "fast reconstruction and trigger studies",
            },
            {
                "level": "ecal_grid",
                "output": "nonnegative ID-derived ECAL 20x20 cell-energy tensor",
                "use": "ML studies requiring fixed ECAL transverse response",
            },
            {
                "level": "hcal_coordinate_binned",
                "output": "HCAL tensors made by an explicitly specified coordinate-binning rule",
                "use": "ML studies after validating the chosen binning against hit positions",
                "restriction": (
                    "HCAL (layer_id, cell_id) pairs do not have stable recorded positions, so "
                    "the ROOT IDs alone do not define a fixed dense grid."
                ),
            },
            {
                "level": "jagged_hit",
                "output": "the original hit-level branch schema",
                "use": "analysis requiring exact variable-length hit representation",
            },
        ],
        "known_absences": [
            (
                "No timing, waveform, ADC, SiPM gain, electronics-noise, or pileup branches "
                "are present in the ROOT tree."
            ),
            (
                "The file supports simulation-domain fast MC only; it is not a real-detector "
                "calibration sample."
            ),
        ],
    }


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8"
    )


def upload_tree(local_root: Path, output_uri: str) -> None:
    filesystem = fsspec.filesystem("gcs")
    destination = output_uri.rstrip("/")
    for path in local_root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(local_root).as_posix()
        if relative == "input.root":
            continue
        with (
            path.open("rb") as source,
            filesystem.open(f"{destination}/{relative}", "wb") as target,
        ):
            target.write(source.read())


def stage_input_on_vertex_worker(
    filesystem: Any, input_uri: str, destination: Path, expected_size: int | None
) -> dict[str, Any]:
    """Copy the GCS object to the Vertex worker's ephemeral SSD with progress logs."""
    chunk_bytes = 64 * 1024 * 1024
    bytes_written = 0
    started = time.monotonic()
    with filesystem.open(input_uri, "rb") as source, destination.open("wb") as target:
        while block := source.read(chunk_bytes):
            target.write(block)
            bytes_written += len(block)
            if bytes_written % (1024 * 1024 * 1024) < chunk_bytes:
                elapsed = max(time.monotonic() - started, 1e-9)
                print(
                    f"Staged {bytes_written / 1024**3:.1f} GiB in {elapsed:.1f} s "
                    f"({bytes_written / elapsed / 1024**2:.1f} MiB/s)",
                    flush=True,
                )
    if expected_size is not None and bytes_written != expected_size:
        raise OSError(f"Staged {bytes_written} bytes, expected {expected_size} bytes")
    elapsed = max(time.monotonic() - started, 1e-9)
    print(
        f"Finished staging {bytes_written / 1024**3:.2f} GiB in {elapsed:.1f} s",
        flush=True,
    )
    return {
        "mode": "GCS object staged to Vertex ephemeral SSD before ROOT scan",
        "staged_bytes": bytes_written,
        "staging_seconds": elapsed,
        "worker_local_path": str(destination),
        "persistence": "ephemeral worker disk; removed when the custom-job worker exits",
    }


def main() -> None:
    args = parse_args()
    filesystem = fsspec.filesystem("gcs")
    input_info = filesystem.info(args.input_uri)
    with tempfile.TemporaryDirectory(prefix="zdc-mc-root-analysis-") as temporary:
        temporary_path = Path(temporary)
        plots_path = temporary_path / "plots"
        tables_path = temporary_path / "tables"
        reports_path = temporary_path / "reports"
        for directory in (plots_path, tables_path, reports_path):
            directory.mkdir(parents=True, exist_ok=True)

        input_access = stage_input_on_vertex_worker(
            filesystem,
            args.input_uri,
            temporary_path / "input.root",
            int(input_info["size"]) if input_info.get("size") is not None else None,
        )
        decompression_executor = ThreadPoolExecutor(max_workers=args.decompression_workers)

        with uproot.open(
            temporary_path / "input.root", decompression_executor=decompression_executor
        ) as root_file:
            selected_tree = root_file[args.tree_name]
            catalog = branch_catalog(selected_tree)
            cycles = [
                {"key": key, "classname": classname}
                for key, classname in root_file.classnames(recursive=True).items()
            ]
            object_histograms = histogram_metadata(root_file)
            all_tree_branches = tuple(selected_tree.keys())
            missing = sorted(set(REQUIRED_BRANCHES).difference(all_tree_branches))
            if missing:
                raise ValueError(f"Required branches are missing: {missing}")

            ecal_signal_stats = NumericStats()
            hcal_signal_stats = NumericStats()
            ecal_hit_stats = NumericStats()
            hcal_hit_stats = NumericStats()
            ecal_centers = CenterMap()
            hcal_centers = CenterMap()
            pdg_counts: collections.Counter[int] = collections.Counter()
            alignment_failures: collections.Counter[str] = collections.Counter()
            neutron_count_histogram: collections.Counter[int] = collections.Counter()
            sum_difference_stats = {
                "ecal": NumericStats(),
                "hcal": NumericStats(),
                "zdc": NumericStats(),
            }
            all_vector_stats = {branch: NumericStats() for branch in all_tree_branches}
            events: dict[str, list[np.ndarray]] = {}

            events_scanned = 0
            for chunk_number, arrays in enumerate(
                selected_tree.iterate(
                    expressions=all_tree_branches, step_size=args.step_size, library="ak"
                ),
                start=1,
            ):
                for branch in all_tree_branches:
                    all_vector_stats[branch].update(
                        ak.to_numpy(ak.flatten(arrays[branch], axis=None))
                    )
                ecal_reference = arrays["ecal_energy"]
                for branch in ECAL_BRANCHES:
                    alignment_failures[f"ecal_energy_vs_{branch}"] += update_alignment(
                        ecal_reference, arrays[branch]
                    )
                hcal_reference = arrays["hcal_energy"]
                for branch in HCAL_BRANCHES:
                    alignment_failures[f"hcal_energy_vs_{branch}"] += update_alignment(
                        hcal_reference, arrays[branch]
                    )
                truth_reference = arrays["mcPar_PDG"]
                for branch in TRUTH_BRANCHES:
                    alignment_failures[f"mcPar_PDG_vs_{branch}"] += update_alignment(
                        truth_reference, arrays[branch]
                    )

                ecal_values = ak.to_numpy(ak.flatten(arrays["ecal_energy"], axis=None))
                hcal_values = ak.to_numpy(ak.flatten(arrays["hcal_energy"], axis=None))
                ecal_signal_stats.update(ecal_values)
                hcal_signal_stats.update(hcal_values)
                ecal_counts = ak.to_numpy(ak.num(ecal_reference, axis=1))
                hcal_counts = ak.to_numpy(ak.num(hcal_reference, axis=1))
                events_scanned += len(ecal_counts)
                if chunk_number % 10 == 0:
                    print(f"Processed {events_scanned} events", flush=True)
                ecal_hit_stats.update(ecal_counts)
                hcal_hit_stats.update(hcal_counts)
                ecal_sum = ak.to_numpy(ak.sum(ecal_reference, axis=1))
                hcal_sum = ak.to_numpy(ak.sum(hcal_reference, axis=1))

                ecal_ids = ak.to_numpy(ak.flatten(arrays["ecal_cellID"], axis=None))
                ecal_centers.update(
                    ecal_ids,
                    ak.to_numpy(ak.flatten(arrays["ecal_posX"], axis=None)),
                    ak.to_numpy(ak.flatten(arrays["ecal_posY"], axis=None)),
                    ak.to_numpy(ak.flatten(arrays["ecal_posZ"], axis=None)),
                )
                hcal_ids = ak.to_numpy(ak.flatten(arrays["hcal_cellID"], axis=None))
                hcal_layers = ak.to_numpy(ak.flatten(arrays["hcal_LayerID"], axis=None))
                hcal_centers.update(
                    hcal_layers.astype(np.int64) * 1_000_000 + hcal_ids.astype(np.int64),
                    ak.to_numpy(ak.flatten(arrays["hcal_posX"], axis=None)),
                    ak.to_numpy(ak.flatten(arrays["hcal_posY"], axis=None)),
                    ak.to_numpy(ak.flatten(arrays["hcal_posZ"], axis=None)),
                )

                pdg_values = ak.to_numpy(ak.flatten(arrays["mcPar_PDG"], axis=None))
                pdg_counts.update(int(value) for value in pdg_values)
                truth = selected_neutron_truth(arrays)
                neutron_count_histogram.update(int(value) for value in truth.pop("neutron_count"))
                update_event_vectors(
                    events,
                    {
                        **truth,
                        "ecal_hits": ecal_counts,
                        "hcal_hits": hcal_counts,
                        "ecal_sum_gev": ecal_sum,
                        "hcal_sum_gev": hcal_sum,
                    },
                )
                for label, branch, calculated in (
                    ("ecal", "energySum_ecal", ecal_sum),
                    ("hcal", "energySum_hcal", hcal_sum),
                    ("zdc", "energySum_ZDC", ecal_sum + hcal_sum),
                ):
                    sum_difference_stats[label].update(
                        scalar_from_jagged(arrays[branch]) - calculated
                    )

        decompression_executor.shutdown(wait=True)

        event_data = concat_event_vectors(events)
        raw_momentum = np.column_stack(
            [
                event_data["raw_mcpar_px"],
                event_data["raw_mcpar_py"],
                event_data["raw_mcpar_pz"],
            ]
        )
        energy_convention = infer_energy_convention(
            event_data["raw_mcpar_energy"], raw_momentum, mass_gev=NEUTRON_MASS_GEV
        )
        event_data.update(
            canonical_truth(
                event_data["raw_mcpar_energy"],
                raw_momentum,
                energy_convention,
                mass_gev=NEUTRON_MASS_GEV,
            )
        )
        stated_total_energy = event_data[
            "raw_mcpar_energy"
        ] * energy_convention.energy_scale_to_gev + (
            NEUTRON_MASS_GEV if energy_convention.semantics == "kinetic" else 0.0
        )
        stated_total_minus_on_shell = stated_total_energy - event_data["energy_true_gev"]
        event_count = len(event_data["energy_true_gev"])
        if event_count != 764940:
            raise AssertionError(f"Unexpected event count: {event_count}")
        if neutron_count_histogram.get(1, 0) != event_count:
            raise AssertionError(
                f"Expected exactly one neutron per event, found {dict(neutron_count_histogram)}"
            )
        ecal_frame = centers_dataframe(ecal_centers, args.position_scale_to_cm, include_layer=False)
        hcal_frame = centers_dataframe(hcal_centers, args.position_scale_to_cm, include_layer=True)
        ecal_frame.to_csv(tables_path / "ecal_cell_centers.csv", index=False)
        hcal_frame.to_csv(tables_path / "hcal_layer_cell_centers.csv", index=False)
        pd.DataFrame(catalog).to_csv(tables_path / "root_branch_catalog.csv", index=False)
        pd.DataFrame(sorted(pdg_counts.items()), columns=["pdg", "particles"]).to_csv(
            tables_path / "pdg_counts.csv", index=False
        )
        pd.DataFrame(
            [
                {"check": key, "events_with_mismatch": value}
                for key, value in sorted(alignment_failures.items())
            ]
        ).to_csv(tables_path / "jagged_alignment_checks.csv", index=False)

        sum_differences = {name: stats.to_dict() for name, stats in sum_difference_stats.items()}
        report = {
            "input_uri": args.input_uri,
            "input_gcs_metadata": input_info,
            "input_access": input_access,
            "selected_tree": args.tree_name,
            "events": event_count,
            "tree_cycles_and_objects": cycles,
            "root_histograms": object_histograms,
            "branch_count": len(catalog),
            "all_vector_branch_statistics": {
                branch: stats.to_dict() for branch, stats in all_vector_stats.items()
            },
            "neutron_mass_gev": NEUTRON_MASS_GEV,
            "truth": {
                "pdg_counts": dict(sorted(pdg_counts.items())),
                "neutron_count_per_event": dict(sorted(neutron_count_histogram.items())),
                "raw_mcpar_energy": summarize_values(event_data["raw_mcpar_energy"]),
                "raw_mcpar_energy_convention": energy_convention.to_dict(),
                "stated_total_minus_on_shell_gev": summarize_values(stated_total_minus_on_shell),
                "generator_energy_gev": summarize_values(event_data["generator_energy_gev"]),
                "energy_true_gev": summarize_values(event_data["energy_true_gev"]),
                "kinetic_energy_true_gev": summarize_values(event_data["kinetic_energy_true_gev"]),
                "theta_true_rad": summarize_values(event_data["theta_true_rad"]),
                "phi_true_rad": summarize_values(event_data["phi_true_rad"]),
                "focus_boundary_counts": {
                    "below_50_gev": int(np.sum(event_data["generator_energy_gev"] < 50.0)),
                    "in_50_to_250_gev_inclusive": int(
                        np.sum(
                            (event_data["generator_energy_gev"] >= 50.0)
                            & (event_data["generator_energy_gev"] <= 250.0)
                        )
                    ),
                    "above_250_gev": int(np.sum(event_data["generator_energy_gev"] > 250.0)),
                    "exactly_50_gev": int(np.sum(event_data["generator_energy_gev"] == 50.0)),
                    "exactly_250_gev": int(np.sum(event_data["generator_energy_gev"] == 250.0)),
                },
            },
            "hits": {
                "ecal_energy": ecal_signal_stats.to_dict(),
                "hcal_energy": hcal_signal_stats.to_dict(),
                "ecal_hits_per_event": ecal_hit_stats.to_dict(),
                "hcal_hits_per_event": hcal_hit_stats.to_dict(),
                "no_ecal_hits_events": int(np.sum(event_data["ecal_hits"] == 0)),
                "no_hcal_hits_events": int(np.sum(event_data["hcal_hits"] == 0)),
                "no_visible_signal_events": int(
                    np.sum((event_data["ecal_sum_gev"] + event_data["hcal_sum_gev"]) == 0.0)
                ),
                "stored_energy_sum_minus_calculated_sum": sum_differences,
            },
            "geometry": {
                "position_scale_to_cm": args.position_scale_to_cm,
                "ecal_unique_cell_ids": int(len(ecal_frame)),
                "hcal_unique_layer_cell_pairs": int(len(hcal_frame)),
                "hcal_unique_layers": int(hcal_frame["layer_id"].nunique()),
                "hcal_unique_cells_per_layer": {
                    str(int(layer)): int(count)
                    for layer, count in hcal_frame.groupby("layer_id")["cell_id"].nunique().items()
                },
                "ecal_center_axes": center_axis_summary(ecal_frame),
                "hcal_center_axes": center_axis_summary(hcal_frame),
                "ecal_cell_position_conflicts": ecal_centers.conflicts,
                "hcal_cell_position_conflicts": hcal_centers.conflicts,
            },
            "jagged_alignment_failures": dict(sorted(alignment_failures.items())),
        }
        write_json(reports_path / "mc_root_full_analysis.json", report)
        write_json(reports_path / "fast_mc_input_contract.json", fast_mc_contract(report))
        write_json(
            reports_path / "analysis_manifest.json",
            {
                "input_uri": args.input_uri,
                "output_uri": args.output_uri,
                "tree": args.tree_name,
                "events": event_count,
                "step_size": args.step_size,
                "position_scale_to_cm": args.position_scale_to_cm,
            },
        )
        make_plots(event_data, ecal_frame, hcal_frame, plots_path)
        upload_tree(temporary_path, args.output_uri)


if __name__ == "__main__":
    main()
