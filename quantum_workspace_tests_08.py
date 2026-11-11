#!/usr/bin/env python3
"""Physical and numerical validation for QWX-08."""
from dataclasses import replace
import numpy as np
from quantum_workspace_experience_08_friction import (
    PTConfig, SpinConfig, run_pt, run_spin, drive_fields, mps_expectation, Z)
from quantum_workspace_theorie_04_predictive_mps import MPS

def run():
    pt=PTConfig(distance=1.2,drive_velocity=.3)
    for ratio in (0.,.4):
        result=run_pt(replace(pt,quasiperiodic_ratio=ratio),samples=301)
        assert result['viscous_heat']>=0
        assert result['maximum_energy_balance_error']<2e-6,result
        assert abs(result['external_work']-result['viscous_heat']-
                   result['delta_mechanical_energy'])<2e-6
    gamma0=run_pt(replace(pt,damping=0.),samples=301)
    assert abs(gamma0['viscous_heat'])<1e-13
    assert abs(gamma0['external_work']-gamma0['delta_mechanical_energy'])<2e-6

    config=SpinConfig(n=6,chi=8,dt=.03,duration=1.2,sample_every=6)
    assert np.allclose(drive_fields(0.,config),0.)
    assert np.allclose(drive_fields(config.duration,config),0.)
    q=run_spin(config)
    assert q['fidelity_vs_sparse_midpoint']>.9999,q
    assert q['absolute_energy_error']<1e-3,q
    assert q['absorbed_work_excitation_energy']>0,q
    assert len(q['snapshots'])>=2
    assert all(0<=x<=1+1e-7 for snap in q['snapshots']
               for x in snap['excitation_proxy'])
    no_drive=run_spin(replace(config,amplitude=0.,sample_every=0))
    assert abs(no_drive['absorbed_work_excitation_energy'])<2e-8,no_drive
    assert no_drive['fidelity_vs_sparse_midpoint']>.999999

    m=MPS(n=4,chi=8)
    m.apply_one(2,np.array([[0,1],[1,0]],complex))
    assert abs(mps_expectation(m,{2:Z}).real+1)<1e-12
    m.reorder((2,0,1,3))
    assert abs(mps_expectation(m,{2:Z}).real+1)<1e-12

    coarse=run_spin(replace(config,dt=.12,sample_every=0))
    fine=run_spin(replace(config,dt=.03,sample_every=0))
    assert fine['fidelity_vs_sparse_midpoint'] >= coarse['fidelity_vs_sparse_midpoint']-1e-9

    q8=run_spin(SpinConfig(n=8,chi=16,dt=.04,duration=.8))
    assert q8['fidelity_vs_sparse_midpoint']>.9999,q8
    print("Theory 08: PT energy balance, MPS fidelity, no-drive and convergence: OK")

if __name__=="__main__":run()
