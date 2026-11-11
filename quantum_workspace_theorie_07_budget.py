#!/usr/bin/env python3
"""QWX Theory 07: budgeted observations triggered by cheap MPS diagnostics.

All controllers see only operations ALREADY executed. Synthetic circuits, not
quantum hardware; this experimental policy is not a new physics discovery.
The bond utilization and discarded weight below are numerical diagnostics,
NOT entanglement measurements on a generally noncanonical MPS.
"""
from __future__ import annotations
import argparse
import json
import statistics
import time
from pathlib import Path
import numpy as np
import quantum_workspace_theorie_04_predictive_mps as q4
import quantum_workspace_theorie_05_history_mps as q5
import quantum_workspace_theorie_06_observation_selective as q6


def seeded_batches(n: int, repeats: int, scenario: str, seed: int):
    """Independent layout seeds, even for persistent and switching scenarios."""
    original = q5.create_microbatches(n=n, repeats=repeats, scenario=scenario, seed=seed)
    perm = np.random.default_rng(seed + 7847).permutation(n)
    result = []
    for batch in original:
        remapped = []
        for gate in batch:
            if gate[0] == 'zz':
                remapped.append(('zz', int(perm[gate[1]]), int(perm[gate[2]]), float(gate[3])))
            else:
                remapped.append(('ry', int(perm[gate[1]]), float(gate[2])))
        result.append(remapped)
    return result


def bond_pressure(mps, discarded_since_last: float, trunc_eps: float = 1e-12):
    """Cheap telemetry: tensor shapes and already accumulated truncation loss."""
    bonds = [int(t.shape[2]) for t in mps.tensors[:-1]]
    utilisation = max(bonds, default=1) / max(1, mps.chi)
    return {'max_bond': max(bonds, default=1),
            'utilisation': float(utilisation),
            'discarded_increment': float(max(0., discarded_since_last)),
            'pressure': float(max(utilisation, min(1., discarded_since_last / max(1e-20, trunc_eps))))}


def start_mps(n, chi):
    mps = q4.MPS(n=n, chi=chi, svd_tol=1e-13)
    for k in range(n):
        mps.apply_one(k, q4.H)
    return mps


def run_budgeted(batches, n=8, chi=16, budget=2, period=3,
                 utilisation_trigger=.8, discard_trigger=1e-10, penalty=1.0):
    """Decide before each batch, using only earlier interactions and measurements.

    Stable history: use cheap history routing. After a changed regime, measure
    at most budget previous-interaction correlations if earlier MPS diagnostics
    signal risk, and consider these observations only for the next batch.
    All observation and reconfiguration time is included in wall clock cost.
    """
    begin = time.perf_counter()
    mps = start_mps(n, chi)
    previous_pairs = None
    penultimate_pairs = None
    cached_pairs = {}
    last_probe = -period
    measurements = 0
    probe_count = 0
    measurement_time = 0.
    decision_time = 0.
    changes = 0
    history = []
    for step, batch in enumerate(batches):
        tick = time.perf_counter()
        stable = (previous_pairs is not None and penultimate_pairs is not None and
                  q6.normalized_edges(previous_pairs) == q6.normalized_edges(penultimate_pairs))
        if stable:
            target = q4.choose_target(mps.order, previous_pairs, threshold=1.0)
        elif cached_pairs and previous_pairs is not None:
            target = q6.propose_target(mps.order, previous_pairs, cached_pairs,
                                       min_mi=.015, penalty=penalty)
        else:
            target = tuple(mps.order)
        decision_time += time.perf_counter() - tick
        if tuple(target) != tuple(mps.order):
            changes += 1
        mps.reorder(target)
        discard_before = mps.discarded_weight_proxy
        for gate in batch:
            if gate[0] == 'zz':
                mps.apply_nonlocal(gate[1], gate[2], q4.zz(gate[3]))
            else:
                mps.apply_one(gate[1], q4.ry(gate[2]))
        new_pairs = q4.pairs_in_batch(batch)
        pressure = bond_pressure(mps, mps.discarded_weight_proxy-discard_before)
        changed = (previous_pairs is not None and
                   q6.normalized_edges(new_pairs) != q6.normalized_edges(previous_pairs))
        risk = bool(pressure['utilisation'] >= utilisation_trigger or
                    pressure['discarded_increment'] >= discard_trigger)
        probed = False
        # Observation happens strictly AFTER executing this batch.
        if changed and risk and step-last_probe >= period:
            pairs = q6.select_probe_pairs(new_pairs, n, max_pairs=budget)
            tick = time.perf_counter()
            cached_pairs = {pair: q6.pair_mi(mps, *pair) for pair in pairs}
            measurement_time += time.perf_counter()-tick
            probe_count += 1
            measurements += len(pairs)
            last_probe = step
            probed = True
        elif not changed:
            cached_pairs = {}
        history.append({'step': step, 'order_before_next': list(mps.order),
                        'stable_prior': stable, 'changed_after_batch': changed,
                        'probed_after_batch': probed, 'pressure': pressure,
                        'swaps_cumulative': mps.swaps})
        penultimate_pairs, previous_pairs = previous_pairs, new_pairs
    elapsed = time.perf_counter()-begin
    row = {'policy': 'budgeted', 'swaps': mps.swaps,
           'layout_swaps': mps.layout_swaps, 'route_swaps': mps.route_swaps,
           'svd_calls': mps.svd_calls,
           'peak_coefficients': mps.peak_tensor_coefficients,
           'peak_svd_input': mps.peak_svd_input_coefficients,
           'discarded_weight_proxy': mps.discarded_weight_proxy,
           'elapsed_seconds': elapsed, 'mi_measure_seconds': measurement_time,
           'decision_seconds': decision_time, 'reorder_events': changes,
           'probe_events': probe_count, 'pair_probes': measurements,
           'probe_budget': budget, 'trace': history}
    return row, mps


def benchmark(n=8, chi=16, repeats=3, seeds=(17, 23, 29),
              scenarios=('persistent', 'switching', 'random'), budget=2):
    all_rows = []
    for scenario in scenarios:
        for seed in seeds:
            batches = seeded_batches(n, repeats, scenario, seed)
            reference = q5.exact_state(n, batches)
            cases = []
            for p in ('fixed', 'history', 'history_confident'):
                r, m = q5.run_policy(p, batches, n=n, chi=chi)
                if reference is not None:
                    r['fidelity'] = q6.fidelity(m.state_for_validation(), reference)
                else:
                    r['fidelity'] = None
                cases.append(r)
            r, m = run_budgeted(batches, n=n, chi=chi, budget=budget)
            r['fidelity'] = (q6.fidelity(m.state_for_validation(), reference)
                             if reference is not None else None)
            cases.append(r)
            all_rows.append({'scenario': scenario, 'seed': seed, 'strategies': cases})
    return {'name': 'Quantum Workspace X Theory 07 - budgeted observation',
            'n': n, 'chi': chi, 'repeats': repeats, 'seeds': list(seeds),
            'scenarios': list(scenarios), 'budget': budget,
            'notes': ['No future access; independent seeded qubit permutations',
                      'SVD pressure = bond dimension + discarded weight, not entanglement',
                      'Wall clock is noisy; coefficient counts are not actual RAM',
                      'Exact fidelity only for n<=10; synthetic circuits only.'],
            'results': all_rows}


def summaries(data):
    result = []
    for scenario in data['scenarios']:
        for strategy in ('fixed', 'history', 'history_confident', 'budgeted'):
            rows = [next(x for x in c['strategies'] if x['policy'] == strategy)
                    for c in data['results'] if c['scenario'] == scenario]
            result.append({'scenario': scenario, 'policy': strategy,
                           'median_wall_ms': 1000*statistics.median(x['elapsed_seconds'] for x in rows),
                           'mean_swaps': statistics.mean(x['swaps'] for x in rows),
                           'mean_probes': statistics.mean(x.get('pair_probes', 0) for x in rows),
                           'mean_peak_mps_coefficients': statistics.mean(x['peak_coefficients'] for x in rows),
                           'worst_fidelity': min((x['fidelity'] for x in rows
                                                  if x['fidelity'] is not None), default=None)})
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--n', type=int, default=8)
    p.add_argument('--chi', type=int, default=16)
    p.add_argument('--repeats', type=int, default=3)
    p.add_argument('--seeds', type=int, nargs='+', default=[17, 23, 29])
    p.add_argument('--budget', type=int, default=2)
    opt = p.parse_args()
    if opt.n < 4 or opt.n > 16 or opt.n % 2 or opt.chi < 1 or opt.budget < 1 or opt.repeats < 1:
        p.error('n even 4..16, chi, budget and repeats positive')
    data = benchmark(n=opt.n, chi=opt.chi, repeats=opt.repeats,
                     seeds=tuple(opt.seeds), budget=opt.budget)
    data['summary'] = summaries(data)
    dst = Path(__file__).with_name(f'quantum_workspace_resultats_07_n{opt.n}.json')
    dst.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    for row in data['summary']:
        print(f"{row['scenario']:<11} {row['policy']:<18} "
              f"SWAP={row['mean_swaps']:6.1f} median={row['median_wall_ms']:8.2f}ms "
              f"probe={row['mean_probes']:5.1f} fidelity={row['worst_fidelity']}")
    print('Saved:', dst)
    return data


if __name__ == '__main__':
    main()
