import unittest

import numpy as np

from zdc_reco.features import build_event_features
from zdc_reco.geometry import infer_detector_frame, validate_frame


class GeometryFeatureTests(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(9)
        self.ecal = rng.normal([2.0, -3.0, 10.0], [3.0, 3.0, 1.0], size=(500, 3))
        self.hcal = rng.normal([12.0, -3.0, 110.0], [8.0, 8.0, 25.0], size=(2000, 3))
        self.frame = infer_detector_frame(self.ecal, self.hcal)

    def test_frame_is_right_handed_and_downstream(self):
        validate_frame(self.frame)
        self.assertGreater(np.linalg.det(self.frame.rotation), 0.0)

    def test_feature_builder_is_finite(self):
        e = self.ecal[:20]
        h = self.hcal[:80]
        features = build_event_features(
            ecal_x=e[:, 0],
            ecal_y=e[:, 1],
            ecal_z=e[:, 2],
            ecal_signal_gev=np.linspace(0.001, 0.02, len(e)),
            hcal_x=h[:, 0],
            hcal_y=h[:, 1],
            hcal_z=h[:, 2],
            hcal_signal_gev=np.linspace(0.002, 0.08, len(h)),
            frame=self.frame,
        )
        self.assertGreater(len(features), 100)
        self.assertTrue(all(np.isfinite(v) for v in features.values()))
        self.assertAlmostEqual(
            features["ecal_signal_fraction"] + features["hcal_signal_fraction"], 1.0
        )

    def test_empty_event_has_explicit_flags(self):
        empty = np.asarray([])
        features = build_event_features(
            ecal_x=empty,
            ecal_y=empty,
            ecal_z=empty,
            ecal_signal_gev=empty,
            hcal_x=empty,
            hcal_y=empty,
            hcal_z=empty,
            hcal_signal_gev=empty,
            frame=self.frame,
        )
        self.assertEqual(features["no_detector_signal"], 1.0)
        self.assertEqual(features["ecal_empty"], 1.0)
        self.assertEqual(features["hcal_empty"], 1.0)


if __name__ == "__main__":
    unittest.main()
