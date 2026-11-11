#!/usr/bin/env python3
"""Tests automatiques du prototype Quantum Workspace X — Théorie 01."""
import numpy as np
import quantum_workspace_theorie_01 as q


def presque(x, y, eps=1e-9):
    assert abs(x-y) < eps, (x, y)


def main():
    bell = q.bell_pairs()
    assert bell.shape == (256,)
    presque(np.linalg.norm(bell), 1.0)
    im = q.mutual_information_map(bell)
    presque(im[0, 4], 2.0)
    presque(im[0, 1], 0.0)
    assert np.allclose(im, im.T)

    normal = tuple(range(8))
    optimize = q.best_order_exact(im)
    assert optimize == (0, 4, 1, 5, 2, 6, 3, 7), optimize
    assert max(q.schmidt_ranks(bell, normal)) == 16
    assert max(q.schmidt_ranks(bell, optimize)) == 2
    f_bell, params = q.approximate_mps(bell, optimize, 2)
    presque(f_bell, 1.0)
    assert params == 56

    ghz = q.ghz()
    mi_ghz = q.mutual_information_map(ghz)
    presque(mi_ghz[0, 1], 1.0)
    assert max(q.schmidt_ranks(ghz, normal)) == 2
    presque(q.approximate_mps(ghz, normal, 2)[0], 1.0)

    rng = np.random.default_rng(19)
    psi = q.normed(rng.normal(size=256) + 1j*rng.normal(size=256))
    for order in (normal, (4, 3, 0, 6, 1, 7, 5, 2)):
        presque(q.approximate_mps(psi, order, 16)[0], 1.0)
        assert q.approximate_mps(psi, order, 1)[0] <= q.approximate_mps(psi, order, 16)[0]

    ising = q.make_cases()['Ising 1D (ordre brouillé)']
    best = q.best_order_exact(q.mutual_information_map(ising))
    assert q.required_bond(ising, normal, q.TARGET_FIDELITY)[0] == 7
    assert q.required_bond(ising, best, q.TARGET_FIDELITY)[0] == 4
    print('Tous les tests sont réussis : Bell, GHZ, état aléatoire et Ising.')


if __name__ == '__main__':
    main()
