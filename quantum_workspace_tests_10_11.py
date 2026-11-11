#!/usr/bin/env python3
"""Independent correctness checks for the QWX 10/11 zip-up MPO prototype."""
import numpy as np
import quantum_workspace_theorie_04_predictive_mps as q4
import quantum_workspace_theorie_09_hybride_mpo as q9
import quantum_workspace_theorie_10_11_zipup_selector as exp


def fidelity(x,y):
    return float(abs(np.vdot(x,y))**2 / (np.vdot(x,x).real*np.vdot(y,y).real))


def build_initial(n,chi):
    obj=q4.MPS(n=n,chi=chi,svd_tol=1e-14)
    for q in range(n):obj.apply_one(q,q4.H)
    return obj


def main():
    for n,chi in ((6,16),(8,16),(10,32)):
        for a,b in ((0,n-1),(1,n-2),(0,1)):
            theta=0.27
            mpo=build_initial(n,chi)
            streaming=build_initial(n,chi)
            dense=streaming.state_for_validation()
            exact=q4.apply_full_gate(dense,(a,b),q4.zz(theta),n)
            q9.apply_zz_mpo(mpo,a,b,theta)
            exp.apply_zz_zipup(streaming,a,b,theta,oversample=2)
            assert fidelity(streaming.state_for_validation(),exact)>1-1e-11,(n,a,b,'zip-up exact')
            assert fidelity(mpo.state_for_validation(),exact)>1-1e-11,(n,a,b,'MPO eager exact')
            assert all(np.all(np.isfinite(t)) for t in streaming.tensors)
            assert max(t.shape[-1] for t in streaming.tensors)<=chi

    for n,chi in ((8,16),(10,32)):
        for mode in exp.POLICIES:
            result=exp.run(mode,n=n,chi=chi,repeats=2,scenario='random',seed=11)
            assert result['fidelity'] is not None and result['fidelity']>1-1e-9,(n,mode,result['fidelity'])
            assert result['maxrss_kib']>0
            assert result['decision_count']>0
            assert sum(result['choices'].values())==result['decision_count']
            assert result['peak_mps_coefficients']>0

    # Nonidentical state families: test cases without future lookahead.
    result=exp.run('zipup',n=8,chi=16,repeats=2,scenario='switching',seed=23)
    assert result['fidelity']>1-1e-9
    assert result['swaps']==0
    s=exp.suite(n=6,chi=16,repeats=1,scenario='random',seed=11)
    assert set(row['policy'] for row in s['results'])==set(exp.POLICIES)
    assert all(row['fidelity']>1-1e-10 for row in s['results'])
    print('Theory 10/11 zipup and selector numerical tests: OK')


if __name__=='__main__':
    main()
