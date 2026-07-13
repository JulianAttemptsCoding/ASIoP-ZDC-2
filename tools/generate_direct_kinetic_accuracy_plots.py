"""Create direct-kinetic XGBoost accuracy diagnostics from saved Vertex artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import r2_score

MASS_GEV = 0.93956542052
BINS_GEV = np.arange(50.0, 251.0, 25.0)
COMPONENTS = (
    ("E", "E_total_hat", "energy_true_gev"),
    ("px", "px_hat", "px_true_gev"),
    ("py", "py_hat", "py_true_gev"),
    ("pz", "pz_hat", "pz_true_gev"),
)
COLORS = ("#1976d2", "#e26d24", "#2e8b57", "#c62828")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument(
        "--plots-dir", type=Path, default=Path("outputs/plots/direct_kinetic_accuracy")
    )
    parser.add_argument(
        "--reports-dir", type=Path, default=Path("outputs/reports/direct_kinetic_accuracy")
    )
    return parser.parse_args()


def configure() -> None:
    plt.rcParams.update(
        {
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "axes.grid.axis": "y",
            "grid.color": "#d9dde3",
            "grid.linewidth": 0.7,
            "font.size": 10,
            "axes.titlesize": 12,
            "figure.titlesize": 15,
            "savefig.dpi": 180,
        }
    )


def read_json(path: Path) -> dict[str, float]:
    return json.loads(path.read_text(encoding="utf-8"))


def attach_truth(predictions: pd.DataFrame, targets: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "event_uid",
        "energy_true_gev",
        "px_true_gev",
        "py_true_gev",
        "pz_true_gev",
        "visible_signal_gev",
        "ux_true",
        "uy_true",
        "uz_true",
    ]
    result = predictions.merge(targets[columns], on="event_uid", how="left", validate="one_to_one")
    if result["energy_true_gev"].isna().any():
        raise ValueError("Prediction-to-target join has missing truth rows")
    focus = result.loc[result["generator_energy_gev"].between(50.0, 250.0, inclusive="both")].copy()
    if len(focus) == 0:
        raise ValueError("No 50-250 GeV focus rows found")
    return focus


def annotate(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    for label, pred_col, true_col in COMPONENTS:
        residual = result[pred_col].to_numpy() - result[true_col].to_numpy()
        result[f"residual_{label}"] = residual
        result[f"norm_residual_{label}"] = residual / result["energy_true_gev"].to_numpy()
    p_pred = result[["px_hat", "py_hat", "pz_hat"]].to_numpy()
    p_true = result[["px_true_gev", "py_true_gev", "pz_true_gev"]].to_numpy()
    direction_pred = p_pred / np.linalg.norm(p_pred, axis=1, keepdims=True)
    direction_true = p_true / np.linalg.norm(p_true, axis=1, keepdims=True)
    cosine = np.clip(np.sum(direction_pred * direction_true, axis=1), -1.0, 1.0)
    result["angular_mrad"] = np.arccos(cosine) * 1000.0
    result["mass_shell_gev2"] = (
        result["E_total_hat"].to_numpy() ** 2 - np.sum(p_pred**2, axis=1) - MASS_GEV**2
    )
    return result


def component_metrics(frame: pd.DataFrame, sample: str) -> pd.DataFrame:
    rows: list[dict[str, float | str | int]] = []
    for label, pred_col, true_col in COMPONENTS:
        prediction = frame[pred_col].to_numpy()
        truth = frame[true_col].to_numpy()
        residual = prediction - truth
        normalized = residual / frame["energy_true_gev"].to_numpy()
        slope, intercept = np.polyfit(truth, prediction, 1)
        rows.append(
            {
                "sample": sample,
                "component": label,
                "events": len(frame),
                "mse_gev2": float(np.mean(residual**2)),
                "rmse_gev": float(np.sqrt(np.mean(residual**2))),
                "mae_gev": float(np.mean(np.abs(residual))),
                "bias_gev": float(np.mean(residual)),
                "residual_sd_gev": float(np.std(residual)),
                "abs_error_68_gev": float(np.quantile(np.abs(residual), 0.68)),
                "abs_error_90_gev": float(np.quantile(np.abs(residual), 0.90)),
                "abs_error_95_gev": float(np.quantile(np.abs(residual), 0.95)),
                "normalized_mse": float(np.mean(normalized**2)),
                "normalized_rmse": float(np.sqrt(np.mean(normalized**2))),
                "normalized_mae": float(np.mean(np.abs(normalized))),
                "normalized_bias": float(np.mean(normalized)),
                "abs_normalized_68": float(np.quantile(np.abs(normalized), 0.68)),
                "abs_normalized_95": float(np.quantile(np.abs(normalized), 0.95)),
                "r2": float(r2_score(truth, prediction)),
                "pearson_r": float(np.corrcoef(truth, prediction)[0, 1]),
                "slope": float(slope),
                "intercept_gev": float(intercept),
                "within_1gev": float(np.mean(np.abs(residual) <= 1.0)),
                "within_5gev": float(np.mean(np.abs(residual) <= 5.0)),
                "within_10gev": float(np.mean(np.abs(residual) <= 10.0)),
                "within_1pct_energy": float(np.mean(np.abs(normalized) <= 0.01)),
                "within_5pct_energy": float(np.mean(np.abs(normalized) <= 0.05)),
                "within_10pct_energy": float(np.mean(np.abs(normalized) <= 0.10)),
            }
        )
    return pd.DataFrame(rows)


def slice_metrics(frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, float | int]] = []
    energy = frame["energy_true_gev"].to_numpy()
    for low, high in zip(BINS_GEV[:-1], BINS_GEV[1:], strict=True):
        mask = (energy >= low) & ((energy < high) | (high == BINS_GEV[-1]))
        part = frame.loc[mask]
        relative_energy = part["norm_residual_E"].to_numpy()
        row: dict[str, float | int] = {
            "bin_low_gev": low,
            "bin_high_gev": high,
            "bin_center_gev": (low + high) / 2.0,
            "events": len(part),
            "response_mean": float(np.mean(part["E_total_hat"] / part["energy_true_gev"])),
            "response_median": float(np.median(part["E_total_hat"] / part["energy_true_gev"])),
            "energy_bias_gev": float(np.mean(part["residual_E"])),
            "energy_mae_gev": float(np.mean(np.abs(part["residual_E"]))),
            "energy_relative_rmse": float(np.sqrt(np.mean(relative_energy**2))),
            "energy_abs_relative_68": float(np.quantile(np.abs(relative_energy), 0.68)),
            "angular_median_mrad": float(np.quantile(part["angular_mrad"], 0.50)),
            "angular_68_mrad": float(np.quantile(part["angular_mrad"], 0.68)),
            "angular_95_mrad": float(np.quantile(part["angular_mrad"], 0.95)),
        }
        for label, _, _ in COMPONENTS:
            values = part[f"norm_residual_{label}"].to_numpy()
            row[f"{label}_normalized_rmse"] = float(np.sqrt(np.mean(values**2)))
            row[f"{label}_normalized_bias"] = float(np.mean(values))
        rows.append(row)
    return pd.DataFrame(rows)


def save(fig: plt.Figure, path: Path) -> None:
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def bars(ax: plt.Axes, data: pd.DataFrame, columns: list[str], title: str, ylabel: str) -> None:
    x = np.arange(len(data))
    width = 0.8 / len(columns)
    for index, column in enumerate(columns):
        offset = (index - (len(columns) - 1) / 2.0) * width
        ax.bar(x + offset, data[column], width, label=column, color=COLORS[index])
    ax.set_xticks(x, data["component"])
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.legend(frameon=False, fontsize=8)


def plot_pred_true(frame: pd.DataFrame, path: Path) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    for ax, (label, pred_col, true_col) in zip(axes.flat, COMPONENTS, strict=True):
        prediction, truth = frame[pred_col].to_numpy(), frame[true_col].to_numpy()
        lo, hi = min(prediction.min(), truth.min()), max(prediction.max(), truth.max())
        hexbin = ax.hexbin(truth, prediction, gridsize=85, mincnt=1, bins="log", cmap="Blues")
        ax.plot([lo, hi], [lo, hi], color=COLORS[3], linewidth=1.0)
        ax.set_title(f"{label}: predicted versus true")
        ax.set_xlabel(f"True {label} [GeV]")
        ax.set_ylabel(f"Direct-K predicted {label} [GeV]")
        fig.colorbar(hexbin, ax=ax, label="log10(events)")
    fig.suptitle("Direct-kinetic XGBoost: reconstructed locked focus-test components")
    save(fig, path)


def plot_residuals(frame: pd.DataFrame, path: Path) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(12, 9))
    limits = {"E": (-120, 120), "px": (-35, 35), "py": (-35, 35), "pz": (-120, 120)}
    for ax, (label, _, _) in zip(axes.flat, COMPONENTS, strict=True):
        residual = frame[f"residual_{label}"].to_numpy()
        ax.hist(residual, bins=120, range=limits[label], color=COLORS[0], alpha=0.84)
        ax.axvline(0.0, color=COLORS[3], linewidth=1.0)
        ax.axvline(np.mean(residual), color=COLORS[1], linestyle="--", linewidth=1.0)
        ax.set_title(f"{label} residual")
        ax.set_xlabel("Prediction - truth [GeV]")
        ax.set_ylabel("Events")
    fig.suptitle("Direct-kinetic XGBoost: component residual distributions")
    save(fig, path)


def plot_component_metrics(metrics: pd.DataFrame, path: Path) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8))
    bars(axes[0], metrics, ["mae_gev", "rmse_gev"], "Absolute error", "GeV")
    bars(axes[1], metrics, ["mse_gev2"], "Squared error", "GeV^2")
    axes[1].set_yscale("log")
    bars(axes[2], metrics, ["bias_gev", "residual_sd_gev"], "Bias and residual spread", "GeV")
    fig.suptitle("Direct-kinetic XGBoost: physical-unit component accuracy")
    save(fig, path)


def plot_normalized_metrics(metrics: pd.DataFrame, path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    bars(
        axes[0],
        metrics,
        ["normalized_rmse", "normalized_mae", "normalized_bias"],
        "Energy-normalized residual metrics",
        "Residual / E_true",
    )
    bars(axes[1], metrics, ["r2", "pearson_r", "slope"], "Response regression metrics", "Value")
    axes[1].set_ylim(0.0, 1.05)
    fig.suptitle("Direct-kinetic XGBoost: normalized accuracy and response")
    save(fig, path)


def plot_tolerances(metrics: pd.DataFrame, path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    bars(
        axes[0],
        metrics,
        ["within_1gev", "within_5gev", "within_10gev"],
        "Absolute tolerance fractions",
        "Fraction of focus-test events",
    )
    bars(
        axes[1],
        metrics,
        ["within_1pct_energy", "within_5pct_energy", "within_10pct_energy"],
        "Energy-scaled tolerance fractions",
        "Fraction of focus-test events",
    )
    for axis in axes:
        axis.set_ylim(0.0, 1.05)
        axis.yaxis.set_major_formatter(lambda value, _: f"{100 * value:.0f}%")
    fig.suptitle("Direct-kinetic XGBoost: explicit tolerance accuracy")
    save(fig, path)


def plot_energy_slices(slices: pd.DataFrame, path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    center = slices["bin_center_gev"]
    axes[0].plot(center, slices["response_mean"], "o-", label="mean", color=COLORS[0])
    axes[0].plot(center, slices["response_median"], "s--", label="median", color=COLORS[1])
    axes[0].axhline(1.0, color="black", linewidth=0.9)
    axes[0].set_title("Energy response")
    axes[0].set_xlabel("True energy bin center [GeV]")
    axes[0].set_ylabel("E_pred / E_true")
    axes[0].legend(frameon=False)
    axes[1].plot(
        center, slices["energy_relative_rmse"], "o-", label="relative RMSE", color=COLORS[3]
    )
    axes[1].plot(
        center,
        slices["energy_abs_relative_68"],
        "s--",
        label="68% abs. relative error",
        color=COLORS[2],
    )
    axes[1].set_title("Energy resolution")
    axes[1].set_xlabel("True energy bin center [GeV]")
    axes[1].set_ylabel("Relative error")
    axes[1].legend(frameon=False)
    fig.suptitle("Direct-kinetic XGBoost: energy response and resolution by true-energy slice")
    save(fig, path)


def plot_component_slices(slices: pd.DataFrame, path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    for index, (label, _, _) in enumerate(COMPONENTS):
        axes[0].plot(
            slices["bin_center_gev"],
            slices[f"{label}_normalized_rmse"],
            "o-",
            color=COLORS[index],
            label=label,
        )
        axes[1].plot(
            slices["bin_center_gev"],
            slices[f"{label}_normalized_bias"],
            "o-",
            color=COLORS[index],
            label=label,
        )
    axes[0].set_title("Component normalized RMSE")
    axes[0].set_xlabel("True energy bin center [GeV]")
    axes[0].set_ylabel("RMSE((prediction - truth) / E_true)")
    axes[1].set_title("Component normalized bias")
    axes[1].set_xlabel("True energy bin center [GeV]")
    axes[1].set_ylabel("Mean((prediction - truth) / E_true)")
    for axis in axes:
        axis.legend(frameon=False, ncol=2)
    fig.suptitle("Direct-kinetic XGBoost: four-vector component errors by true-energy slice")
    save(fig, path)


def plot_energy_density(frame: pd.DataFrame, path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    left = axes[0].hexbin(
        frame["energy_true_gev"],
        frame["residual_E"],
        gridsize=75,
        mincnt=1,
        bins="log",
        cmap="Blues",
    )
    axes[0].axhline(0.0, color=COLORS[3], linewidth=1.0)
    axes[0].set_title("Energy residual density")
    axes[0].set_xlabel("True energy [GeV]")
    axes[0].set_ylabel("E prediction - truth [GeV]")
    fig.colorbar(left, ax=axes[0], label="log10(events)")
    response = frame["E_total_hat"] / frame["energy_true_gev"]
    right = axes[1].hexbin(
        frame["energy_true_gev"], response, gridsize=75, mincnt=1, bins="log", cmap="Blues"
    )
    axes[1].axhline(1.0, color=COLORS[3], linewidth=1.0)
    axes[1].set_title("Energy response density")
    axes[1].set_xlabel("True energy [GeV]")
    axes[1].set_ylabel("E_pred / E_true")
    fig.colorbar(right, ax=axes[1], label="log10(events)")
    fig.suptitle("Direct-kinetic XGBoost: locked focus-test energy-density diagnostics")
    save(fig, path)


def plot_angular(frame: pd.DataFrame, slices: pd.DataFrame, path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    angular = frame["angular_mrad"].to_numpy()
    axes[0].hist(angular, bins=120, range=(0, 45), color=COLORS[0], alpha=0.84)
    for quantile, color, label in [
        (0.50, COLORS[2], "median"),
        (0.68, COLORS[1], "68%"),
        (0.95, COLORS[3], "95%"),
    ]:
        axes[0].axvline(np.quantile(angular, quantile), color=color, linestyle="--", label=label)
    axes[0].set_title("Angular residual distribution")
    axes[0].set_xlabel("Angle between predicted and true momentum [mrad]")
    axes[0].set_ylabel("Events")
    axes[0].legend(frameon=False)
    for column, color, label in [
        ("angular_median_mrad", COLORS[2], "median"),
        ("angular_68_mrad", COLORS[1], "68%"),
        ("angular_95_mrad", COLORS[3], "95%"),
    ]:
        axes[1].plot(slices["bin_center_gev"], slices[column], "o-", color=color, label=label)
    axes[1].set_title("Angular residual by energy slice")
    axes[1].set_xlabel("True energy bin center [GeV]")
    axes[1].set_ylabel("Angular error [mrad]")
    axes[1].legend(frameon=False)
    fig.suptitle("Direct-kinetic XGBoost: direction reconstruction accuracy")
    save(fig, path)


def plot_shell(frame: pd.DataFrame, path: Path) -> None:
    residual = frame["mass_shell_gev2"].to_numpy()
    edge = max(float(np.quantile(np.abs(residual), 0.999)), 1e-13)
    fig, axis = plt.subplots(figsize=(9.5, 5))
    axis.hist(residual, bins=100, range=(-edge, edge), color=COLORS[0], alpha=0.84)
    axis.axvline(0.0, color=COLORS[3], linewidth=1.0)
    axis.set_title("Direct-kinetic XGBoost: reconstructed mass-shell residual")
    axis.set_xlabel("E_pred^2 - |p_pred|^2 - m_n^2 [GeV^2]")
    axis.set_ylabel("Events")
    axis.text(
        0.98,
        0.94,
        f"max |residual| = {np.max(np.abs(residual)):.3e} GeV^2",
        transform=axis.transAxes,
        ha="right",
        va="top",
    )
    save(fig, path)


def plot_coverage(coverage: dict[str, float], path: Path) -> None:
    nominal = np.array([0.68, 0.90, 0.95])
    observed = np.array([coverage["0.68"], coverage["0.9"], coverage["0.95"]])
    labels = ["68%", "90%", "95%"]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    axes[0].bar(labels, observed, color=COLORS[0], label="locked-test coverage")
    axes[0].plot(labels, nominal, "o--", color=COLORS[1], label="nominal interval")
    axes[0].set_title("Empirical interval coverage")
    axes[0].set_ylabel("Fraction of focus-test events")
    axes[0].set_ylim(0.6, 1.0)
    axes[0].legend(frameon=False)
    axes[1].bar(labels, observed - nominal, color=COLORS[2])
    axes[1].axhline(0.0, color="black", linewidth=0.9)
    axes[1].set_title("Coverage residual")
    axes[1].set_ylabel("Observed - nominal coverage")
    for axis in axes:
        axis.yaxis.set_major_formatter(lambda value, _: f"{100 * value:.0f}%")
    fig.suptitle("Direct-kinetic XGBoost: validation-derived energy intervals on locked focus test")
    save(fig, path)


def plot_validation_test(validation: pd.DataFrame, test: pd.DataFrame, path: Path) -> None:
    merged = validation.merge(test, on="component", suffixes=("_validation", "_test"))
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8))
    for axis, metric, label in [
        (axes[0], "mae_gev", "MAE [GeV]"),
        (axes[1], "normalized_rmse", "Normalized RMSE"),
        (axes[2], "r2", "R^2"),
    ]:
        x = np.arange(len(merged))
        axis.bar(
            x - 0.18, merged[f"{metric}_validation"], 0.36, label="validation", color=COLORS[1]
        )
        axis.bar(x + 0.18, merged[f"{metric}_test"], 0.36, label="locked test", color=COLORS[0])
        axis.set_xticks(x, merged["component"])
        axis.set_title(label)
        axis.legend(frameon=False)
    axes[2].set_ylim(0.0, 1.05)
    fig.suptitle(
        "Direct-kinetic XGBoost: calibrated validation and locked focus-test component metrics"
    )
    save(fig, path)


def plot_leaderboard(leaderboard: pd.DataFrame, path: Path) -> None:
    display = leaderboard.copy()
    display["label"] = display["model_id"].str.replace("_", " ", regex=False)
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    for axis, column, title in [
        (
            axes[0],
            "macro_rms_relative_fourvector_error",
            "Validation macro RMS relative four-vector error",
        ),
        (axes[1], "energy_relative_rmse", "Validation energy relative RMSE"),
        (axes[2], "energy_mae_gev", "Validation energy MAE [GeV]"),
    ]:
        color = [COLORS[0] if deployable else "#7d8793" for deployable in display["deployable"]]
        axis.barh(display["label"], display[column], color=color)
        axis.set_title(title)
        axis.invert_yaxis()
        axis.grid(axis="x")
        axis.grid(axis="y", visible=False)
    fig.suptitle("Direct-kinetic Vertex run: validation candidate metrics")
    save(fig, path)


def plot_signal_dependence(frame: pd.DataFrame, path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    absolute_error = np.abs(frame["residual_E"].to_numpy())
    left = axes[0].hexbin(
        frame["energy_true_gev"],
        frame["visible_signal_gev"],
        C=absolute_error,
        reduce_C_function=np.mean,
        gridsize=55,
        mincnt=3,
        cmap="viridis",
    )
    axes[0].set_title("Mean absolute energy error")
    axes[0].set_xlabel("True energy [GeV]")
    axes[0].set_ylabel("ECAL + HCAL visible signal [GeV]")
    fig.colorbar(left, ax=axes[0], label="Mean |E_pred - E_true| [GeV]")
    response = frame["E_total_hat"] / frame["energy_true_gev"]
    right = axes[1].hexbin(
        frame["energy_true_gev"],
        frame["visible_signal_gev"],
        C=response,
        reduce_C_function=np.mean,
        gridsize=55,
        mincnt=3,
        cmap="viridis",
        vmin=0.85,
        vmax=1.15,
    )
    axes[1].set_title("Mean energy response")
    axes[1].set_xlabel("True energy [GeV]")
    axes[1].set_ylabel("ECAL + HCAL visible signal [GeV]")
    fig.colorbar(right, ax=axes[1], label="Mean E_pred / E_true")
    fig.suptitle("Direct-kinetic XGBoost: energy accuracy across visible-signal phase space")
    save(fig, path)


def plot_residual_correlation(frame: pd.DataFrame, path: Path) -> None:
    names = [f"residual_{label}" for label, _, _ in COMPONENTS]
    correlation = frame[names].corr().to_numpy()
    fig, axis = plt.subplots(figsize=(6.2, 5.6))
    image = axis.imshow(correlation, cmap="coolwarm", vmin=-1.0, vmax=1.0)
    axis.set_xticks(range(4), ["E", "px", "py", "pz"])
    axis.set_yticks(range(4), ["E", "px", "py", "pz"])
    for row in range(4):
        for column in range(4):
            axis.text(column, row, f"{correlation[row, column]:.3f}", ha="center", va="center")
    axis.set_title("Direct-kinetic XGBoost: component residual correlation")
    fig.colorbar(image, ax=axis, label="Pearson correlation")
    save(fig, path)


def qa(frame: pd.DataFrame, metrics: pd.DataFrame, saved: dict[str, float]) -> dict[str, float]:
    energy = metrics.loc[metrics["component"] == "E"].iloc[0]
    checks = {
        "energy_mae_gev": float(energy["mae_gev"]),
        "energy_relative_rmse": float(energy["normalized_rmse"]),
        "angular_median_mrad": float(np.quantile(frame["angular_mrad"], 0.50)),
        "angular_68_mrad": float(np.quantile(frame["angular_mrad"], 0.68)),
        "angular_95_mrad": float(np.quantile(frame["angular_mrad"], 0.95)),
        "mass_shell_residual_abs_max_gev2": float(np.max(np.abs(frame["mass_shell_gev2"]))),
    }
    for key, value in checks.items():
        if not np.isclose(value, float(saved[key]), rtol=1e-9, atol=1e-11):
            raise AssertionError(f"Saved Vertex metric mismatch for {key}: {value} != {saved[key]}")
    return checks


def write_reports(
    reports: Path,
    test: pd.DataFrame,
    validation: pd.DataFrame,
    slices: pd.DataFrame,
    saved: dict[str, float],
    coverage: dict[str, float],
    checks: dict[str, float],
) -> None:
    test.to_csv(reports / "direct_kinetic_focus_test_component_metrics.csv", index=False)
    validation.to_csv(
        reports / "direct_kinetic_validation_focus_component_metrics.csv", index=False
    )
    slices.to_csv(reports / "direct_kinetic_focus_energy_slice_metrics.csv", index=False)
    summary = {
        "model": "M1_xgb_focus_only",
        "target": "kinetic_energy",
        "evaluation": "locked 50-250 GeV focus test",
        "events": int(saved["focus_events"]),
        "saved_vertex_focus_metrics": saved,
        "empirical_interval_coverage": coverage,
        "recalculation_qa": checks,
        "not_available": (
            "The direct-kinetic Vertex artifact set does not persist per-boosting loss curves."
        ),
    }
    (reports / "direct_kinetic_accuracy_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    content = "\n".join(
        [
            "# Direct-kinetic XGBoost accuracy diagnostics",
            "",
            "Plots use calibrated M1_xgb_focus_only outputs from the completed direct-kinetic",
            "Vertex job. Predictions are joined to the locked target table by event_uid and",
            "filtered to 50-250 GeV.",
            "All component quantities are reconstructed physical GeV values.",
            "",
            "Regression has no classification accuracy. Tolerance figures report explicit",
            "fractions within 1, 5, and 10 GeV and within 1%, 5%, and 10% of true total energy.",
            "Normalized momentum residuals use (prediction - truth) / E_true to avoid singular",
            "values at px or py near zero.",
            "",
            "The generator validates energy MAE, energy-relative RMSE, angular quantiles, and",
            "maximum mass-shell residual against saved focus_test_metrics.json before",
            "writing plots.",
            "Per-boosting loss curves were not persisted in the direct-kinetic output artifacts.",
            "",
        ]
    )
    (reports / "README.md").write_text(content, encoding="utf-8")


def make_montage(plots: Path) -> None:
    from PIL import Image, ImageDraw

    images = []
    for path in sorted(plots.glob("*.png")):
        if path.name.startswith("00_"):
            continue
        image = Image.open(path).convert("RGB")
        image.thumbnail((430, 260))
        tile = Image.new("RGB", (450, 300), "white")
        tile.paste(image, ((450 - image.width) // 2, 10))
        ImageDraw.Draw(tile).text((12, 275), path.stem.replace("_", " "), fill="black")
        images.append(tile)
    columns = 3
    rows = int(np.ceil(len(images) / columns))
    montage = Image.new("RGB", (columns * 450, rows * 300), "#f5f6f8")
    for index, image in enumerate(images):
        montage.paste(image, ((index % columns) * 450, (index // columns) * 300))
    montage.save(plots / "00_direct_kinetic_accuracy_montage.png")


def main() -> None:
    args = parse_args()
    configure()
    args.plots_dir.mkdir(parents=True, exist_ok=True)
    args.reports_dir.mkdir(parents=True, exist_ok=True)
    targets = pd.read_parquet(args.input_dir / "targets.parquet")
    test_frame = annotate(
        attach_truth(pd.read_parquet(args.input_dir / "test_M1_xgb_focus_only.parquet"), targets)
    )
    validation_frame = annotate(
        attach_truth(
            pd.read_parquet(args.input_dir / "validation_calibrated_M1_xgb_focus_only.parquet"),
            targets,
        )
    )
    if len(test_frame) != 50685:
        raise AssertionError(f"Expected 50,685 focus-test rows, found {len(test_frame)}")
    saved = read_json(args.input_dir / "focus_test_metrics.json")
    coverage = read_json(args.input_dir / "empirical_interval_coverage.json")
    leaderboard = pd.read_csv(args.input_dir / "validation_leaderboard.csv")
    test_metrics = component_metrics(test_frame, "locked_focus_test")
    validation_metrics = component_metrics(validation_frame, "validation_focus")
    slices = slice_metrics(test_frame)
    checks = qa(test_frame, test_metrics, saved)
    plot_pred_true(test_frame, args.plots_dir / "01_predicted_vs_true_components.png")
    plot_residuals(test_frame, args.plots_dir / "02_component_residual_distributions.png")
    plot_component_metrics(test_metrics, args.plots_dir / "03_physical_component_metrics.png")
    plot_normalized_metrics(test_metrics, args.plots_dir / "04_normalized_component_metrics.png")
    plot_tolerances(test_metrics, args.plots_dir / "05_tolerance_accuracy.png")
    plot_energy_slices(slices, args.plots_dir / "06_energy_response_resolution_slices.png")
    plot_component_slices(slices, args.plots_dir / "07_component_error_slices.png")
    plot_energy_density(test_frame, args.plots_dir / "08_energy_error_density.png")
    plot_angular(test_frame, slices, args.plots_dir / "09_angular_accuracy.png")
    plot_shell(test_frame, args.plots_dir / "10_mass_shell_residual.png")
    plot_coverage(coverage, args.plots_dir / "11_interval_coverage.png")
    plot_validation_test(
        validation_metrics,
        test_metrics,
        args.plots_dir / "12_validation_vs_test_component_metrics.png",
    )
    plot_leaderboard(leaderboard, args.plots_dir / "13_validation_candidate_metrics.png")
    plot_signal_dependence(test_frame, args.plots_dir / "14_visible_signal_accuracy_dependence.png")
    plot_residual_correlation(test_frame, args.plots_dir / "15_component_residual_correlation.png")
    make_montage(args.plots_dir)
    write_reports(
        args.reports_dir, test_metrics, validation_metrics, slices, saved, coverage, checks
    )


if __name__ == "__main__":
    main()
