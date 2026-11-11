#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""QWX-08: atomic-friction baseline and a SEPARATE driven quantum spin toy model.

(A) Classical Prandtl-Tomlinson tip: external work = change in mechanical
    energy + heat from modeled viscous damping.
(B) CLOSED quantum Ising chain: moving transverse-field pulse, compressed
    matrix-product state (MPS) and independent sparse midpoint reference.

The spin chain is NOT a literal simulation of sliding atoms or irreversible
friction, and neither model represents new physics. All units are dimensionless.
Run: python quantum_workspace_experience_08_friction.py --n 6 --chi 8
"""
from __future__ import annotations
import argparse
import json
import math
import time
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp
from scipy.sparse import csr_matrix, kron
from scipy.sparse.linalg import expm_multiply
from quantum_workspace_theorie_04_predictive_mps import MPS, zz

X=np.array([[0,1],[1,0]],complex)
Z=np.diag([1.,-1.]).astype(complex)
I=np.eye(2,dtype=complex)
PHI=(1+5**.5)/2

@dataclass(frozen=True)
class PTConfig:
    mass:float=1.
    stiffness:float=4.
    damping:float=1.5
    corrugation:float=1.
    lattice:float=1.
    drive_velocity:float=.22
    distance:float=5.
    quasiperiodic_ratio:float=0.
    phi:float=PHI

def pt_potential(x,support,c):
    u1=c.corrugation*(1-c.quasiperiodic_ratio)
    u2=c.corrugation*c.quasiperiodic_ratio
    phase=2*np.pi*x/c.lattice
    return (.5*c.stiffness*(x-support)**2+
            u1*(1-np.cos(phase))+u2*(1-np.cos(phase/c.phi)))

def pt_force(x,c):
    q=2*np.pi/c.lattice
    u1=c.corrugation*(1-c.quasiperiodic_ratio)
    u2=c.corrugation*c.quasiperiodic_ratio
    return -u1*q*np.sin(q*x)-u2*q/c.phi*np.sin(q*x/c.phi)

def run_pt(c:PTConfig,samples=801):
    if min(c.mass,c.stiffness,c.lattice,c.drive_velocity,c.distance)<=0:
        raise ValueError("physical PT parameters must be positive")
    if c.damping<0 or c.corrugation<0 or not 0<=c.quasiperiodic_ratio<=1:
        raise ValueError("damping/corrugation/ratio out of range")
    duration=c.distance/c.drive_velocity
    def rhs(t,y):
        x,v,work,heat=y
        pulling=c.stiffness*(c.drive_velocity*t-x)
        return [v,(pulling+pt_force(x,c)-c.damping*v)/c.mass,
                pulling*c.drive_velocity,c.damping*v*v]
    t=np.linspace(0,duration,samples)
    start=time.perf_counter()
    sol=solve_ivp(rhs,(0,duration),[0.,0.,0.,0.],method="DOP853",
                  t_eval=t,rtol=2e-10,atol=3e-12,
                  max_step=min(.04,duration/250))
    elapsed=time.perf_counter()-start
    if not sol.success:raise RuntimeError(sol.message)
    pos,vel,work,heat=sol.y
    mechanical=(.5*c.mass*vel**2+
                np.array([pt_potential(x,c.drive_velocity*ti,c)
                          for x,ti in zip(pos,t)]))
    residual=work-heat-(mechanical-mechanical[0])
    return dict(config=c.__dict__,elapsed_seconds=elapsed,
                final_position=float(pos[-1]),
                external_work=float(work[-1]),
                viscous_heat=float(heat[-1]),
                delta_mechanical_energy=float(mechanical[-1]-mechanical[0]),
                maximum_energy_balance_error=float(np.max(np.abs(residual))),
                mean_pulling_force=float(work[-1]/c.distance),
                time=t.tolist(),position=pos.tolist(),
                pulling_force=(c.stiffness*(c.drive_velocity*t-pos)).tolist())

@dataclass(frozen=True)
class SpinConfig:
    n:int=6
    chi:int=8
    h:float=1.
    j:float=.45
    amplitude:float=1.1
    width:float=.85
    duration:float=1.8
    dt:float=.03
    svd_tol:float=1e-12
    sample_every:int=0

def drive_fields(t,c):
    s=float(np.clip(t/c.duration,0,1))
    return c.amplitude*np.sin(np.pi*s)**2 * np.exp(
        -.5*((np.arange(c.n)-(c.n-1)*s)/c.width)**2)

def onsite_gate(h,field,tau):
    omega=math.hypot(h,field)
    if omega<1e-15:return I.copy()
    return np.cos(tau*omega)*I-1j*np.sin(tau*omega)/omega*(-h*Z+field*X)

def mps_expectation(mps,local_ops):
    env=np.ones((1,1),complex)
    for p,A in enumerate(mps.tensors):
        op=local_ops.get(mps.order[p],I)
        env=np.einsum("ab,aic,ij,bjd->cd",env,A.conj(),op,A,optimize=True)
    return complex(env[0,0])

def mps_H0_energy(mps,c):
    norm=mps_expectation(mps,{}).real
    z=sum(mps_expectation(mps,{i:Z}).real for i in range(c.n))
    zzs=sum(mps_expectation(mps,{i:Z,i+1:Z}).real for i in range(c.n-1))
    return (-c.h*z-c.j*zzs)/norm

def H0_diagonal(c):
    bits=np.arange(2**c.n)
    spins=np.vstack([1-2*((bits>>(c.n-1-i))&1) for i in range(c.n)])
    return -c.h*np.sum(spins,axis=0)-c.j*np.sum(spins[:-1]*spins[1:],axis=0)

def sparse_midpoint_reference(c,steps):
    """Independent full-Hilbert-space evolution, midpoint time approximation.
    This is NOT mathematically exact continuous-time propagation."""
    if c.n>10:raise ValueError("only n<=10 supports dense validation")
    size=2**c.n
    H0=csr_matrix((H0_diagonal(c),(np.arange(size),np.arange(size))),
                  shape=(size,size))
    Xops=[]
    for i in range(c.n):
        op=csr_matrix([[1.]])
        for j in range(c.n):
            op=kron(op,csr_matrix(X if i==j else I),format="csr")
        Xops.append(op)
    state=np.zeros(size,complex);state[0]=1
    dt=c.duration/steps
    for step in range(steps):
        fields=drive_fields((step+.5)*dt,c)
        H=H0.copy()
        for amp,op in zip(fields,Xops):
            if amp:H=H+amp*op
        state=expm_multiply((-1j*dt)*H,state)
    return state

def run_spin(c,validate=True):
    if c.n<2 or c.n>24 or c.chi<1 or c.width<=0 or c.dt<=0 or c.duration<=0 or c.sample_every<0:
        raise ValueError("invalid spin config")
    steps=int(np.ceil(c.duration/c.dt))
    dt=c.duration/steps
    mps=MPS(n=c.n,chi=c.chi,svd_tol=c.svd_tol)
    snapshots=[]
    observation_seconds=0.
    def snapshot(t):
        nonlocal observation_seconds
        start=time.perf_counter()
        norm=mps_expectation(mps,{}).real
        excitations=[(1-mps_expectation(mps,{i:Z}).real/norm)/2
                     for i in range(c.n)]
        snapshots.append({"time":float(t),"excitation_proxy":list(map(float,excitations))})
        observation_seconds+=time.perf_counter()-start
    start=time.perf_counter()
    if c.sample_every:snapshot(0.)
    even,odd=zz(-c.j*dt/2),zz(-c.j*dt)
    for k in range(steps):
        fields=drive_fields((k+.5)*dt,c)
        for i in range(c.n):mps.apply_one(i,onsite_gate(c.h,float(fields[i]),dt/2))
        for i in range(0,c.n-1,2):mps.apply_adjacent(i,even)
        for i in range(1,c.n-1,2):mps.apply_adjacent(i,odd)
        for i in range(0,c.n-1,2):mps.apply_adjacent(i,even)
        for i in range(c.n):mps.apply_one(i,onsite_gate(c.h,float(fields[i]),dt/2))
        if c.sample_every and ((k+1)%c.sample_every==0 or k+1==steps):
            snapshot((k+1)*dt)
    elapsed=time.perf_counter()-start
    initial=-c.h*c.n-c.j*(c.n-1)
    excitation=mps_H0_energy(mps,c)-initial
    reference=None
    fidelity=None
    if validate and c.n<=10:
        state=sparse_midpoint_reference(c,steps)
        approx=mps.state_for_validation()
        fidelity=float(abs(np.vdot(state,approx))**2/
                       (np.vdot(state,state).real*np.vdot(approx,approx).real))
        reference=float(np.dot(abs(state)**2,H0_diagonal(c)).real-initial)
    return dict(config=c.__dict__,steps=steps,
                absorbed_work_excitation_energy=float(excitation),
                sparse_reference_excitation_energy=reference,
                absolute_energy_error=(abs(excitation-reference)
                                       if reference is not None else None),
                fidelity_vs_sparse_midpoint=fidelity,
                peak_mps_coefficients=mps.peak_tensor_coefficients,
                local_svd_count=mps.svd_calls,
                evolution_seconds=elapsed,
                observation_seconds=observation_seconds,
                snapshots=snapshots,
                warning="Closed spin model: excitation is not irreversible frictional heat")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--n",type=int,default=6)
    ap.add_argument("--chi",type=int,default=8)
    ap.add_argument("--dt",type=float,default=.03)
    ap.add_argument("--sample-every",type=int,default=5)
    args=ap.parse_args()
    base=PTConfig()
    periodic=run_pt(base)
    quasi=run_pt(replace(base,quasiperiodic_ratio=.4))
    quantum=run_spin(SpinConfig(n=args.n,chi=args.chi,dt=args.dt,
                                sample_every=args.sample_every))
    control=run_spin(SpinConfig(n=args.n,chi=args.chi,dt=args.dt,amplitude=0.))
    report={"status":"known models, exploratory computation, no discovery",
            "friction_classical_periodic":periodic,
            "friction_classical_quasiperiodic":quasi,
            "driven_quantum_spin_analogy":quantum,"spin_no_drive_control":control,
            "caveat":"Quasiperiodic substrate changes corrugation and cannot by itself establish superlubricity or golden-ratio advantage."}
    output=Path(__file__).with_name("quantum_workspace_resultats_08.json")
    output.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
    print("PT periodic: heat =",periodic["viscous_heat"],
          "energy balance error =",periodic["maximum_energy_balance_error"])
    print("PT quasi: heat =",quasi["viscous_heat"],
          "energy balance error =",quasi["maximum_energy_balance_error"])
    print("Spin: work/excitation =",quantum["absorbed_work_excitation_energy"],
          "fidelity vs sparse midpoint =",quantum["fidelity_vs_sparse_midpoint"])
    if quantum["snapshots"]:
        try:
            import matplotlib.pyplot as plt
            arr=np.array([r["excitation_proxy"] for r in quantum["snapshots"]])
            ts=[r["time"] for r in quantum["snapshots"]]
            fig,ax=plt.subplots(figsize=(9,4.4))
            im=ax.imshow(arr.T,aspect="auto",origin="lower",interpolation="nearest",
                         extent=[ts[0],ts[-1],-.5,args.n-.5],vmin=0,vmax=1,cmap="magma")
            ax.set_xlabel("Simulation time (dimensionless)")
            ax.set_ylabel("Spin site (not a real atom)")
            ax.set_title("Local excitation under a moving drive (QWX-08)")
            fig.colorbar(im,ax=ax,label="Local flipped-spin probability")
            fig.tight_layout()
            fig.savefig(output.with_name("quantum_workspace_excitation_locale_08.png"),dpi=165)
            plt.close(fig)
        except ImportError:
            pass
    print("Result:",output)
    return report

if __name__=="__main__":
    main()
