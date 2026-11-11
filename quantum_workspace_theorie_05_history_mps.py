#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quantum Workspace X — Théorie 05 : prédiction par historique de MPS.

Aucune politique sauf l'oracle ne lit les portes du prochain intervalle.
La fonction d'onde n'est jamais reconstruite par les contrôleurs ; la
validation dense indépendante est réservée aux expériences n<=10.
La carte d'information mutuelle contient aussi les corrélations classiques.
Les mesures de temps Python ne sont pas des benchmarks matériels fiables.

Exécution : python quantum_workspace_theorie_05_history_mps.py
Dépendances : numpy et quantum_workspace_theorie_04_predictive_mps.py
"""
from __future__ import annotations
import argparse
import json
import time
from pathlib import Path
import numpy as np
import quantum_workspace_theorie_04_predictive_mps as q4

def reduced_density_from_mps(mps: q4.MPS, kept_sites: tuple[int,...]) -> np.ndarray:
    """Matrice densité 1 ou 2 sites par contractions MPS, sans état complet."""
    assert tuple(sorted(set(kept_sites))) == kept_sites
    assert all(0 <= j < mps.n for j in kept_sites)
    env=np.ones((1,1,1,1),dtype=complex)
    kept=set(kept_sites)
    for p,A in enumerate(mps.tensors):
        if p in kept:
            env=np.einsum('abxy,apr,bqs->rsxpyq',env,A,A.conj(),optimize=True)
            dr,ds,x,_,y,_=env.shape
            env=env.reshape(dr,ds,x*2,y*2)
        else:
            env=np.einsum('abxy,apr,bps->rsxy',env,A,A.conj(),optimize=True)
    rho=env[0,0]
    trace=np.trace(rho)
    if abs(trace)<1e-14:
        raise ValueError("MPS norm too small")
    rho=rho/trace
    return (rho+rho.conj().T)/2

def entropy(rho):
    eig=np.maximum(np.linalg.eigvalsh(rho).real,0)
    eig=eig[eig>1e-13]
    return float(-np.sum(eig*np.log2(eig)))

def mi_from_mps(mps: q4.MPS):
    """Information mutuelle courante de toutes les paires (pas du futur)."""
    n=mps.n
    one=[entropy(reduced_density_from_mps(mps,(i,))) for i in range(n)]
    mi=np.zeros((n,n))
    for i in range(n):
        for j in range(i+1,n):
            h=entropy(reduced_density_from_mps(mps,(i,j)))
            a,b=mps.order[i],mps.order[j]
            mi[a,b]=mi[b,a]=max(0.0,one[i]+one[j]-h)
    return mi

def greedy_pairs_from_mi(mi):
    n=len(mi)
    edges=sorted((-float(mi[i,j]),i,j)
                 for i in range(n) for j in range(i+1,n))
    taken=set()
    pairs=[]
    for _,a,b in edges:
        if a not in taken and b not in taken:
            pairs.append((a,b))
            taken.add(a);taken.add(b)
    assert len(taken)==n
    return pairs

def weighted_distance(order,mi):
    pos={q:i for i,q in enumerate(order)}
    return sum(mi[i,j]*abs(pos[i]-pos[j]) for i in range(len(mi))
               for j in range(i+1,len(mi)))

def target_from_mi(order,mi,penalty=0.2):
    target=q4.group_pairs(tuple(order),greedy_pairs_from_mi(mi))
    gain=weighted_distance(order,mi)-weighted_distance(target,mi)
    swaps=q4.inversions_from_to(tuple(order),target)
    return target if gain>penalty*swaps else tuple(order)

def forecast_trend(previous,latest,beta=0.7):
    """Extrapolation linéaire de deux cartes antérieures ; aucune porte future."""
    return np.clip(latest+beta*(latest-previous),0.0,2.0)

def create_microbatches(n=8,repeats=4,scenario="persistent",seed=15):
    if n%2 or n<4:raise ValueError("n must be even >=4")
    rng=np.random.default_rng(seed)
    types=q4.pairings(n)
    batches=[]
    for t in range(3*repeats):
        if scenario=="persistent":
            idx=0 if t<2*repeats else 2
        elif scenario=="switching":
            idx=(t//repeats)%3
        elif scenario=="random":
            idx=None
        else:raise ValueError(scenario)
        if idx is None:
            perm=list(map(int,rng.permutation(n)))
            pairs=list(zip(perm[0::2],perm[1::2]))
        else:
            pairs=types[idx]
        angle=float(.22+.06*np.sin(t))
        events=[('zz',int(a),int(b),angle) for a,b in pairs]
        for k in range(n):
            if (k+t)%3==0:
                events.append(('ry',k,float(.09*(1+t%3))))
        batches.append(events)
    return batches

def exact_state(n,batches):
    if n>10:return None
    psi=np.zeros(2**n,complex)
    psi[0]=1
    for k in range(n):
        psi=q4.apply_full_gate(psi,(k,),q4.H,n)
    for batch in batches:
        for event in batch:
            if event[0]=="zz":
                psi=q4.apply_full_gate(psi,(event[1],event[2]),q4.zz(event[3]),n)
            else:
                psi=q4.apply_full_gate(psi,(event[1],),q4.ry(event[2]),n)
    return psi

def run_policy(policy,batches,n=8,chi=16,penalty=.2):
    """Historique seul, sauf oracle étiqueté et non comparable comme prédicteur."""
    assert policy in ("fixed","history","history_confident","reactive","trend","oracle")
    started=time.perf_counter()
    mps=q4.MPS(n=n,chi=chi,svd_tol=1e-13)
    for k in range(n):mps.apply_one(k,q4.H)
    previous=None
    latest=None
    prevpairs=None
    penultimate=None
    prediction_mae=[]
    persistence_mae=[]
    measurement_seconds=0.0
    decision_seconds=0.0
    reorder_events=0
    for batch in batches:
        tick=time.perf_counter()
        if policy=="fixed":
            target=tuple(mps.order)
        elif policy=="history":
            target=(q4.choose_target(mps.order,prevpairs,threshold=1.0)
                    if prevpairs is not None else tuple(mps.order))
        elif policy=="history_confident":
            stable=(penultimate is not None and
                    set(map(frozenset,prevpairs))==set(map(frozenset,penultimate)))
            target=(q4.choose_target(mps.order,prevpairs,threshold=1.0)
                    if stable else tuple(mps.order))
        elif policy=="oracle":
            target=q4.choose_target(mps.order,q4.pairs_in_batch(batch),threshold=1.0)
        elif latest is None:
            target=tuple(mps.order)
        elif policy=="reactive":
            target=target_from_mi(mps.order,latest,penalty=penalty)
        elif policy=="trend":
            guess=forecast_trend(previous,latest) if previous is not None else latest
            target=target_from_mi(mps.order,guess,penalty=penalty)
        decision_seconds+=time.perf_counter()-tick
        if target!=tuple(mps.order):reorder_events+=1
        mps.reorder(target)
        for ev in batch:
            if ev[0]=="zz":mps.apply_nonlocal(ev[1],ev[2],q4.zz(ev[3]))
            else:mps.apply_one(ev[1],q4.ry(ev[2]))
        penultimate,prevpairs=prevpairs,q4.pairs_in_batch(batch)
        if policy in ("reactive","trend"):
            measure_start=time.perf_counter()
            current=mi_from_mps(mps)
            measurement_seconds+=time.perf_counter()-measure_start
            if latest is not None:
                persistence_mae.append(float(np.mean(np.abs(current-latest))))
                if previous is not None:
                    forecast=forecast_trend(previous,latest)
                    prediction_mae.append(float(np.mean(np.abs(current-forecast))))
            previous,latest=latest,current
    elapsed=time.perf_counter()-started
    result={"policy":policy,"swaps":mps.swaps,
            "layout_swaps":mps.layout_swaps,"route_swaps":mps.route_swaps,
            "svd_calls":mps.svd_calls,
            "peak_coefficients":mps.peak_tensor_coefficients,
            "peak_svd_input":mps.peak_svd_input_coefficients,
            "discarded_weight_proxy":mps.discarded_weight_proxy,
            "reorder_events":reorder_events,"elapsed_seconds":elapsed,
            "mi_measure_seconds":measurement_seconds,
            "decision_seconds":decision_seconds,
            "forecast_mae":float(np.mean(prediction_mae)) if prediction_mae else None,
            "persistence_mae":float(np.mean(persistence_mae)) if persistence_mae else None}
    return result,mps

def benchmark(n=8,chi=16,repeats=4,seed=15,
              scenarios=("persistent","switching","random")):
    rows=[]
    for scenario in scenarios:
        batches=create_microbatches(n,repeats,scenario,seed)
        ref=exact_state(n,batches)
        cases=[]
        for policy in ("fixed","history","history_confident","reactive","trend","oracle"):
            row,mps=run_policy(policy,batches,n=n,chi=chi)
            if ref is not None:
                psi=mps.state_for_validation()
                row["fidelity"]=float(abs(np.vdot(ref,psi))**2/
                    (np.vdot(ref,ref).real*np.vdot(psi,psi).real))
            else:row["fidelity"]=None
            cases.append(row)
        rows.append({"scenario":scenario,"results":cases})
    return {"name":"Quantum Workspace X Theory 05 - MPS history only forecast",
            "n":n,"chi":chi,"repeats":repeats,"seed":seed,
            "note":"Future gates hidden from all except oracle; mutual information includes classical correlations. All circuits synthetic; no general speedup claimed.",
            "scenarios":rows}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--n",type=int,default=8)
    ap.add_argument("--chi",type=int,default=16)
    ap.add_argument("--repeats",type=int,default=4)
    ap.add_argument("--seed",type=int,default=15)
    args=ap.parse_args()
    if args.n%2 or args.n<4 or args.n>16:ap.error("n must be even 4..16")
    report=benchmark(**vars(args))
    dst=Path(__file__).resolve().parent/(
        f"quantum_workspace_resultats_05_n{args.n}_seed{args.seed}.json")
    dst.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
    for scene in report["scenarios"]:
        print("\n",scene["scenario"],"(qubits:",args.n,")")
        for r in scene["results"]:
            print(f"{r['policy']:18s} swaps={r['swaps']:3d} "
                  f"SVD={r['svd_calls']:3d} peak={r['peak_coefficients']:4d} "
                  f"fidelity={r['fidelity']} t={r['elapsed_seconds']:.3f}s")
    print("saved",dst)
    return report

if __name__=="__main__":main()
