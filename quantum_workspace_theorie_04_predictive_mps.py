#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quantum Workspace X — Theory 04: predictive routing on a compressed MPS.

This is a routing / circuit compilation experiment, NOT an entanglement
forecast or a newly discovered quantum algorithm. Compressed MPS tensors are
maintained throughout the evolution; dense vectors are formed only for
small (n <= 10) independent accuracy verification.

Controls: natural, golden initial order, precompiled static order (knows the
whole circuit), reactive (previous batch) and lookahead (next batch).
Both routing and placement SWAPs are counted and timed.

Run: python quantum_workspace_theorie_04_predictive_mps.py [--n 8 --chi 16]
Requires: numpy.
"""
from __future__ import annotations
import argparse
import json
import time
from pathlib import Path
import numpy as np

PHI = (1 + np.sqrt(5)) / 2
H = np.array([[1, 1], [1, -1]], complex) / np.sqrt(2)
SWAP = np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]], complex)


def ry(theta):
    c, s = np.cos(theta/2), np.sin(theta/2)
    return np.array([[c, -s], [s, c]], complex)


def zz(theta):
    return np.diag(np.exp(-1j * theta * np.array([1, -1, -1, 1]))).astype(complex)


def golden_order(n):
    return tuple(sorted(range(n), key=lambda i: ((i / PHI) % 1.0, i)))


def pairings(n):
    assert n % 2 == 0 and n >= 4
    half = n//2
    return [tuple((i, i+half) for i in range(half)),
            tuple((2*i, 2*i+1) for i in range(half)),
            tuple((i, n-1-i) for i in range(half))]


def make_batches(n=8, passes=4):
    batches = []
    for phase, pairs in enumerate(pairings(n)):
        steps=[]
        for repeat in range(passes):
            angle = 0.12 + 0.17 * ((repeat + phase) % 3)
            for a,b in pairs:
                steps.append(('zz',a,b,float(angle)))
            for q in range(n):
                if (q + repeat + phase) % 3 == 0:
                    steps.append(('ry',q,float(0.08*(repeat+1))))
        batches.append(steps)
    return batches


def pairs_in_batch(batch):
    return [(event[1],event[2]) for event in batch if event[0]=='zz']


def distance_cost(order, pairs):
    pos = {q:i for i,q in enumerate(order)}
    return 2*sum(max(0,abs(pos[a]-pos[b])-1) for a,b in pairs)


def group_pairs(order, pairs):
    pos = {q:i for i,q in enumerate(order)}
    unique = list(dict.fromkeys(tuple(sorted((a,b))) for a,b in pairs))
    unique.sort(key=lambda p: min(pos[p[0]], pos[p[1]]))
    arranged=[]
    for a,b in unique:
        arranged.extend((a,b) if pos[a]<pos[b] else (b,a))
    arranged.extend(q for q in order if q not in arranged)
    assert sorted(arranged) == list(range(len(order)))
    return tuple(arranged)


def inversions_from_to(source,target):
    target_pos={q:i for i,q in enumerate(target)}
    values=[target_pos[q] for q in source]
    return sum(values[i]>values[j] for i in range(len(values)) for j in range(i+1,len(values)))


def choose_compiled_order(n, batches):
    """Static baseline with access to the whole circuit, restricted candidates."""
    identity=tuple(range(n))
    candidates=[identity, golden_order(n)]
    all_pairs=[]
    for batch in batches:
        pairs=pairs_in_batch(batch)
        all_pairs.extend(pairs)
        candidates.append(group_pairs(identity,pairs))
        candidates.append(tuple(reversed(candidates[-1])))
    return min(candidates,key=lambda order:(distance_cost(order,all_pairs),order))


class MPS:
    """Nearest-neighbor SVD update, storing the wavefunction as MPS tensors."""
    def __init__(self, n=8, chi=8, svd_tol=1e-12, order=None):
        self.n=n
        self.order=list(range(n)) if order is None else list(order)
        assert sorted(self.order)==list(range(n))
        self.tensors=[np.array([[[1.0+0j],[0.0+0j]]]) for _ in range(n)]
        self.chi=chi
        self.svd_tol=svd_tol
        self.swaps=0
        self.layout_swaps=0
        self.route_swaps=0
        self.svd_calls=0
        self.total_svd_elements=0
        self.discarded_weight_proxy=0.0
        self.peak_tensor_coefficients=self.tensor_coefficients()
        self.peak_svd_input_coefficients=0

    def tensor_coefficients(self):
        return sum(t.size for t in self.tensors)

    def update_peaks(self, msize=0):
        self.peak_tensor_coefficients=max(self.peak_tensor_coefficients,self.tensor_coefficients())
        self.peak_svd_input_coefficients=max(self.peak_svd_input_coefficients,msize)

    def apply_one(self, logical, gate):
        p=self.order.index(logical)
        self.tensors[p]=np.einsum('oi,aib->aob',gate,self.tensors[p],optimize=True)
        self.update_peaks()

    def apply_adjacent(self, p, gate):
        A,B=self.tensors[p],self.tensors[p+1]
        left,_,mid=A.shape
        mid2,_,right=B.shape
        assert mid==mid2
        block=np.einsum('aib,bjc->aijc',A,B,optimize=True)
        block=np.einsum('uvij,aijc->auvc',gate.reshape(2,2,2,2),block,optimize=True)
        mat=block.reshape(2*left,2*right)
        U,s,Vh=np.linalg.svd(mat,full_matrices=False)
        self.svd_calls+=1
        self.total_svd_elements+=mat.size
        total=float(np.dot(s,s))
        keep=min(self.chi,len(s))
        if total>0 and self.svd_tol>0:
            tail=np.cumsum((s[::-1]**2))[::-1]
            for k in range(1,keep+1):
                lost=float(tail[k]) if k<len(s) else 0.0
                if lost/total <= self.svd_tol:
                    keep=k
                    break
        discarded=float(np.dot(s[keep:],s[keep:]))/total if total else 0.0
        self.discarded_weight_proxy+=discarded
        self.tensors[p]=U[:,:keep].reshape(left,2,keep)
        self.tensors[p+1]=(s[:keep,None]*Vh[:keep,:]).reshape(keep,2,right)
        self.update_peaks(mat.size)

    def swap_sites(self,p,layout=False):
        self.apply_adjacent(p,SWAP)
        self.order[p],self.order[p+1]=self.order[p+1],self.order[p]
        self.swaps+=1
        if layout: self.layout_swaps+=1
        else: self.route_swaps+=1

    def reorder(self,target):
        assert sorted(target)==list(range(self.n))
        for p, logical in enumerate(target):
            j=self.order.index(logical)
            while j>p:
                self.swap_sites(j-1,layout=True)
                j-=1
        assert tuple(self.order)==tuple(target)

    def apply_nonlocal(self,a,b,gate):
        pa,pb=self.order.index(a),self.order.index(b)
        if pa>pb: pa,pb=pb,pa
        used=[]
        for p in range(pb-1,pa,-1):
            self.swap_sites(p)
            used.append(p)
        self.apply_adjacent(pa,gate)
        for p in reversed(used):
            self.swap_sites(p)

    def state_for_validation(self):
        """DENSE reconstruction ONLY AFTER evolution, for n<=10."""
        assert self.n<=10
        temp=self.tensors[0]
        for nxt in self.tensors[1:]:
            temp=np.tensordot(temp,nxt,axes=([-1],[0]))
        site_vector=temp.reshape((2,)*self.n)
        inverse=np.argsort(self.order)
        return site_vector.transpose(inverse).reshape(-1)


def apply_full_gate(psi, ids, matrix, n):
    """Independent dense reference; never used by the MPS engine."""
    assert n<=10
    ids=tuple(ids)
    remaining=tuple(i for i in range(n) if i not in ids)
    x=psi.reshape((2,)*n).transpose(ids+remaining).reshape(2**len(ids),-1)
    x=(matrix@x).reshape((2,)*n)
    p=ids+remaining
    return x.transpose(np.argsort(p)).reshape(-1)


def exact_reference(n,batches):
    assert n<=10
    state=np.zeros(2**n,complex);state[0]=1.0
    for i in range(n): state=apply_full_gate(state,(i,),H,n)
    for batch in batches:
        for ev in batch:
            if ev[0]=='zz': state=apply_full_gate(state,(ev[1],ev[2]),zz(ev[3]),n)
            else: state=apply_full_gate(state,(ev[1],),ry(ev[2]),n)
    return state


def choose_target(order, pairs, threshold=1.0):
    candidate=group_pairs(order,pairs)
    before=distance_cost(order,pairs)
    after=distance_cost(candidate,pairs)
    cost=inversions_from_to(order,candidate)
    if before-after > threshold*cost:
        return candidate
    return tuple(order)


def run_strategy(strategy,n=8,chi=8,passes=4,svd_tol=1e-12):
    batches=make_batches(n,passes)
    initial=(golden_order(n) if strategy=='golden' else
             choose_compiled_order(n,batches) if strategy=='compiled_static' else
             tuple(range(n)))
    start=time.perf_counter()
    mps=MPS(n,chi,svd_tol,order=initial)
    for i in range(n):mps.apply_one(i,H)
    previous_pairs=None
    decisions=[]
    for batch in batches:
        if strategy=='lookahead':
            observed=pairs_in_batch(batch) # known future gates, NOT entanglement forecast
            target=choose_target(mps.order,observed)
        elif strategy=='reactive' and previous_pairs is not None:
            target=choose_target(mps.order,previous_pairs)
        else:
            target=tuple(mps.order)
        before=mps.swaps
        mps.reorder(target)
        decisions.append({'placement':list(target),'layout_swaps_this_batch':mps.swaps-before})
        for ev in batch:
            if ev[0]=='zz':mps.apply_nonlocal(ev[1],ev[2],zz(ev[3]))
            else:mps.apply_one(ev[1],ry(ev[2]))
        previous_pairs=pairs_in_batch(batch)
    elapsed=time.perf_counter()-start
    result={'policy':strategy,'n':n,'chi':chi,'elapsed_seconds':elapsed,
            'svd_calls':mps.svd_calls,'swap_total':mps.swaps,
            'layout_swaps':mps.layout_swaps,'route_swaps':mps.route_swaps,
            'peak_tensor_coefficients':mps.peak_tensor_coefficients,
            'final_tensor_coefficients':mps.tensor_coefficients(),
            'peak_svd_input_coefficients':mps.peak_svd_input_coefficients,
            'total_svd_input_coefficients':mps.total_svd_elements,
            'sum_local_discarded_weight_proxy':mps.discarded_weight_proxy,
            'decisions':decisions, 'final_order':mps.order}
    return result,mps


def benchmark(n=8,chi=8,passes=4,svd_tol=1e-12):
    batches=make_batches(n,passes)
    reference=exact_reference(n,batches) if n<=10 else None
    rows=[]
    for strategy in ('natural','golden','compiled_static','reactive','lookahead'):
        row,mps=run_strategy(strategy,n,chi,passes,svd_tol)
        if reference is not None:
            actual=mps.state_for_validation()
            fidelity=abs(np.vdot(reference,actual))**2/(np.vdot(reference,reference).real*np.vdot(actual,actual).real)
            row['fidelity_vs_exact']=float(fidelity)
        else:row['fidelity_vs_exact']=None
        rows.append(row)
    return {'name':'Quantum Workspace X theory 04 — compressed MPS predictive routing',
            'note':'Known future gates are a routing hint, not an entanglement predictor. SVD truncation is standard.',
            'n':n,'chi':chi,'passes':passes,'svd_tol':svd_tol,'rows':rows}


def main():
    cli=argparse.ArgumentParser()
    cli.add_argument('--n',type=int,default=8)
    cli.add_argument('--chi',type=int,default=8)
    cli.add_argument('--passes',type=int,default=4)
    args=cli.parse_args()
    if args.n%2 or args.n<4 or args.n>24 or args.chi<1 or args.passes<1:
        cli.error('n must be even 4..24, chi>=1, passes>=1')
    result=benchmark(n=args.n,chi=args.chi,passes=args.passes)
    output=Path(__file__).resolve().parent/f'quantum_workspace_resultats_04_n{args.n}_chi{args.chi}.json'
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'Quantum Workspace X / theory 04 / n={args.n} / chi={args.chi}')
    print('Policy       SWAPs (layout) SVDs  coefficients  fidelity      time(s)')
    for r in result['rows']:
        f=r['fidelity_vs_exact']
        print(f'{r["policy"]:<12} {r["swap_total"]:>4} ({r["layout_swaps"]:<3})    {r["svd_calls"]:>4} '
              f'{r["peak_tensor_coefficients"]:>8}    {f if f is not None else "--":<12} {r["elapsed_seconds"]:.4f}')
    print('Saved:',output)
    return result


if __name__=='__main__':
    main()
