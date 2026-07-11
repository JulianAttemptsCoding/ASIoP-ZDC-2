from __future__ import annotations

import json

import numpy as np

from .metrics import macro_rms_relative_fourvector
from .physics import fourvector_from_kinetic_direction, mass_shell_residual


def main() -> None:
    kinetic = np.asarray([50.0, 100.0, 150.0, 200.0, 250.0])
    direction = np.tile(np.asarray([[0.0, 0.0, 1.0]]), (len(kinetic), 1))
    fourvector = fourvector_from_kinetic_direction(kinetic, direction)
    score = macro_rms_relative_fourvector(
        fourvector,
        fourvector,
        kinetic,
        np.asarray([50.0, 100.0, 150.0, 200.0, 250.0]),
    )
    print(json.dumps({
        "macro_score_perfect": score,
        "mass_shell_abs_max": float(np.max(np.abs(mass_shell_residual(fourvector)))),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
