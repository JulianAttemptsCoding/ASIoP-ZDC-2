import unittest

import numpy as np

from zdc_reco.physics import (
    canonical_truth,
    fourvector_from_kinetic_direction,
    infer_energy_convention,
    mass_shell_residual,
)


class PhysicsTests(unittest.TestCase):
    def test_kinetic_parameterization_is_on_shell(self):
        kinetic = np.asarray([0.0, 1.0, 50.0, 300.0])
        direction = np.asarray([[0.0, 0.0, 1.0], [1.0, 2.0, 3.0], [0.2, 0.1, 1.0], [1.0, 0.0, 0.0]])
        fourvector = fourvector_from_kinetic_direction(kinetic, direction)
        self.assertLess(float(np.max(np.abs(mass_shell_residual(fourvector)))), 1e-10)

    def test_infer_total_gev(self):
        rng = np.random.default_rng(4)
        momentum = rng.uniform(0.0, 300.0, size=(2000, 3))
        mass = 0.93956542052
        energy = np.sqrt(np.sum(momentum**2, axis=1) + mass**2)
        convention = infer_energy_convention(energy, momentum)
        self.assertEqual(convention.semantics, "total")
        self.assertEqual(convention.energy_scale_to_gev, 1.0)
        self.assertEqual(convention.momentum_scale_to_gev, 1.0)

    def test_infer_kinetic_mev(self):
        p_gev = np.linspace(0.0, 300.0, 2000)
        momentum_mev = np.column_stack([np.zeros_like(p_gev), np.zeros_like(p_gev), p_gev * 1000.0])
        mass = 0.93956542052
        kinetic_mev = (np.sqrt(p_gev**2 + mass**2) - mass) * 1000.0
        convention = infer_energy_convention(kinetic_mev, momentum_mev)
        self.assertEqual(convention.semantics, "kinetic")
        self.assertEqual(convention.energy_scale_to_gev, 0.001)
        truth = canonical_truth(kinetic_mev, momentum_mev, convention)
        self.assertTrue(np.allclose(truth["kinetic_energy_true_gev"], kinetic_mev / 1000.0))


if __name__ == "__main__":
    unittest.main()
