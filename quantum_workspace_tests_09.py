#!/usr/bin/env python3
"""QWX theory 09 — independent exact-state comparisons and regression tests."""
import numpy as np
import quantum_workspace_theorie_04_predictive_mps as q4
import quantum_workspace_theorie_09_hybride_mpo as q9


def fidelity(a, b):
    return float(abs(np.vdot(a,b))**2 /
                 (np.vdot(a,a).real * np.vdot(b,b).real))


def check_mpo_gates():
    rng = np.random.default_rng(2026)
    for n, chi in ((6,8), (8,16), (10,32)):
        for _ in range(3):
            m = q4.MPS(n=n, chi=chi, svd_tol=1e-14)
            for site in range(n):
                m.apply_one(site, q4.H)
                m.apply_one(site, q4.ry(float(rng.uniform(-.3, .3))))
            for a,b in ((0,n-1),(1,n-2),(0,2)):
                before = m.state_for_validation()
                angle = float(rng.uniform(-.5, .5))
                exact = q4.apply_full_gate(before,(a,b),q4.zz(angle),n)
                q9.apply_zz_mpo(m,a,b,angle)
                assert fidelity(exact,m.state_for_validation()) > 1-1e-11
                assert m.swaps == 0
            assert m.svd_calls > 0


def check_reordered():
    m = q4.MPS(n=8, chi=16)
    for j in range(8):
        m.apply_one(j,q4.H)
    m.reorder((0,4,1,5,2,6,3,7))
    before=m.state_for_validation()
    exact=q4.apply_full_gate(before,(0,7),q4.zz(.47),8)
    old_swaps=m.swaps
    q9.apply_zz_mpo(m,0,7,.47)
    assert m.swaps == old_swaps
    assert fidelity(exact,m.state_for_validation()) > 1-1e-12


def check_benchmark():
    for n,chi in ((8,16),(10,32)):
        for scene in ('persistent','switching','random'):
            for mode in ('swap','mpo','hybrid','hybrid_budget'):
                r=q9.run(n=n,chi=chi,repeats=2,seed=11,
                         scenario=scene,mode=mode)
                assert r['fidelity'] > 1-1e-10, r
                assert r['peak_coefficients'] > 0
                assert r['svd_calls'] > 0
                assert r['swaps'] >= 0
    direct=q9.run(n=10,chi=32,repeats=2,seed=11,
                 scenario='switching',mode='mpo')
    budget=q9.run(n=10,chi=32,repeats=2,seed=11,
                 scenario='switching',mode='hybrid_budget')
    assert budget['peak_coefficients'] < direct['peak_coefficients']
    assert budget['fidelity'] > 1-1e-10


def main():
    check_mpo_gates()
    check_reordered()
    check_benchmark()
    print('Theory 09: precision, routing and budget tests passed')


if __name__ == '__main__':
    main()
