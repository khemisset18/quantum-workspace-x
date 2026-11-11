#!/usr/bin/env python3
"""Tests for the Theory 04 compressed MPS experiment."""
import numpy as np
import quantum_workspace_theorie_04_predictive_mps as q


def fidelity(a,b):
    return abs(np.vdot(a,b))**2/(np.vdot(a,a).real*np.vdot(b,b).real)


def main():
    # Physical swaps + logical mapping must preserve the logical wavefunction.
    m=q.MPS(n=8,chi=16)
    for j in range(8):
        m.apply_one(j,q.H if j % 2 == 0 else q.ry(0.17*j))
    initial=m.state_for_validation()
    order=(0,4,1,5,2,6,3,7)
    m.reorder(order)
    assert fidelity(initial,m.state_for_validation())>1-1e-12
    assert m.layout_swaps==q.inversions_from_to(tuple(range(8)),order)

    # Nonlocal gate against an independent exact reference.
    exact=q.apply_full_gate(initial,(0,7),q.zz(0.31),8)
    m.apply_nonlocal(0,7,q.zz(0.31))
    assert fidelity(exact,m.state_for_validation())>1-1e-12

    # Low-rank truncation remains finite and within requested bond cap.
    small=q.MPS(n=8,chi=2)
    for j in range(8):
        small.apply_one(j,q.H)
    for a,b in [(0,4),(1,5),(2,6),(3,7)]:
        small.apply_nonlocal(a,b,q.zz(.49))
    assert all(np.all(np.isfinite(t)) for t in small.tensors)
    assert max(t.shape[-1] for t in small.tensors)<=2

    # Controlled routing comparison, including measured fidelity.
    b8=q.benchmark(n=8,chi=16,passes=4)
    r8={r['policy']:r for r in b8['rows']}
    expected={'natural','golden','compiled_static','reactive','lookahead'}
    assert set(r8)==expected
    assert all(r['fidelity_vs_exact']>1-1e-11 for r in r8.values())
    assert r8['natural']['swap_total']==192
    assert r8['lookahead']['swap_total']==20
    assert r8['lookahead']['svd_calls']<r8['natural']['svd_calls']

    b10=q.benchmark(n=10,chi=16,passes=4)
    r10={r['policy']:r for r in b10['rows']}
    assert r10['lookahead']['fidelity_vs_exact']>1-1e-10
    assert r10['natural']['fidelity_vs_exact']<.99
    assert r10['lookahead']['peak_tensor_coefficients']<r10['natural']['peak_tensor_coefficients']

    # Equal-fidelity check: every policy can keep fidelity ~1 with chi=32.
    b10full=q.benchmark(n=10,chi=32,passes=4)
    rf={r['policy']:r for r in b10full['rows']}
    assert all(r['fidelity_vs_exact']>1-1e-10 for r in rf.values())
    assert rf['lookahead']['peak_tensor_coefficients']<rf['natural']['peak_tensor_coefficients']

    # Dense reference is deliberately disabled past ten qubits.
    b12=q.benchmark(n=12,chi=16,passes=2)
    assert all(r['fidelity_vs_exact'] is None for r in b12['rows'])
    print('Theory 04 tests: OK')


if __name__=='__main__':
    main()
