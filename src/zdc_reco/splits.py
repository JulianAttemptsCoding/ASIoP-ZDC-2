from __future__ import annotations

import hashlib

import numpy as np
import pandas as pd

SPLIT_NAMES = ("train", "validation", "test")


def composite_stratum(
    energy: np.ndarray,
    theta: np.ndarray,
    phi: np.ndarray,
    *,
    energy_edges: list[float],
    theta_bins: int,
    phi_bins: int,
) -> np.ndarray:
    e = np.clip(np.digitize(energy, energy_edges[1:-1]), 0, len(energy_edges) - 2)
    t_edges = np.linspace(float(np.nanmin(theta)), float(np.nanmax(theta)) + 1e-12, theta_bins + 1)
    p_edges = np.linspace(-np.pi, np.pi + 1e-12, phi_bins + 1)
    t = np.clip(np.digitize(theta, t_edges[1:-1]), 0, theta_bins - 1)
    p = np.clip(np.digitize(phi, p_edges[1:-1]), 0, phi_bins - 1)
    return np.asarray([f"e{ei}_t{ti}_p{pi}" for ei, ti, pi in zip(e, t, p, strict=True)])


def make_grouped_splits(
    frame: pd.DataFrame,
    *,
    seed: int,
    energy_edges: list[float],
    theta_bins: int = 8,
    phi_bins: int = 8,
) -> pd.Series:
    required = {"event_uid", "group_uid", "generator_energy_gev", "theta_true_rad", "phi_true_rad"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Missing split columns: {sorted(missing)}")
    strata = composite_stratum(
        frame["generator_energy_gev"].to_numpy(),
        frame["theta_true_rad"].to_numpy(),
        frame["phi_true_rad"].to_numpy(),
        energy_edges=energy_edges,
        theta_bins=theta_bins,
        phi_bins=phi_bins,
    )
    counts = pd.Series(strata).value_counts()
    rare = set(counts[counts < 10].index)
    if rare:
        strata = np.asarray(["rare" if value in rare else value for value in strata])
    groups = frame["group_uid"].astype(str).to_numpy()
    if len(np.unique(groups)) < 10:
        raise ValueError("At least ten independent groups are required for 80/10/10 splitting")
    group_frame = pd.DataFrame({"group_uid": groups, "stratum": strata})
    group_strata = (
        group_frame.groupby("group_uid", sort=False, observed=True)["stratum"]
        .agg(lambda values: values.mode().iat[0])
        .rename("stratum")
    )
    group_to_fold: dict[str, int] = {}
    for stratum, stratum_groups in group_strata.groupby(group_strata, sort=True):
        ordered_groups = stratum_groups.index.to_numpy(copy=True)
        digest = hashlib.sha256(f"{seed}:{stratum}".encode()).digest()
        rng = np.random.default_rng(int.from_bytes(digest[:8], "little"))
        rng.shuffle(ordered_groups)
        for offset, group in enumerate(ordered_groups):
            group_to_fold[str(group)] = offset % 10
    fold_id = np.asarray([group_to_fold[group] for group in groups], dtype=int)
    if np.any(fold_id < 0):
        raise RuntimeError("Some events were not assigned to a split fold")
    split = np.full(len(frame), "train", dtype=object)
    split[fold_id == 0] = "test"
    split[fold_id == 1] = "validation"
    result = pd.Series(split, index=frame.index, name="split")
    assert_split_integrity(frame.assign(split=result))
    return result


def assert_split_integrity(frame: pd.DataFrame) -> None:
    if frame["event_uid"].duplicated().any():
        raise ValueError("event_uid is not unique")
    group_counts = frame.groupby("group_uid", observed=True)["split"].nunique()
    if (group_counts > 1).any():
        raise ValueError("A source group crosses split boundaries")
    if set(frame["split"].unique()) != set(SPLIT_NAMES):
        raise ValueError("All three split names must be present")


def detector_fingerprint(values: np.ndarray) -> str:
    rounded = np.round(np.asarray(values, dtype=float), decimals=8)
    return hashlib.sha256(rounded.tobytes()).hexdigest()


def assert_no_duplicate_fingerprint_leakage(frame: pd.DataFrame) -> None:
    if "detector_fingerprint" not in frame:
        raise ValueError("detector_fingerprint column is required")
    crossing = frame.groupby("detector_fingerprint", observed=True)["split"].nunique()
    if (crossing > 1).any():
        raise ValueError(f"Exact detector duplicates cross splits: {int((crossing > 1).sum())}")
