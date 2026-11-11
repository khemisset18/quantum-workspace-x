#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quantum Workspace X — Théorie 03 : topologies arborescentes inspirées de Fibonacci.

Compare, pour de petits états EXACTS, des arbres de tenseurs binaires :
- arbre équilibré, feuilles dans l'ordre naturel ;
- arbre à divisions de type Fibonacci / nombre d'or ;
- mêmes formes sur un ordre dérivé de l'information mutuelle ;
- arbre agglomératif construit avec l'information mutuelle ;
- contrôle aléatoire.

Mesures : rang de Schmidt à chaque arête et nombre formel de coefficients
complexes dans un réseau d'arbres exact (sans suppression des libertés de jauge).
Ni temps réel, ni RAM réelle, ni accélération quantique ne sont démontrés.
Une petite expérience dynamique compare une réorganisation 'retardée' à
un arbre figé et à un oracle calculant les corrélations de l'état courant.
Les calculs reposent toujours sur l'état complet (8 qubits) : pas d'échelle.

Exécution: python quantum_workspace_theorie_03_arbres.py
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import quantum_workspace_theorie_01 as q

OUT = Path(__file__).resolve().parent
SEED = 20261111
PHI = (1.0 + 5.0 ** 0.5) / 2.0
# A tuple (left, right) is an inner node; an integer is a leaf/qubit.


def leaves(tree):
    if isinstance(tree, (int, np.integer)):
        return (int(tree),)
    return leaves(tree[0]) + leaves(tree[1])


def balanced(order):
    order = tuple(int(i) for i in order)
    if len(order) == 1:
        return order[0]
    k = len(order) // 2
    return balanced(order[:k]), balanced(order[k:])


def fibonacci(order):
    """Division recursive n -> round(n/phi) + reste (heuristique explicite)."""
    order = tuple(int(i) for i in order)
    if len(order) == 1:
        return order[0]
    k = max(1, min(len(order)-1, round(len(order) / PHI)))
    return fibonacci(order[:k]), fibonacci(order[k:])


def mutual_tree(mi):
    """Fusion déterministe des sous-ensembles selon leur information mutuelle moyenne."""
    groups = [(i,) for i in range(len(mi))]
    trees = [i for i in range(len(mi))]
    while len(groups) > 1:
        options = []
        for a in range(len(groups)):
            for b in range(a+1, len(groups)):
                weight = float(np.mean([mi[i,j] for i in groups[a] for j in groups[b]]))
                options.append((-weight, tuple(sorted(groups[a]+groups[b])), a, b))
        _, _, a, b = min(options)
        combined = (trees[a], trees[b])
        group = tuple(sorted(groups[a] + groups[b]))
        for idx in sorted((a,b), reverse=True):
            del groups[idx]
            del trees[idx]
        groups.append(group)
        trees.append(combined)
    return trees[0]


def valid_tree(tree, n):
    return sorted(leaves(tree)) == list(range(n)) and len(leaves(tree)) == n


def measure_tree(psi, tree, threshold=1e-10):
    """TTN exacte : rangs des bipartitions et taille formelle des tenseurs.

    Le nombre de coefficients formels est une mesure du STOCKAGE TTN théorique
    sans jauge, et non pas la RAM effective du programme. Exact à tolérance
    de rang fixée, pas une compression physique de la fonction d'onde.
    """
    n = int(round(np.log2(psi.size)))
    assert psi.size == (1 << n) and valid_tree(tree, n)
    tensor = psi.reshape((2,) * n)
    rank_cache = {}

    def rank(node):
        group = tuple(sorted(leaves(node)))
        if len(group) == n:
            return 1
        if group not in rank_cache:
            rest = tuple(i for i in range(n) if i not in group)
            mat = tensor.transpose(group + rest).reshape(2**len(group), -1)
            singular = np.linalg.svd(mat, compute_uv=False)
            rank_cache[group] = int(np.count_nonzero(singular > threshold * singular[0]))
        return rank_cache[group]

    def walk(node, root=False):
        if isinstance(node, (int, np.integer)):
            return 2 * rank(node)
        a, b = node
        local = rank(a) * rank(b) * (1 if root else rank(node))
        return int(local + walk(a) + walk(b))

    cost = walk(tree, root=True)
    return {"coefficients": int(cost),
            "liaison_max": int(max(rank_cache.values(), default=1)),
            "nombre_coupures": len(rank_cache)}


def evaluate_static():
    rng = np.random.default_rng(SEED)
    states = q.make_cases()
    results = []
    for name, psi in states.items():
        mi = q.mutual_information_map(psi)
        directed = mutual_tree(mi)
        order = leaves(directed)
        designs = {
            "equilibre_naturel": balanced(range(q.N)),
            "fibonacci_naturel": fibonacci(range(q.N)),
            "equilibre_correle": balanced(order),
            "fibonacci_correle": fibonacci(order),
            "fusion_intrication": directed,
        }
        metrics = {k: measure_tree(psi, t) for k,t in designs.items()}
        random_costs = [measure_tree(psi, balanced(tuple(rng.permutation(q.N))))["coefficients"] for _ in range(24)]
        results.append({"etat":name,"ordre_guide":order,"mesures":metrics,
                        "controle_aleatoire_mediane":float(np.median(random_costs)),
                        "controle_aleatoire_min":min(random_costs),
                        "controle_aleatoire_max":max(random_costs)})
    return results


def alternate_bell_state(pairs, n=8):
    """Produit de paires Bell ; matching des feuilles distinct."""
    state = np.zeros(2**n, dtype=np.complex128)
    for bits in range(2**len(pairs)):
        assignment = [0]*n
        for k, (a,b) in enumerate(pairs):
            assignment[a] = assignment[b] = (bits >> k) & 1
        index = sum(bit << (n-1-i) for i,bit in enumerate(assignment))
        state[index] = 2**(-len(pairs)/2)
    return state


def evaluate_dynamic():
    pair_A = ((0,4),(1,5),(2,6),(3,7))
    pair_B = ((0,1),(2,3),(4,5),(6,7))
    left, right = alternate_bell_state(pair_A), alternate_bell_state(pair_B)
    base = balanced(range(8))
    times = np.linspace(0.0, 1.0, 13)
    static_tree = mutual_tree(q.mutual_information_map(left))
    previous_mi = None
    steps = []
    for t in times:
        psi = q.normed((1-t)*left + t*right)
        current_mi = q.mutual_information_map(psi)
        actual = mutual_tree(current_mi)
        # Une étape de retard, PAS une véritable prédiction à l'avance.
        lag_tree = mutual_tree(previous_mi) if previous_mi is not None else static_tree
        row = {"t":round(float(t),6),
               "arbre_equilibre":measure_tree(psi,base)["coefficients"],
               "arbre_fixe":measure_tree(psi,static_tree)["coefficients"],
               "arbre_retarde":measure_tree(psi,lag_tree)["coefficients"],
               "arbre_oracle":measure_tree(psi,actual)["coefficients"]}
        steps.append(row)
        previous_mi = current_mi
    return steps


def main():
    static = evaluate_static()
    dynamic = evaluate_dynamic()
    results = {"titre":"Quantum Workspace X — Théorie 03 : arbres hiérarchiques",
               "statut":"expérience exploratoire, pas de découverte prouvée",
               "qubits":q.N,"graine":SEED,
               "metriques":"rangs de Schmidt et coefficients formels exacts (pas RAM / latence)",
               "fibonacci":"division récursive round(n/phi), sans prétention d'optimalité",
               "statique":static,"dynamique":dynamic}
    (OUT / 'quantum_workspace_resultats_03.json').write_text(json.dumps(results,indent=2,ensure_ascii=False),encoding='utf-8')
    print('THÉORIE 03 — arbres hiérarchiques, n=8')
    for r in static:
        print(r['etat'], ' | '.join(f'{name}={m["coefficients"]}' for name,m in r['mesures'].items()))
    print('DYNAMIQUE (moyennes de coefficients):')
    for key in ('arbre_equilibre','arbre_fixe','arbre_retarde','arbre_oracle'):
        print(key, round(float(np.mean([step[key] for step in dynamic])),2))
    return results


if __name__ == '__main__':
    main()
