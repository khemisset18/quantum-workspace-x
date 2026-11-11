#!/usr/bin/env python3
"""Tests du protocole d'exploration du nombre d'or."""
import numpy as np
import quantum_workspace_theorie_01 as q
import quantum_workspace_theorie_02_nombre_or as exp


def main():
    assert 1.618 < exp.PHI < 1.619
    for n in (2, 5, 8, 13):
        order = exp.golden_angle_order(n)
        assert sorted(order) == list(range(n))
        assert order == exp.golden_angle_order(n)
    bell = q.bell_pairs()
    normal = exp.evaluate(bell, tuple(range(8)))
    golden = exp.evaluate(bell, exp.golden_angle_order(8))
    assert normal["bond"] == golden["bond"] == 16
    assert np.isclose(normal["fidelity"], 1)
    assert golden["parameters"] == normal["parameters"] == 680
    data = exp.main()
    assert len(data["reference_cases"]) == 4
    assert len(data["ising_trials"]) == 36
    for row in data["ising_trials"]:
        assert all(row[k]["fidelity"] >= q.TARGET_FIDELITY - 1e-10
                   for k in ("identity", "golden", "random"))
    print("Tests du nombre d'or : OK")


if __name__ == "__main__":
    main()
