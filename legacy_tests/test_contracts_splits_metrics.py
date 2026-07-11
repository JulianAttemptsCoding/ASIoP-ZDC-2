import unittest

import numpy as np
import pandas as pd

from zdc_reco.contracts import assert_feature_provenance
from zdc_reco.metrics import evaluate_fourvectors
from zdc_reco.physics import fourvector_from_kinetic_direction
from zdc_reco.splits import assert_split_integrity, make_grouped_splits


class ContractSplitMetricTests(unittest.TestCase):
    def test_truth_provenance_is_rejected(self):
        with self.assertRaises(ValueError):
            assert_feature_provenance(
                [{"feature": "bad", "source_kind": "detector", "source_branches": ["px_true_gev"]}]
            )

    def test_grouped_split_has_no_group_overlap(self):
        n = 20000
        rng = np.random.default_rng(12)
        frame = pd.DataFrame(
            {
                "event_uid": [f"e{i}" for i in range(n)],
                "group_uid": [f"g{i // 2}" for i in range(n)],
                "generator_energy_gev": rng.uniform(0.0, 300.0, n),
                "theta_true_rad": rng.uniform(0.0, 0.1, n),
                "phi_true_rad": rng.uniform(-np.pi, np.pi, n),
            }
        )
        frame["split"] = make_grouped_splits(
            frame,
            seed=42,
            energy_edges=[0, 50, 100, 150, 200, 250, 300],
            theta_bins=4,
            phi_bins=4,
        )
        assert_split_integrity(frame)
        fractions = frame["split"].value_counts(normalize=True)
        self.assertAlmostEqual(fractions["train"], 0.8, delta=0.02)
        self.assertAlmostEqual(fractions["validation"], 0.1, delta=0.02)
        self.assertAlmostEqual(fractions["test"], 0.1, delta=0.02)
        self.assertNotIn("calibration", fractions.index)

    def test_perfect_metrics(self):
        true = fourvector_from_kinetic_direction(
            np.asarray([50.0, 100.0]), np.asarray([[0.0, 0.0, 1.0], [0.1, 0.2, 1.0]])
        )
        metrics = evaluate_fourvectors(true, true.copy(), mass_gev=0.93956542052)
        self.assertAlmostEqual(metrics["energy_relative_rmse"], 0.0)
        self.assertAlmostEqual(metrics["angular_68_mrad"], 0.0)


if __name__ == "__main__":
    unittest.main()
