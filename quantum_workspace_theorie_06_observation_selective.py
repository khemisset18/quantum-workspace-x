#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quantum Workspace X — Théorie 06 : observation sélective de corrélations MPS.

Une expérience en aveugle : les politiques non-oracles ne peuvent consulter
les opérations à venir. Le diagnostic lit seulement un MPS déjà mis à jour,
et n'évalue qu'un budget restreint de paires après stabilisation du motif
historique. Les corrélations incluent les corrélations classiques.

Ce programme n'est ni un nouveau calculateur quantique, ni une preuve de gain
universel. On mesure aussi le surcoût réel des observations Python.
"""
from __future__ import annotations
import argparse
import json
import time
from pathlib import Path
import numpy as np
import quantum_workspace_theorie_04_predictive_mps as q4
import quantum_workspace_theorie_05_history_mps as q5


def normalized_edges(pairs):
    return frozenset(tuple(sorted((int(a), int(b)))) for a, b in pairs)


def pair_mi(mps, a, b):
    """Information mutuelle quantique I(a:b), via UNE densité 2-sites.

    Les indices a et b sont des étiquettes logiques, converties en positions
    courantes MPS. Cela ne reconstruit jamais le vecteur d'état dense.
    """
    i, j = sorted((mps.order.index(a), mps.order.index(b)))
    rho = q5.reduced_density_from_mps(mps, (i, j)).reshape(2, 2, 2, 2)
    rho_a = np.einsum('abcb->ac', rho, optimize=True)
    rho_b = np.einsum('abad->bd', rho, optimize=True)
    mi = q5.entropy(rho_a) + q5.entropy(rho_b) - q5.entropy(rho.reshape(4, 4))
    return float(np.clip(mi, 0.0, 2.0))


def select_probe_pairs(history_pairs, n, max_pairs=3):
    """Sélectionne uniquement des paires du passé, sans interactions futures."""
    seen = []
    for pair in history_pairs:
        e = tuple(sorted(pair))
        if e not in seen:
            seen.append(e)
    # Ajouter au besoin quelques paires locales de contrôle.
    for i in range(0, n-1, 2):
        p = (i, i + 1)
        if p not in seen:
            seen.append(p)
    return seen[:max_pairs]


def propose_target(order, previous_pairs, sampled, min_mi=.005, penalty=1.0):
    """Décision sur score de coûts de routage HISTORIQUES, avec filtre MI.

    On n'utilise pas l'information mutuelle pour deviner des paires futures.
    Le filtre MI refuse la réorganisation lorsqu'aucune corrélation significative
    n'a été observée dans les paires échantillonnées.
    """
    if not sampled or max(sampled.values()) < min_mi:
        return tuple(order)
    valid = [tuple(pair) for pair, mi in sorted(sampled.items(), key=lambda item: -item[1])
             if mi >= min_mi]
    busy = set()
    disjoint = []
    for a,b in valid:
        if a not in busy and b not in busy:
            disjoint.append((a,b))
            busy.update((a,b))
    if not disjoint:
        return tuple(order)
    candidate = q4.group_pairs(tuple(order), disjoint)
    old = q4.distance_cost(order, previous_pairs)
    new = q4.distance_cost(candidate, previous_pairs)
    swaps = q4.inversions_from_to(tuple(order), candidate)
    return candidate if old-new > penalty*swaps else tuple(order)


def run_selective(batches, n=8, chi=16, probe_budget=3,
                  probe_period=3, min_mi=.005, penalty=1.0):
    """Moteur sans regard sur les prochaines opérations.

    Chaque décision précède l'exécution du prochain lot. On n'observe les
    corrélations qu'après un lot traité, et seulement si l'historique montre
    au moins deux lots successifs avec le même jeu de paires.
    """
    start = time.perf_counter()
    mps = q4.MPS(n=n, chi=chi, svd_tol=1e-13)
    for k in range(n):
        mps.apply_one(k, q4.H)
    previous_pairs = None
    preceding_pairs = None
    sampled = {}
    last_probe = -1000
    active = False
    decisions = 0
    probe_events = 0
    pair_probes = 0
    probe_seconds = 0.0
    policy_seconds = 0.0
    history = []
    for step, batch in enumerate(batches):
        tick = time.perf_counter()
        stable = (previous_pairs is not None and preceding_pairs is not None and
                  normalized_edges(previous_pairs)==normalized_edges(preceding_pairs))
        target = (propose_target(mps.order, previous_pairs, sampled, min_mi, penalty)
                  if stable and active else tuple(mps.order))
        policy_seconds += time.perf_counter()-tick
        if target != tuple(mps.order):
            decisions += 1
        mps.reorder(target)
        # batch n'est lu que pour APPLIQUER le circuit, jamais pour DECIDER.
        for gate in batch:
            if gate[0] == 'zz':
                mps.apply_nonlocal(gate[1], gate[2], q4.zz(gate[3]))
            else:
                mps.apply_one(gate[1], q4.ry(gate[2]))
        latest_pairs = q4.pairs_in_batch(batch)
        now_stable = (previous_pairs is not None and
                      normalized_edges(previous_pairs)==normalized_edges(latest_pairs))
        # Observation après exécution : jamais avant.
        if now_stable and (not active or step-last_probe >= probe_period):
            t = time.perf_counter()
            pairs = select_probe_pairs(latest_pairs, n, max_pairs=probe_budget)
            sampled = {pair: pair_mi(mps, *pair) for pair in pairs}
            probe_seconds += time.perf_counter()-t
            pair_probes += len(pairs)
            probe_events += 1
            last_probe = step
            active = True
        elif not now_stable:
            # Ne pas faire confiance à une vieille carte lors d'un changement.
            sampled = {}
            active = False
        history.append({'step':step,'previous_was_stable':bool(stable),
                        'probed':bool(now_stable and last_probe==step),
                        'order':list(mps.order),
                        'swaps_so_far':mps.swaps})
        preceding_pairs, previous_pairs = previous_pairs, latest_pairs
    elapsed = time.perf_counter()-start
    return {'policy':'selective','swaps':mps.swaps,
            'layout_swaps':mps.layout_swaps,'route_swaps':mps.route_swaps,
            'svd_calls':mps.svd_calls,
            'peak_coefficients':mps.peak_tensor_coefficients,
            'peak_svd_input':mps.peak_svd_input_coefficients,
            'discarded_weight_proxy':mps.discarded_weight_proxy,
            'reorder_events':decisions, 'elapsed_seconds':elapsed,
            'mi_measure_seconds':probe_seconds,'decision_seconds':policy_seconds,
            'probe_events':probe_events,'pair_probes':pair_probes,
            'probe_budget':probe_budget,'history':history},mps


def fidelity(psi, exact):
    numerator = abs(np.vdot(psi, exact))**2
    return float(numerator/(np.vdot(psi,psi).real*np.vdot(exact,exact).real))


def benchmark(n=8, chi=16, repeats=4, seeds=(11,12,13),
              scenarios=('persistent','switching','random'), budget=3):
    results=[]
    for scenario in scenarios:
        for seed in seeds:
            batches = q5.create_microbatches(n=n, repeats=repeats,
                                            scenario=scenario, seed=seed)
            ref = q5.exact_state(n, batches)
            strategies=[]
            for key in ('fixed','history','history_confident','reactive'):
                row, engine = q5.run_policy(key,batches,n=n,chi=chi)
                if ref is not None:
                    row['fidelity'] = fidelity(engine.state_for_validation(), ref)
                strategies.append(row)
            row, engine = run_selective(batches,n=n,chi=chi,probe_budget=budget)
            if ref is not None:
                row['fidelity']=fidelity(engine.state_for_validation(), ref)
            strategies.append(row)
            results.append({'scenario':scenario,'seed':seed,'strategies':strategies})
    return {'name':'Quantum Workspace X Theory 06 - selective MI observation',
            'n':n,'chi':chi,'repeats':repeats,'budget':budget,
            'seeds':list(seeds),'scenarios':list(scenarios),
            'assumptions':'No next batch gate access; dense validation only n<=10; MI includes classical correlations',
            'measurement':'Pairwise MI contracts MPS; elapsed seconds includes measurement and routing, no isolated hardware benchmark.',
            'results':results}


def summary(report):
    grouped=[]
    for scenario in report['scenarios']:
        rows=[r for r in report['results'] if r['scenario']==scenario]
        policies=rows[0]['strategies']
        for i,p in enumerate(policies):
            runs=[row['strategies'][i] for row in rows]
            grouped.append({'scenario':scenario,'policy':p['policy'],
                            'mean_swaps':float(np.mean([x['swaps'] for x in runs])),
                            'mean_elapsed_seconds':float(np.mean([x['elapsed_seconds'] for x in runs])),
                            'mean_probe_seconds':float(np.mean([x.get('mi_measure_seconds',0.0) for x in runs])),
                            'mean_pair_probes':float(np.mean([x.get('pair_probes',0) for x in runs])),
                            'mean_fidelity':float(np.mean([x['fidelity'] for x in runs])) if runs[0].get('fidelity') is not None else None})
    return grouped


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--n',type=int,default=8)
    p.add_argument('--chi',type=int,default=16)
    p.add_argument('--repeats',type=int,default=4)
    p.add_argument('--seeds',type=int,nargs='+',default=[11,12,13])
    p.add_argument('--budget',type=int,default=3)
    a=p.parse_args()
    if a.n<4 or a.n%2 or a.n>16 or a.budget<1 or a.chi<1:
        p.error('n pair 4..16, budget et chi positifs')
    data=benchmark(n=a.n,chi=a.chi,repeats=a.repeats,seeds=tuple(a.seeds),budget=a.budget)
    data['summary']=summary(data)
    path=Path(__file__).resolve().parent/f'quantum_workspace_resultats_06_n{a.n}.json'
    path.write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf-8')
    print('THEORY 06: mean swaps, seconds, sampled pair MI, fidelity')
    for r in data['summary']:
        print(f"{r['scenario']:<11} {r['policy']:<20} {r['mean_swaps']:7.1f} "
              f"{r['mean_elapsed_seconds']:9.4f} {r['mean_pair_probes']:5.1f} {r['mean_fidelity']}")
    print('Saved',path)
    return data


if __name__=='__main__': main()
