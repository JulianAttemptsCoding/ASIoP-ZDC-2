import unittest
from pathlib import Path

import numpy as np

from zdc_hybrid.budget import JobEstimate, assert_planned_budget
from zdc_hybrid.calibration import (
    EnergyBalancedIsotonicCalibrator,
    finite_sample_absolute_residual_quantile,
)
from zdc_hybrid.cli import REQUIRED_COMMANDS, build_parser, main
from zdc_hybrid.metrics import fixed_bin_masks, macro_rms_relative_fourvector
from zdc_hybrid.objectives import joint_energy_theta_weights
from zdc_hybrid.physics import (
    apply_tangent_residual,
    fourvector_from_kinetic_direction,
    mass_shell_residual,
)


class CoreTests(unittest.TestCase):
    def test_mass_shell_across_support(self):
        kinetic = np.linspace(0.0, 300.0, 301)
        direction = np.tile(np.asarray([[0.01, -0.02, 1.0]]), (len(kinetic), 1))
        fourvector = fourvector_from_kinetic_direction(kinetic, direction)
        # Absolute cancellation error scales with E^2; 1e-10 GeV^2 is still
        # sub-part-per-quadrillion relative to a 300 GeV four-vector scale.
        self.assertLess(float(np.max(np.abs(mass_shell_residual(fourvector)))), 1e-10)

    def test_tangent_zero_is_identity(self):
        axis = np.asarray([[0.1, 0.2, 1.0], [-0.2, 0.1, 1.0]])
        corrected = apply_tangent_residual(axis, np.zeros((2, 2)))
        expected = axis / np.linalg.norm(axis, axis=1)[:, None]
        self.assertTrue(np.allclose(corrected, expected))

    def test_final_bin_is_inclusive(self):
        masks = fixed_bin_masks(np.asarray([50.0, 75.0, 250.0]), np.asarray([50.0, 75.0, 250.0]))
        self.assertTrue(np.array_equal(masks[0], [True, False, False]))
        self.assertTrue(np.array_equal(masks[1], [False, True, True]))

    def test_perfect_macro_score(self):
        energy = np.asarray([50.0, 75.0, 100.0, 125.0, 150.0, 175.0, 200.0, 225.0, 250.0])
        direction = np.tile(np.asarray([[0.0, 0.0, 1.0]]), (len(energy), 1))
        truth = fourvector_from_kinetic_direction(energy, direction)
        score = macro_rms_relative_fourvector(truth, truth, energy, np.arange(50.0, 275.0, 25.0))
        self.assertEqual(score, 0.0)

    def test_joint_weights_are_finite_and_normalized(self):
        energy = np.asarray([50, 60, 100, 110, 200, 210], dtype=float)
        theta = np.asarray([0, 10, 0, 10, 100, 110], dtype=float)
        weight = joint_energy_theta_weights(
            energy, theta, np.asarray([50, 100, 150, 250]), np.asarray([0, 50, 150])
        )
        self.assertTrue(np.all(np.isfinite(weight)))
        self.assertAlmostEqual(float(np.mean(weight)), 1.0)

    def test_empirical_quantile(self):
        q = finite_sample_absolute_residual_quantile(
            np.asarray([0.0, 1.0, 2.0]), np.asarray([0.0, 0.0, 0.0]), 0.5
        )
        self.assertEqual(q, 1.0)

    def test_isotonic_calibrator_is_monotone(self):
        predicted = np.asarray([55, 60, 80, 90, 105, 115, 130, 140], dtype=float)
        truth = np.asarray([50, 60, 75, 95, 100, 120, 125, 145], dtype=float)
        calibrator = EnergyBalancedIsotonicCalibrator(
            np.asarray([50, 75, 100, 125, 150], dtype=float)
        ).fit(predicted, truth)
        calibrated = calibrator.predict(np.linspace(55, 140, 30))
        self.assertTrue(np.all(np.diff(calibrated) >= 0.0))
        self.assertEqual(calibrator.clipped_fraction(np.asarray([40.0, 100.0, 160.0])), 2 / 3)

    def test_budget_refuses_overspend(self):
        jobs = [JobEstimate("too-large", 20.0, 4.0)]
        with self.assertRaises(ValueError):
            assert_planned_budget(jobs)

    def test_budget_accepts_bounded_plan(self):
        jobs = [JobEstimate("cpu", 2.0, 4.0), JobEstimate("t4", 3.0, 10.0)]
        self.assertEqual(assert_planned_budget(jobs), 38.0)

    def test_cli_exposes_required_commands(self):
        parser = build_parser()
        subparsers = next(
            action for action in parser._actions if getattr(action, "dest", None) == "command"
        )
        self.assertEqual(set(REQUIRED_COMMANDS), set(subparsers.choices))

    def test_cli_fails_closed_after_blocker(self):
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmp:
            report_dir = Path(tmp) / "reports"
            report_dir.mkdir()
            (report_dir / "BLOCKED.md").write_text("# BLOCKED\n", encoding="utf-8")
            code = main(["build-targets", "--output-dir", tmp])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
