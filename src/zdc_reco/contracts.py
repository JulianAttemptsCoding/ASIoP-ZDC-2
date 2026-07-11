from __future__ import annotations

from collections.abc import Iterable

import numpy as np

from .constants import TRUTH_COLUMNS


def require_equal_jagged_lengths(**arrays: Iterable[np.ndarray]) -> None:
    names = list(arrays)
    if not names:
        return
    event_counts = [len(arrays[name]) for name in names]
    if len(set(event_counts)) != 1:
        raise ValueError(
            "Event counts differ across jagged branches: "
            f"{dict(zip(names, event_counts, strict=True))}"
        )
    for event_index, values in enumerate(zip(*(arrays[name] for name in names), strict=True)):
        lengths = [len(np.asarray(v)) for v in values]
        if len(set(lengths)) != 1:
            raise ValueError(
                f"Jagged hit lengths differ at event {event_index}: "
                f"{dict(zip(names, lengths, strict=True))}"
            )


def assert_feature_provenance(feature_manifest: Iterable[dict]) -> None:
    for row in feature_manifest:
        name = str(row["feature"])
        sources = {str(v) for v in row.get("source_branches", [])}
        if name in TRUTH_COLUMNS or sources & TRUTH_COLUMNS:
            raise ValueError(f"Truth leakage in feature provenance: {name} <- {sorted(sources)}")
        if row.get("source_kind") not in {"detector", "geometry", "quality_flag"}:
            raise ValueError(f"Unapproved feature source kind for {name}: {row.get('source_kind')}")


def validate_hit_event(x: np.ndarray, y: np.ndarray, z: np.ndarray, signal: np.ndarray) -> None:
    arrays = [np.asarray(v) for v in (x, y, z, signal)]
    if len({len(v) for v in arrays}) != 1:
        raise ValueError("x/y/z/signal lengths differ within an event")
    if not all(np.all(np.isfinite(v)) for v in arrays):
        raise ValueError("Nonfinite hit coordinate or signal")
