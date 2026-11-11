#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""QWX Theory 09: long-range MPO vs SWAP for MPS quantum simulation.

Existing methods; the experiment studies a simple memory-aware policy.
No quantum hardware, no entanglement forecasting, no novel physical law.
A dense state is reconstructed ONLY for independent verification (n<=10).
"""
from __future__ import annotations
import argparse
import json
import time
from pathlib import Path
import numpy as np
import quantum_workspace_theorie_04_predictive_mps as q4
import quantum_workspace_theorie_05_history_mps as q5

Z = np.array([1.0, -1.0], dtype=float)
IDENTITY = np.eye(4, dtype=complex)


def apply_zz_mpo(mps: q4.MPS, a: int, b: int, theta: float) -> None:
    """Implement exp(-i theta Z_a Z_b) by a bond-2 MPO, then compress.

    Operator Schmidt decomposition: cos(theta) I - i sin(theta) Z_a Z_b.
    IMPORTANT: right-canonicalize BEFORE truncating the enlarged MPS;
    without this, local singular values are not the Schmidt values.
    """
    assert a != b
    p, r = sorted((mps.order.index(a), mps.order.index(b)))
    if r == p + 1:
        mps.apply_adjacent(p, q4.zz(theta))
        return
    old = mps.tensors
    new = list(old)
    A = old[p]
    new[p] = np.stack(
        [np.cos(theta) * A, -1j * np.sin(theta) * A * Z[None, :, None]],
        axis=-1).reshape(A.shape[0], 2, A.shape[2] * 2)
    for i in range(p + 1, r):
        A = old[i]
        left, _, right = A.shape
        tmp = np.zeros((left, 2, right, 2, 2), dtype=complex)
        tmp[:, :, :, 0, 0] = A
        tmp[:, :, :, 1, 1] = A
        new[i] = tmp.transpose(0, 3, 1, 2, 4).reshape(left * 2, 2, right * 2)
    A = old[r]
    new[r] = np.stack([A, A * Z[None, :, None]], axis=1).reshape(
        A.shape[0] * 2, 2, A.shape[2])
    mps.tensors = new
    mps.update_peaks()
    # Canonicalize the right environment. Crucial for valid truncation.
    for i in range(mps.n - 1, p, -1):
        A = mps.tensors[i]
        left, _, right = A.shape
        Q, R = np.linalg.qr(A.reshape(left, 2 * right).T, mode='reduced')
        newleft = Q.shape[1]
        mps.tensors[i] = Q.T.reshape(newleft, 2, right)
        mps.tensors[i - 1] = np.tensordot(
            mps.tensors[i - 1], R.T, axes=(-1, 0))
    mps.update_peaks()
    for i in range(p, r):
        mps.apply_adjacent(i, IDENTITY)


def predicted_mpo_coefficients(mps: q4.MPS, a: int, b: int) -> int:
    """Count upper bound for all enlarged tensors before QR compression."""
    lo, hi = sorted((mps.order.index(a), mps.order.index(b)))
    sizes = [t.size for t in mps.tensors]
    if hi == lo + 1:
        return sum(sizes)
    return (sum(sizes) + sizes[lo] + sizes[hi]
            + 3 * sum(sizes[lo + 1:hi]))


def choose(mode: str, mps: q4.MPS, a: int, b: int) -> str:
    if mode in ('swap', 'mpo'):
        return mode
    gap = abs(mps.order.index(a) - mps.order.index(b))
    if mode == 'hybrid':
        return 'mpo' if gap >= 3 else 'swap'
    if mode == 'hybrid_budget':
        # Fixed transparent heuristic, not an ML model or an optimal policy.
        current = mps.tensor_coefficients()
        would_need = predicted_mpo_coefficients(mps, a, b)
        return 'mpo' if gap >= 3 and would_need <= 2 * current else 'swap'
    raise ValueError(mode)


def run(n=8, chi=16, repeats=3, seed=15,
        scenario='switching', mode='hybrid_budget'):
    batches = q5.create_microbatches(
        n=n, repeats=repeats, scenario=scenario, seed=seed)
    reference = q5.exact_state(n, batches) if n <= 10 else None
    tick = time.perf_counter()
    mps = q4.MPS(n=n, chi=chi, svd_tol=1e-13)
    for site in range(n):
        mps.apply_one(site, q4.H)
    counts = {'swap': 0, 'mpo': 0}
    for batch in batches:
        for ev in batch:
            if ev[0] == 'zz':
                _, a, b, theta = ev
                method = choose(mode, mps, a, b)
                counts[method] += 1
                if method == 'swap':
                    mps.apply_nonlocal(a, b, q4.zz(theta))
                else:
                    apply_zz_mpo(mps, a, b, theta)
            else:
                mps.apply_one(ev[1], q4.ry(ev[2]))
    seconds = time.perf_counter() - tick
    fidelity = None
    if reference is not None:
        actual = mps.state_for_validation()
        fidelity = float(abs(np.vdot(reference, actual))**2 /
            (np.vdot(reference, reference).real *
             np.vdot(actual, actual).real))
    return {
        'n': n, 'chi': chi, 'repeats': repeats, 'seed': seed,
        'scenario': scenario, 'mode': mode, 'elapsed_seconds': seconds,
        'fidelity': fidelity, 'gate_counts': counts,
        'swaps': mps.swaps, 'svd_calls': mps.svd_calls,
        'peak_coefficients': mps.peak_tensor_coefficients,
        'peak_svd_input': mps.peak_svd_input_coefficients,
        'sum_svd_input': mps.total_svd_elements,
        'discarded_weight_proxy': mps.discarded_weight_proxy,
    }


def benchmark(ns=(8, 10), chis=(16, 32),
              scenarios=('persistent', 'switching', 'random'),
              seeds=(11, 15, 23), repeats=2):
    rows = [
        run(n=n, chi=chi, repeats=repeats, seed=seed,
            scenario=scenario, mode=mode)
        for n in ns
        for chi in chis
        for scenario in scenarios
        for seed in seeds
        for mode in ('swap', 'mpo', 'hybrid', 'hybrid_budget')
    ]
    return {
        'title': 'QWX Theory 09 — MPO / SWAP hybrid benchmarking',
        'status': 'exploratory, existing numerical methods',
        'note': ('Timing depends on hardware. MPO may quadruple temporary '
                 'MPS coefficients. Accuracy independently checked for n<=10.'),
        'results': rows,
    }


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--n', type=int, default=8)
    cli.add_argument('--chi', type=int, default=16)
    cli.add_argument('--repeats', type=int, default=3)
    cli.add_argument('--seed', type=int, default=15)
    cli.add_argument('--scenario',
                     choices=('persistent', 'switching', 'random'),
                     default='switching')
    args = cli.parse_args()
    if args.n % 2 or not (4 <= args.n <= 20) or args.chi < 1:
        cli.error('n even and 4..20, chi positive')
    rows = [run(**vars(args), mode=m)
            for m in ('swap', 'mpo', 'hybrid', 'hybrid_budget')]
    outfile = (Path(__file__).resolve().parent /
               f'quantum_workspace_resultats_09_hybride_n{args.n}.json')
    outfile.write_text(json.dumps({'results': rows}, indent=2,
                                  ensure_ascii=False), encoding='utf-8')
    for row in rows:
        print(row)
    print('Saved:', outfile)
    return rows


if __name__ == '__main__':
    main()
