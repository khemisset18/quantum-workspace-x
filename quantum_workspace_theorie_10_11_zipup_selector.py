#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quantum Workspace X — Theory 10/11: streaming MPO + cost-aware selector.

Existing MPO/MPS algorithms (not a new quantum law). Zip-up applies the rank-2
MPO one site at a time using SVD, followed by right-canonicalization and a
controlled left-to-right compression sweep. Internal SVDs may be truncated;
local discarded weights DO NOT prove a global fidelity bound.

Policies: swap, mpo_eager (theory 09), zipup, budget_selector.
All policies use only the current gate and present MPS tensors; none sees
future circuit batches. Accuracy independently checked against dense state
on <=10 qubits. Subprocess suite isolates peak Linux ru_maxrss memory.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import time
import numpy as np
import quantum_workspace_theorie_04_predictive_mps as q4
import quantum_workspace_theorie_05_history_mps as q5
import quantum_workspace_theorie_09_hybride_mpo as q9

Z = np.array([1., -1.])
IDENTITY = np.eye(4, dtype=complex)
ROOT = Path(__file__).resolve().parent
POLICIES = ('swap', 'mpo_eager', 'zipup', 'budget_selector')


def expanded_site(A, i, lo, hi, theta):
    """Apply one tensor of the rank-2 ZZ MPO to one MPS site."""
    if i == lo:
        return np.stack([np.cos(theta)*A,
                         -1j*np.sin(theta)*A*Z[None,:,None]], axis=-1
                        ).reshape(A.shape[0], 2, 2*A.shape[2])
    if i == hi:
        return np.stack([A, A*Z[None,:,None]], axis=1
                        ).reshape(2*A.shape[0], 2, A.shape[2])
    left,_,right=A.shape
    tmp=np.zeros((left,2,right,2,2), dtype=complex)
    tmp[:,:,:,0,0]=A
    tmp[:,:,:,1,1]=A
    return tmp.transpose(0,3,1,2,4).reshape(2*left,2,2*right)


def right_canonicalize(mps, start):
    """Make all tensors right of start right-orthogonal (no truncation)."""
    for i in range(mps.n-1, start, -1):
        A=mps.tensors[i]
        l,_,r=A.shape
        Q,R=np.linalg.qr(A.reshape(l,2*r).T,mode='reduced')
        k=Q.shape[1]
        mps.tensors[i]=Q.T.reshape(k,2,r)
        mps.tensors[i-1]=np.tensordot(mps.tensors[i-1],R.T,axes=(-1,0))
        mps.update_peaks()


def apply_zz_zipup(mps, a, b, theta, oversample=2):
    """Streaming MPO contraction. Local cap is oversample*chi.

    A forward SVD pass contracts a single MPO tensor and MPS tensor at once.
    It DOES NOT materialize the whole enlarged MPS as eager MPO does.
    Then right-canonicalization and a standard SVD compression sweep
    control the final MPS bond dimension.

    Caution: optional forward truncation is not variationally optimal;
    total discarded weight does not rigorously bound fidelity.
    """
    lo,hi=sorted((mps.order.index(a),mps.order.index(b)))
    if hi==lo+1:
        mps.apply_adjacent(lo,q4.zz(theta))
        return
    carry=None
    cap=int(max(1,oversample*mps.chi))
    for i in range(lo,hi+1):
        local=expanded_site(mps.tensors[i],i,lo,hi,theta)
        if carry is not None:
            assert carry.shape[1]==local.shape[0]
            local=np.tensordot(carry,local,axes=(1,0))
        mps.peak_working_coefficients=max(
            getattr(mps,'peak_working_coefficients',0),
            int(mps.tensor_coefficients()+local.size+(0 if carry is None else carry.size)))
        if i<hi:
            l,_,r=local.shape
            mat=local.reshape(2*l,r)
            U,s,Vh=np.linalg.svd(mat,full_matrices=False)
            mps.svd_calls+=1
            mps.total_svd_elements+=mat.size
            keep=min(cap,len(s))
            total=float(np.dot(s,s))
            if total and mps.svd_tol>0:
                # Forward truncation is optional and only a heuristic.
                tail=np.cumsum((s[::-1]**2))[::-1]
                for k in range(1,keep+1):
                    if (float(tail[k]) if k<len(s) else 0.)/total<=mps.svd_tol:
                        keep=k
                        break
            mps.discarded_weight_proxy+=(
                float(np.dot(s[keep:],s[keep:]))/total if total else 0.)
            mps.tensors[i]=U[:,:keep].reshape(l,2,keep)
            carry=s[:keep,None]*Vh[:keep,:]
        else:
            mps.tensors[i]=local
        mps.update_peaks()

    # The right environment must be orthonormal before local SVD truncation.
    right_canonicalize(mps,lo)
    for i in range(lo,hi):
        mps.apply_adjacent(i,IDENTITY)


def proposed_choice(mps,a,b,memory_factor=3.0):
    """Conservative rule: no future gates, no unmeasured speedup claim.

    The memory estimate is a crude upper bound based on tensor sizes; the
    measured RSS is authoritative. For adjacent gates both policies coincide.
    """
    lo,hi=sorted((mps.order.index(a),mps.order.index(b)))
    if hi-lo<=2:
        return 'swap'
    current=mps.tensor_coefficients()
    # Guardrail against MPS×MPO growth. May reject useful zip-up cases.
    upper=q9.predicted_mpo_coefficients(mps,a,b)
    return 'zipup' if upper<=memory_factor*max(current,1) else 'swap'


def run(mode,n=8,chi=16,repeats=2,scenario='random',seed=11,
        oversample=2,memory_factor=3.0):
    if mode not in POLICIES: raise ValueError(mode)
    if n<4 or n%2 or n>20 or chi<1:raise ValueError('n even, 4..20; chi>=1')
    batches=q5.create_microbatches(n,repeats,scenario,seed)
    reference=q5.exact_state(n,batches) if n<=10 else None
    start=time.perf_counter()
    mps=q4.MPS(n=n,chi=chi,svd_tol=1e-13)
    for j in range(n):mps.apply_one(j,q4.H)
    mps.peak_working_coefficients=mps.tensor_coefficients()
    counts={'swap':0,'mpo_eager':0,'zipup':0}
    decisions=0
    for batch in batches:
        for ev in batch:
            if ev[0]=='ry':
                mps.apply_one(ev[1],q4.ry(ev[2]))
                continue
            _,a,b,angle=ev
            choice=proposed_choice(mps,a,b,memory_factor) if mode=='budget_selector' else mode
            decisions+=1
            counts[choice]+=1
            if choice=='swap':
                mps.apply_nonlocal(a,b,q4.zz(angle))
            elif choice=='mpo_eager':
                q9.apply_zz_mpo(mps,a,b,angle)
            else:
                apply_zz_zipup(mps,a,b,angle,oversample=oversample)
    seconds=time.perf_counter()-start
    fid=None
    if reference is not None:
        actual=mps.state_for_validation()
        fid=float(abs(np.vdot(actual,reference))**2/
                  (np.vdot(actual,actual).real*np.vdot(reference,reference).real))
    return {
        'policy':mode,'n':n,'chi':chi,'scenario':scenario,
        'seed':seed,'repeats':repeats,'oversample':oversample,
        'memory_factor':memory_factor,'fidelity':fid,
        'seconds':seconds,'maxrss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'peak_mps_coefficients':mps.peak_tensor_coefficients,
        'peak_working_coefficients_proxy':mps.peak_working_coefficients,
        'peak_svd_input_coefficients':mps.peak_svd_input_coefficients,
        'svd_calls':mps.svd_calls,'swaps':mps.swaps,
        'choices':counts,'decision_count':decisions,
        'discarded_weight_proxy':mps.discarded_weight_proxy
    }


def suite(n,chi,repeats,scenario,seed,oversample=2,memory_factor=3.0):
    """Run each policy in a SEPARATE Python process for RSS measurements."""
    result=[]
    env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
    for mode in POLICIES:
        command=[sys.executable,str(Path(__file__).resolve()),'--mode',mode,
            '--n',str(n),'--chi',str(chi),'--repeats',str(repeats),
            '--scenario',scenario,'--seed',str(seed),
            '--oversample',str(oversample),'--memory-factor',str(memory_factor)]
        p=subprocess.run(command,capture_output=True,text=True,check=True,env=env)
        result.append(json.loads(p.stdout))
    return {'name':'Quantum Workspace X T10+T11 — MPO zip-up & selector',
            'status':'exploratory; methods established; no speedup claimed',
            'rss_units':'Linux ru_maxrss in KiB, per isolated subprocess',
            'method_warning':'Forward zip-up truncation not a rigorous global error bound.',
            'results':result}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--mode',choices=POLICIES)
    p.add_argument('--n',type=int,default=8)
    p.add_argument('--chi',type=int,default=16)
    p.add_argument('--repeats',type=int,default=2)
    p.add_argument('--scenario',choices=('random','switching','persistent'),default='random')
    p.add_argument('--seed',type=int,default=11)
    p.add_argument('--oversample',type=int,default=2)
    p.add_argument('--memory-factor',type=float,default=3.)
    args=p.parse_args()
    if args.mode:
        print(json.dumps(run(**vars(args)),ensure_ascii=False))
    else:
        kwargs=vars(args); kwargs.pop('mode')
        data=suite(**kwargs)
        dst=ROOT/f'quantum_workspace_resultats_10_11_n{args.n}_{args.scenario}.json'
        dst.write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf-8')
        print('Measured (each method in an isolated process):')
        for x in data['results']:
            print(f"{x['policy']:16s} fidelity={x['fidelity']} time={x['seconds']:.4f}s "
                  f"RSS={x['maxrss_kib']}KiB swaps={x['swaps']} SVD={x['svd_calls']}")
        print('Saved',dst)
    return 0


if __name__=='__main__':
    raise SystemExit(main())
