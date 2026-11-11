#!/usr/bin/env python3
"""Tests indépendants : observables MPS, limite de prédiction et politiques."""
import numpy as np
import quantum_workspace_theorie_04_predictive_mps as q4
import quantum_workspace_theorie_05_history_mps as q5

def dense_rdm(psi,n,kept):
    rest=tuple(i for i in range(n) if i not in kept)
    arr=psi.reshape((2,)*n).transpose(kept+rest).reshape(2**len(kept),-1)
    rho=arr@arr.conj().T
    return rho/np.trace(rho)

def check_reduced_densities():
    m=q4.MPS(n=8,chi=16)
    for i in range(8):
        m.apply_one(i,q4.ry(.14+i*.07))
        if i%2==0:m.apply_one(i,q4.H)
    m.apply_nonlocal(0,7,q4.zz(.28))
    m.apply_nonlocal(1,5,q4.zz(.61))
    m.reorder((0,5,1,7,2,6,3,4))
    state=m.state_for_validation()
    for selected in ((0,),(1,),(2,6),(3,7),(0,3)):
        result=q5.reduced_density_from_mps(m,selected)
        logical=tuple(m.order[p] for p in selected)
        reference=dense_rdm(state,8,logical)
        assert np.allclose(result,reference,atol=3e-12)
    mi=q5.mi_from_mps(m)
    assert np.allclose(mi,mi.T,atol=1e-13)
    assert np.all(mi>=-1e-12)

def check_impossibility_of_universal_prediction():
    # Identical current states: identity keeps the product state unentangled,
    # whereas a future ZZ(pi/4) entangles two qubits. Without future dynamics,
    # both branches are indistinguishable at the prediction time.
    a,b=q4.MPS(n=4,chi=4),q4.MPS(n=4,chi=4)
    for i in range(4):
        a.apply_one(i,q4.H)
        b.apply_one(i,q4.H)
    assert np.allclose(a.state_for_validation(),b.state_for_validation())
    b.apply_nonlocal(0,1,q4.zz(np.pi/4))
    ea=q5.entropy(q5.reduced_density_from_mps(a,(0,)))
    eb=q5.entropy(q5.reduced_density_from_mps(b,(0,)))
    assert ea<1e-10 and eb>0.9999999

def check_routing_baselines():
    report=q5.benchmark(n=8,chi=16,repeats=4,seed=15)
    scenes={s['scenario']:{r['policy']:r for r in s['results']}
            for s in report['scenarios']}
    assert scenes['persistent']['history']['swaps']<scenes['persistent']['fixed']['swaps']
    assert scenes['persistent']['history_confident']['swaps']<scenes['persistent']['fixed']['swaps']
    assert scenes['switching']['history_confident']['swaps']<scenes['switching']['fixed']['swaps']
    assert scenes['random']['history']['swaps']>scenes['random']['fixed']['swaps']
    assert scenes['random']['history_confident']['swaps']==scenes['random']['fixed']['swaps']
    assert scenes['persistent']['trend']['forecast_mae'] is not None
    for cases in scenes.values():
        for row in cases.values():
            assert row['fidelity']>0.9999999999, row
            assert row['layout_swaps']+row['route_swaps']==row['swaps']
            assert row['svd_calls']>=row['swaps']

if __name__=='__main__':
    check_reduced_densities()
    check_impossibility_of_universal_prediction()
    check_routing_baselines()
    print('Theory 05: MPS RDMs, no-go example, fidelity and routing: OK')
