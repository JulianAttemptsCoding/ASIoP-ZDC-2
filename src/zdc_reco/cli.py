from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from .config import load_config
from .features import build_event_features
from .geometry import infer_detector_frame, validate_frame
from .physics import fourvector_from_kinetic_direction, mass_shell_residual
from .pipeline import (
    build_features,
    build_targets,
    calibrate,
    evaluate_test,
    make_splits,
    plot_outputs,
    select_model,
    train_baselines,
    train_xgb,
    unlock_test,
    validate_schema_command,
    verify_outputs,
)
from .rootio import inspect_root


def _synthetic_smoke() -> dict:
    rng = np.random.default_rng(20260710)
    ecal = rng.normal([0.0, 0.0, 0.0], [5.0, 5.0, 1.0], size=(2000, 3))
    hcal = rng.normal([0.0, 0.0, 90.0], [10.0, 10.0, 25.0], size=(5000, 3))
    frame = infer_detector_frame(ecal, hcal)
    validate_frame(frame)
    e_event = ecal[:30]
    h_event = hcal[:100]
    features = build_event_features(
        ecal_x=e_event[:, 0],
        ecal_y=e_event[:, 1],
        ecal_z=e_event[:, 2],
        ecal_signal_gev=np.abs(rng.normal(0.02, 0.01, len(e_event))),
        hcal_x=h_event[:, 0],
        hcal_y=h_event[:, 1],
        hcal_z=h_event[:, 2],
        hcal_signal_gev=np.abs(rng.normal(0.05, 0.03, len(h_event))),
        frame=frame,
    )
    direction = np.asarray([[0.01, -0.02, 1.0]])
    fourvector = fourvector_from_kinetic_direction(np.asarray([100.0]), direction)
    shell = mass_shell_residual(fourvector)
    if not np.max(np.abs(shell)) < 1e-10:
        raise RuntimeError("Synthetic mass-shell smoke test failed")
    return {"feature_count": len(features), "mass_shell_abs_max": float(np.max(np.abs(shell)))}


def main() -> None:
    parser = argparse.ArgumentParser(prog="zdc-reco")
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate-config", help="Validate configuration invariants")
    validate.add_argument("--config", default="configs/default.yaml")
    inspect = sub.add_parser("inspect-root", help="Inspect ROOT schema, truth units, and geometry")
    inspect.add_argument("--data", required=True)
    inspect.add_argument("--config", default="configs/default.yaml")
    inspect.add_argument("--output", default="outputs/preflight")
    schema = sub.add_parser("validate-schema", help="Validate locked schema fails closed")
    schema.add_argument("--schema", default="outputs/preflight/schema.lock.yaml")
    targets = sub.add_parser(
        "build-targets", help="Build truth/target table and detector fingerprints"
    )
    targets.add_argument("--data", required=True)
    targets.add_argument("--config", default="configs/default.yaml")
    targets.add_argument("--schema", default="outputs/preflight/schema.lock.yaml")
    targets.add_argument("--output-dir", default="outputs")
    targets.add_argument("--limit", type=int, default=None)
    splits = sub.add_parser("make-splits", help="Create grouped 80/10/10 splits")
    splits.add_argument("--config", default="configs/default.yaml")
    splits.add_argument("--output-dir", default="outputs")
    features = sub.add_parser("build-features", help="Build detector feature table")
    features.add_argument("--data", required=True)
    features.add_argument("--config", default="configs/default.yaml")
    features.add_argument("--schema", default="outputs/preflight/schema.lock.yaml")
    features.add_argument("--output-dir", default="outputs")
    features.add_argument("--limit", type=int, default=None)
    baselines = sub.add_parser("train-baselines", help="Train B0/B1 and direct diagnostic baseline")
    baselines.add_argument("--config", default="configs/default.yaml")
    baselines.add_argument("--schema", default="outputs/preflight/schema.lock.yaml")
    baselines.add_argument("--output-dir", default="outputs")
    xgb = sub.add_parser("train-xgb", help="Train constrained XGBoost support ablation")
    xgb.add_argument("--config", default="configs/default.yaml")
    xgb.add_argument("--schema", default="outputs/preflight/schema.lock.yaml")
    xgb.add_argument("--output-dir", default="outputs")
    select = sub.add_parser("select-model", help="Freeze validation-selected champion")
    select.add_argument("--output-dir", default="outputs")
    cal = sub.add_parser("calibrate", help="Fit final validation response and empirical intervals")
    cal.add_argument("--config", default="configs/default.yaml")
    cal.add_argument("--output-dir", default="outputs")
    unlock = sub.add_parser("unlock-test", help="Write one-time test unlock record")
    unlock.add_argument("--output-dir", default="outputs")
    test = sub.add_parser("evaluate-test", help="Evaluate champion on locked test split")
    test.add_argument("--config", default="configs/default.yaml")
    test.add_argument("--output-dir", default="outputs")
    plot = sub.add_parser("plot", help="Regenerate plots from saved predictions")
    plot.add_argument("--output-dir", default="outputs")
    verify = sub.add_parser("verify", help="Verify required artifacts")
    verify.add_argument("--schema", default="outputs/preflight/schema.lock.yaml")
    verify.add_argument("--output-dir", default="outputs")
    run_all = sub.add_parser("run-all", help="Run the full locked local pipeline")
    run_all.add_argument("--data", required=True)
    run_all.add_argument("--config", default="configs/default.yaml")
    run_all.add_argument("--output-dir", default="outputs")
    run_all_gcs = sub.add_parser("run-all-gcs", help="Run full pipeline with GCS data/output")
    run_all_gcs.add_argument("--data-gcs", required=True)
    run_all_gcs.add_argument("--output-gcs", required=True)
    run_all_gcs.add_argument("--config", default="configs/default.yaml")
    run_all_gcs.add_argument("--workdir", default="/tmp/zdc_run")
    resume_training_gcs = sub.add_parser(
        "resume-training-gcs", help="Rerun training/evaluation from existing GCS artifacts"
    )
    resume_training_gcs.add_argument("--source-gcs", required=True)
    resume_training_gcs.add_argument("--output-gcs", required=True)
    resume_training_gcs.add_argument("--config", default="configs/default.yaml")
    resume_training_gcs.add_argument("--workdir", default="/tmp/zdc_resume")
    sub.add_parser("synthetic-smoke", help="Run dependency-light physics and feature smoke checks")
    args = parser.parse_args()
    if args.command == "validate-config":
        cfg = load_config(args.config)
        print(json.dumps({"status": "ok", "project": cfg["project"]["name"]}, indent=2))
    elif args.command == "inspect-root":
        report = inspect_root(args.data, args.config, args.output)
        print(json.dumps(report, indent=2, sort_keys=True))
    elif args.command == "validate-schema":
        print(json.dumps(validate_schema_command(args.schema), indent=2, sort_keys=True))
    elif args.command == "build-targets":
        print(
            json.dumps(
                build_targets(
                    data=args.data,
                    config=args.config,
                    schema_path=args.schema,
                    output_dir=args.output_dir,
                    limit=args.limit,
                ),
                indent=2,
                sort_keys=True,
            )
        )
    elif args.command == "make-splits":
        print(json.dumps(make_splits(config=args.config, output_dir=args.output_dir), indent=2))
    elif args.command == "build-features":
        print(
            json.dumps(
                build_features(
                    data=args.data,
                    config=args.config,
                    schema_path=args.schema,
                    output_dir=args.output_dir,
                    limit=args.limit,
                ),
                indent=2,
                sort_keys=True,
            )
        )
    elif args.command == "train-baselines":
        print(
            json.dumps(
                train_baselines(
                    config=args.config,
                    schema_path=args.schema,
                    output_dir=args.output_dir,
                ),
                indent=2,
                sort_keys=True,
            )
        )
    elif args.command == "train-xgb":
        print(
            json.dumps(
                train_xgb(config=args.config, schema_path=args.schema, output_dir=args.output_dir),
                indent=2,
                sort_keys=True,
            )
        )
    elif args.command == "select-model":
        print(json.dumps(select_model(output_dir=args.output_dir), indent=2, sort_keys=True))
    elif args.command == "calibrate":
        print(json.dumps(calibrate(config=args.config, output_dir=args.output_dir), indent=2))
    elif args.command == "unlock-test":
        print(json.dumps(unlock_test(output_dir=args.output_dir), indent=2, sort_keys=True))
    elif args.command == "evaluate-test":
        print(json.dumps(evaluate_test(config=args.config, output_dir=args.output_dir), indent=2))
    elif args.command == "plot":
        print(json.dumps(plot_outputs(output_dir=args.output_dir), indent=2, sort_keys=True))
    elif args.command == "verify":
        print(
            json.dumps(
                verify_outputs(output_dir=args.output_dir, schema_path=args.schema),
                indent=2,
                sort_keys=True,
            )
        )
    elif args.command == "run-all":
        preflight = str(Path(args.output_dir) / "preflight")
        schema_path = str(Path(preflight) / "schema.lock.yaml")
        inspect_root(args.data, args.config, preflight)
        validate_schema_command(schema_path)
        build_targets(
            data=args.data, config=args.config, schema_path=schema_path, output_dir=args.output_dir
        )
        make_splits(config=args.config, output_dir=args.output_dir)
        build_features(
            data=args.data, config=args.config, schema_path=schema_path, output_dir=args.output_dir
        )
        train_baselines(config=args.config, schema_path=schema_path, output_dir=args.output_dir)
        train_xgb(config=args.config, schema_path=schema_path, output_dir=args.output_dir)
        select_model(output_dir=args.output_dir)
        calibrate(config=args.config, output_dir=args.output_dir)
        unlock_test(output_dir=args.output_dir)
        evaluate_test(config=args.config, output_dir=args.output_dir)
        plot_outputs(output_dir=args.output_dir)
        print(
            json.dumps(
                verify_outputs(output_dir=args.output_dir, schema_path=schema_path),
                indent=2,
                sort_keys=True,
            )
        )
    elif args.command == "run-all-gcs":
        from .pipeline import run_all_gcs as run_all_gcs_command

        print(
            json.dumps(
                run_all_gcs_command(
                    data_gcs=args.data_gcs,
                    output_gcs=args.output_gcs,
                    config=args.config,
                    workdir=args.workdir,
                ),
                indent=2,
                sort_keys=True,
            )
        )
    elif args.command == "resume-training-gcs":
        from .pipeline import resume_training_gcs as resume_training_gcs_command

        print(
            json.dumps(
                resume_training_gcs_command(
                    source_gcs=args.source_gcs,
                    output_gcs=args.output_gcs,
                    config=args.config,
                    workdir=args.workdir,
                ),
                indent=2,
                sort_keys=True,
            )
        )
    elif args.command == "synthetic-smoke":
        print(json.dumps(_synthetic_smoke(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
