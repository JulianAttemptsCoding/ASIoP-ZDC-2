from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REQUIRED_COMMANDS = (
    "preflight",
    "validate-schema",
    "build-targets",
    "make-splits",
    "build-scalars",
    "build-grids",
    "train-baselines",
    "train-xgb",
    "train-dual-grid",
    "evaluate-validation",
    "select-champion",
    "fit-calibration",
    "freeze-study",
    "unlock-test",
    "evaluate-test",
    "plot",
    "verify",
    "run-all",
)


@dataclass(frozen=True)
class RootMetadata:
    uri: str
    keys: list[str]
    trees: dict[str, Any]
    objects: dict[str, Any]


def _now_utc() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _ensure_report_dirs(output_dir: Path) -> tuple[Path, Path]:
    preflight_dir = output_dir / "preflight"
    report_dir = output_dir / "reports"
    preflight_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    return preflight_dir, report_dir


def inspect_root_metadata(uri: str) -> RootMetadata:
    import uproot

    trees: dict[str, Any] = {}
    objects: dict[str, Any] = {}
    with uproot.open(uri) as root_file:
        keys = list(root_file.keys())
        for key in keys:
            obj = root_file[key]
            record: dict[str, Any] = {
                "classname": obj.classname,
                "title": getattr(obj, "title", None),
            }
            if hasattr(obj, "num_entries"):
                record["num_entries"] = obj.num_entries
                record["branches"] = {
                    name: {
                        "typename": getattr(branch, "typename", None),
                        "title": getattr(branch, "title", None),
                    }
                    for name, branch in obj.items()
                }
                trees[key] = record
            else:
                objects[key] = record
    return RootMetadata(uri=uri, keys=keys, trees=trees, objects=objects)


def write_json(path: Path, payload: Any) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def write_blocker(report_dir: Path, *, data_uri: str, metadata_path: Path, reason: str) -> Path:
    path = report_dir / "BLOCKED.md"
    body = f"""# BLOCKED

Created UTC: {_now_utc()}

## Stop reason

{reason}

## Failing check

`docs/MASTER_QC_CHECKLIST.md` item 14 and `AGENT_PROMPT.md` Phase 1 require authoritative
ECAL/HCAL hit-signal meaning and GeV conversion from simulation metadata, simulation code, or data
documentation. The ROOT file branch titles expose only names such as `ecal_energy` and
`hcal_energy`; no units, thresholds, digitization semantics, or conversion rule are embedded.

## Evidence

- Input data URI: `{data_uri}`
- Metadata report: `{metadata_path}`
- ROOT metadata can be opened, but the metadata fields and histogram axes contain no hit-signal unit
  evidence.
- The repository and bucket search found no simulation source, detector macro, README, or data
  dictionary that defines `ecal_energy`/`hcal_energy` units.

## Smallest decision needed

Provide authoritative documentation or source code that states what `ecal_energy` and `hcal_energy`
represent and the conversion to GeV for absolute energy reconstruction. After that, rerun:

```bash
zdc-reco run-all --config configs/study.yaml --data {data_uri}
```

No training, calibration, test unlock, or performance claim is valid until this blocker is resolved.
"""
    path.write_text(body, encoding="utf-8")
    return path


def command_preflight(args: argparse.Namespace) -> int:
    output_dir = Path(args.output_dir)
    preflight_dir, report_dir = _ensure_report_dirs(output_dir)
    metadata = inspect_root_metadata(args.data)
    metadata_path = preflight_dir / "root_metadata.json"
    write_json(metadata_path, {
        "created_utc": _now_utc(),
        "config": args.config,
        "metadata": {
            "uri": metadata.uri,
            "keys": metadata.keys,
            "trees": metadata.trees,
            "objects": metadata.objects,
        },
    })
    if not args.hit_signal_unit_evidence:
        blocker = write_blocker(
            report_dir,
            data_uri=args.data,
            metadata_path=metadata_path,
            reason="Authoritative ECAL/HCAL hit-signal unit evidence was not supplied or found.",
        )
        print(f"BLOCKED: wrote {blocker}")
        return 2
    write_json(preflight_dir / "hit_signal_unit_evidence.json", {
        "created_utc": _now_utc(),
        "evidence": args.hit_signal_unit_evidence,
    })
    print(f"preflight metadata written to {metadata_path}")
    return 0


def command_verify(args: argparse.Namespace) -> int:
    output_dir = Path(args.output_dir)
    blocked = output_dir / "reports" / "BLOCKED.md"
    if blocked.exists():
        print(f"blocked study: {blocked}")
        return 2
    required = [
        output_dir / "reports" / "qa_ledger.md",
        output_dir / "preflight" / "root_metadata.json",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        print("missing verification artifacts:\n" + "\n".join(missing))
        return 2
    print("verification artifacts present")
    return 0


def command_run_all(args: argparse.Namespace) -> int:
    preflight_args = argparse.Namespace(
        config=args.config,
        data=args.data,
        output_dir=args.output_dir,
        hit_signal_unit_evidence=args.hit_signal_unit_evidence,
    )
    code = command_preflight(preflight_args)
    if code != 0:
        return code
    print("preflight passed; downstream production requires the full data-contract implementation")
    return 2


def command_fail_closed(args: argparse.Namespace) -> int:
    output_dir = Path(args.output_dir)
    blocked = output_dir / "reports" / "BLOCKED.md"
    if blocked.exists():
        print(f"{args.command} refused because the study is blocked: {blocked}")
        return 2
    print(f"{args.command} refused: required upstream production artifacts are absent")
    return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="zdc-reco")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in REQUIRED_COMMANDS:
        subparser = subparsers.add_parser(command)
        subparser.add_argument("--config", default="configs/study.yaml")
        subparser.add_argument("--output-dir", default="outputs")
        if command in {"preflight", "run-all"}:
            subparser.add_argument("--data", required=True)
            subparser.add_argument("--hit-signal-unit-evidence")
        if command == "preflight":
            subparser.set_defaults(func=command_preflight)
        elif command == "verify":
            subparser.set_defaults(func=command_verify)
        elif command == "run-all":
            subparser.set_defaults(func=command_run_all)
        else:
            subparser.set_defaults(func=command_fail_closed)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
