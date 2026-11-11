#!/usr/bin/env python3
"""Tests de cohérence de la théorie 03 : arbres de tenseurs."""
import numpy as np
import quantum_workspace_theorie_01 as q
import quantum_workspace_theorie_03_arbres as exp


def run():
    for n in (2, 3, 5, 8, 13):
        assert exp.valid_tree(exp.balanced(range(n)), n)
        assert exp.valid_tree(exp.fibonacci(range(n)), n)
        assert len(exp.leaves(exp.fibonacci(range(n)))) == n

    psi0 = np.zeros(2**8, complex)
    psi0[0] = 1.0
    for tree in (exp.balanced(range(8)), exp.fibonacci(range(8))):
        measured = exp.measure_tree(psi0, tree)
        assert measured['liaison_max'] == 1, measured
        assert measured['coefficients'] == 2 * 8 + 7, measured
        assert measured['nombre_coupures'] == 14

    bell = q.bell_pairs()
    mi = q.mutual_information_map(bell)
    assert exp.valid_tree(exp.mutual_tree(mi), 8)
    best_bell = exp.measure_tree(bell, exp.mutual_tree(mi))
    assert best_bell['coefficients'] == 51, best_bell
    assert best_bell['liaison_max'] == 2, best_bell

    ghz = q.ghz()
    for tree in (exp.balanced(range(8)), exp.fibonacci(range(8))):
        assert exp.measure_tree(ghz, tree)['coefficients'] == 84

    result = exp.main()
    assert len(result['statique']) == 4
    assert len(result['dynamique']) == 13
    assert result['statique'][0]['mesures']['fusion_intrication']['coefficients'] == 51
    assert all(0 <= row['t'] <= 1 for row in result['dynamique'])
    print('Tous les tests de la théorie 03 ont réussi.')


if __name__ == '__main__':
    run()
