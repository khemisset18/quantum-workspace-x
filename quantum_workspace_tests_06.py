#!/usr/bin/env python3
"""Tests numériques de la théorie 06, sans futurs connus du contrôleur."""
import numpy as np
import quantum_workspace_theorie_04_predictive_mps as q4
import quantum_workspace_theorie_05_history_mps as q5
import quantum_workspace_theorie_06_observation_selective as q6


def main():
    # Le diagnostic MPS doit restituer l'information mutuelle sans état dense.
    mps = q4.MPS(n=8, chi=16)
    for i in range(8):
        mps.apply_one(i, q4.H)
    for a,b in ((0,4),(1,5),(2,6),(3,7)):
        mps.apply_nonlocal(a,b,q4.zz(0.4))
    mi = q5.mi_from_mps(mps)
    for a,b in ((0,4),(0,1),(2,6),(3,7)):
        assert abs(q6.pair_mi(mps,a,b)-mi[a,b]) < 1e-9
    mps.reorder((0,4,1,5,2,6,3,7))
    after=q5.mi_from_mps(mps)
    for a,b in ((0,4),(0,1),(2,6),(3,7)):
        assert abs(q6.pair_mi(mps,a,b)-after[a,b]) < 1e-9

    # Borne stricte sur le nombre de paires observées par sondage.
    batches=q5.create_microbatches(n=8,repeats=3,scenario='persistent',seed=11)
    result, state=q6.run_selective(batches,n=8,chi=16,probe_budget=2)
    assert result['pair_probes']<=2*result['probe_events']
    assert result['pair_probes']>0
    ref=q5.exact_state(8,batches)
    assert q6.fidelity(ref,state.state_for_validation())>1-1e-10

    # Une modification de l'avenir ne doit jamais influencer un préfixe commun.
    altered=[list(b) for b in batches]
    altered[-1]=[('zz',1,7,.7),('zz',0,3,.31)]
    first,_=q6.run_selective(batches,n=8,chi=16,probe_budget=2)
    second,_=q6.run_selective(altered,n=8,chi=16,probe_budget=2)
    assert first['history'][:-1]==second['history'][:-1]

    # Scénario à motifs imprévisibles : aucune consultation du futur.
    random=q5.create_microbatches(n=8,repeats=3,scenario='random',seed=23)
    random_result,random_state=q6.run_selective(random,n=8,chi=16,probe_budget=3)
    assert random_result['pair_probes']<=3*random_result['probe_events']
    assert q6.fidelity(q5.exact_state(8,random),random_state.state_for_validation())>1-1e-10
    assert all(t.shape[-1]<=16 for t in random_state.tensors)

    # Contrôles et rapport agrégé, sans assertion sur les temps (bruit CPU).
    report=q6.benchmark(n=8,chi=16,repeats=2,seeds=(23,),budget=2)
    assert len(report['results'])==3
    for scene in report['results']:
        assert {p['policy'] for p in scene['strategies']}=={
            'fixed','history','history_confident','reactive','selective'}
        for policy in scene['strategies']:
            assert policy['fidelity']>1-1e-10
    print('Theory 06: all tests passed.')


if __name__=='__main__':main()
