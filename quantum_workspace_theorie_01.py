#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quantum Workspace X — Théorie 01 : cartographier l'intrication.

Hypothèse testée : rapprocher dans une représentation MPS les qubits fortement
corrélés peut réduire la dimension de liaison nécessaire à fidélité donnée.

Méthode :
  * construit 4 états de 8 qubits (paires de Bell, GHZ, Ising 1D, état aléatoire)
  * calcule la carte d'information mutuelle quantique I(i:j)
  * cherche le meilleur ordre pour le coût somme I(i:j) * distance(i,j)
  * calcule les rangs de Schmidt exacts et la fidélité d'une approximation MPS
  * compare ordre initial vs ordre choisi par l'algorithme
  * écrit résultats JSON et 2 figures si matplotlib est installé.

IMPORTANT : l'optimisation par information mutuelle est une méthode connue,
notamment en DMRG. Ce programme est un banc d'essai, PAS une découverte.

Installation : python -m pip install numpy scipy matplotlib
Exécution :   python quantum_workspace_theorie_01.py
"""

from __future__ import annotations
import itertools
import json
from pathlib import Path

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import eigsh

N = 8
SEED = 2026
TARGET_FIDELITY = 0.9999
OUT = Path(__file__).resolve().parent


def normed(a: np.ndarray) -> np.ndarray:
    a = np.asarray(a, dtype=np.complex128)
    return a / np.linalg.norm(a)


def bell_pairs(n: int = N) -> np.ndarray:
    """Paires intriquées : (0,4), (1,5), (2,6), (3,7)."""
    result = np.zeros((2,) * n, dtype=np.complex128)
    for v in range(16):
        bits = [(v >> (3 - i)) & 1 for i in range(4)]
        result[tuple(bits + bits)] = 0.25
    return result.reshape(-1)


def ghz(n: int = N) -> np.ndarray:
    result = np.zeros(2**n, dtype=np.complex128)
    result[0] = result[-1] = 1 / np.sqrt(2)
    return result


def ising_ground(n: int = N, h: float = 1.0) -> np.ndarray:
    """État fondamental de H = -sum Z_i Z_(i+1) - h sum X_i, bords ouverts."""
    size = 2**n
    rows, cols, vals = [], [], []
    for basis in range(size):
        spins = [(basis >> (n - 1 - i)) & 1 for i in range(n)]
        energy = -sum(1 if spins[i] == spins[i+1] else -1 for i in range(n-1))
        rows.append(basis); cols.append(basis); vals.append(float(energy))
        for i in range(n):
            rows.append(basis); cols.append(basis ^ (1 << (n-1-i))); vals.append(-h)
    hamiltonian = coo_matrix((vals, (rows, cols)), shape=(size, size)).tocsr()
    eigvals, eigvecs = eigsh(hamiltonian, k=1, which='SA', tol=1e-12)
    psi = normed(eigvecs[:, 0])
    return psi


def reorder_state(psi: np.ndarray, order: tuple[int, ...] | list[int]) -> np.ndarray:
    n = int(round(np.log2(psi.size)))
    return psi.reshape((2,) * n).transpose(order).reshape(-1)


def reduced_density(psi: np.ndarray, keep: tuple[int, ...]) -> np.ndarray:
    n = int(round(np.log2(psi.size)))
    other = tuple(i for i in range(n) if i not in keep)
    matrix = psi.reshape((2,) * n).transpose(keep + other).reshape(2**len(keep), -1)
    return matrix @ matrix.conj().T


def entropy_bits(rho: np.ndarray) -> float:
    eigvals = np.linalg.eigvalsh(rho)
    eigvals = eigvals[eigvals > 1e-13]
    return float(-np.dot(eigvals, np.log2(eigvals)))


def mutual_information_map(psi: np.ndarray) -> np.ndarray:
    n = int(round(np.log2(psi.size)))
    single_entropy = [entropy_bits(reduced_density(psi, (i,))) for i in range(n)]
    mi = np.zeros((n,n), dtype=float)
    for i in range(n):
        for j in range(i+1, n):
            two_entropy = entropy_bits(reduced_density(psi, (i,j)))
            mi[i,j] = mi[j,i] = max(0.0, single_entropy[i] + single_entropy[j] - two_entropy)
    return mi


def ordering_cost(order: tuple[int, ...], mi: np.ndarray) -> float:
    pos = [0] * len(order)
    for p, qubit in enumerate(order):
        pos[qubit] = p
    return float(sum(mi[i,j] * abs(pos[i]-pos[j])
                     for i in range(len(order)) for j in range(i+1,len(order))))


def best_order_exact(mi: np.ndarray) -> tuple[int, ...]:
    """Recherche exhaustive : praticable ici UNIQUEMENT parce que n=8."""
    n = len(mi)
    best = tuple(range(n))
    score = ordering_cost(best, mi)
    # Renverser une chaîne ne change pas le coût : on ne garde qu'un sens.
    for candidate in itertools.permutations(range(n)):
        if candidate[0] > candidate[-1]:
            continue
        s = ordering_cost(candidate, mi)
        if s < score - 1e-11:
            best, score = candidate, s
    return best


def schmidt_ranks(psi: np.ndarray, order: tuple[int, ...]) -> list[int]:
    state = reorder_state(psi, order)
    n = len(order)
    result = []
    for left in range(1,n):
        singular = np.linalg.svd(state.reshape(2**left,2**(n-left)),compute_uv=False)
        result.append(int(np.count_nonzero(singular > 1e-10)))
    return result


def approximate_mps(psi: np.ndarray, order: tuple[int, ...], max_bond: int):
    """SVD successives et reconstruction exacte de l'approximation (petit n)."""
    n = len(order)
    state = reorder_state(psi, order)
    remainder = state.reshape(1, -1)
    tensors = []
    left_dim = 1
    for site in range(n - 1):
        remainder = remainder.reshape(left_dim * 2, -1)
        u, s, vh = np.linalg.svd(remainder, full_matrices=False)
        bond = min(max_bond, len(s))
        tensors.append(u[:, :bond].reshape(left_dim, 2, bond))
        remainder = s[:bond, None] * vh[:bond, :]
        left_dim = bond
    tensors.append(remainder.reshape(left_dim, 2, 1))
    v = tensors[0]
    for t in tensors[1:]:
        v = np.tensordot(v, t, axes=([-1],[0]))
    reconstructed = v.reshape(-1)
    rec_norm = np.linalg.norm(reconstructed)
    if rec_norm == 0:
        return 0.0, 0
    fidelity = float(abs(np.vdot(state, reconstructed / rec_norm)) ** 2)
    params = int(sum(t.size for t in tensors))
    return min(1.0, fidelity), params


def required_bond(psi: np.ndarray, order: tuple[int, ...], target: float):
    max_candidate = 2 ** (len(order) // 2)
    for d in range(1, max_candidate + 1):
        fidelity, params = approximate_mps(psi, order, d)
        if fidelity + 1e-12 >= target:
            return d, fidelity, params
    raise RuntimeError('Fidélité cible impossible pour cet état')


def make_cases():
    rng = np.random.default_rng(SEED)
    random_psi = normed(rng.standard_normal(2**N) + 1j*rng.standard_normal(2**N))
    # Rend les voisins physiques du modèle d'Ising éloignés dans l'ordre initial.
    scrambling = (0,4,1,5,2,6,3,7)
    scrambled_ising = reorder_state(ising_ground(), scrambling)
    return {
        'Paires de Bell': bell_pairs(),
        'GHZ': ghz(),
        'Ising 1D (ordre brouillé)': scrambled_ising,
        'État aléatoire': random_psi,
    }


def main():
    records = []
    all_mi = {}
    print('Quantum Workspace X — PREMIÈRE THÉORIE : CARTE D’INTRICATION')
    print(f'{N} qubits | fidélité >= {TARGET_FIDELITY:.4%} | graine = {SEED}\n')
    for name, psi in make_cases().items():
        mi = mutual_information_map(psi)
        normal = tuple(range(N))
        better = best_order_exact(mi)
        raw = schmidt_ranks(psi, normal)
        optimized = schmidt_ranks(psi, better)
        d0, f0, p0 = required_bond(psi, normal, TARGET_FIDELITY)
        d1, f1, p1 = required_bond(psi, better, TARGET_FIDELITY)
        record = {
            'etat': name,
            'ordre_initial': normal,
            'ordre_optimise': better,
            'cout_intrication_initial': ordering_cost(normal, mi),
            'cout_intrication_optimise': ordering_cost(better, mi),
            'rang_exact_max_initial': max(raw),
            'rang_exact_max_optimise': max(optimized),
            'dimensions_MPS_initial': d0,
            'dimensions_MPS_optimise': d1,
            'fidelite_initiale': f0,
            'fidelite_optimisee': f1,
            'parametres_MPS_initiaux': p0,
            'parametres_MPS_optimises': p1,
        }
        records.append(record)
        all_mi[name] = mi
        print(f"{name}: ordre {normal} -> {better}")
        print(f"  rang max exact : {max(raw)} -> {max(optimized)}")
        print(f"  liaison MPS pour fidélité >= {TARGET_FIDELITY:.4%}: {d0} -> {d1}")
        print(f"  paramètres MPS : {p0} -> {p1}; fidélités {f0:.7f}, {f1:.7f}\n")
        # Vérifications pour ne pas afficher une amélioration artificielle.
        assert abs(np.vdot(psi, psi).real - 1.0) < 1e-10
        assert record['cout_intrication_optimise'] <= record['cout_intrication_initial'] + 1e-9
        assert f0 >= TARGET_FIDELITY - 1e-10 and f1 >= TARGET_FIDELITY - 1e-10
        assert (p0 > 0) and (p1 > 0)
    data = {
        'nom': 'Quantum Workspace X - expérience n° 02',
        'statut': 'Preuve de concept éducative; techniques connues',
        'qubits': N,
        'graine': SEED,
        'fidelite_cible': TARGET_FIDELITY,
        'precision': 'complex128',
        'methode_optimisation': 'minimisation exhaustive somme I(i:j) fois distance dans la chaîne, n=8',
        'resultats': records,
    }
    json_path = OUT / 'quantum_workspace_resultats_02.json'
    json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
    print('Résultats écrits dans :', json_path)
    try:
        import matplotlib.pyplot as plt
        names = [r['etat'] for r in records]
        x = np.arange(len(names))
        fig, ax = plt.subplots(figsize=(10,5.1))
        w = .35
        ax.bar(x-w/2,[r['dimensions_MPS_initial'] for r in records],w,label='Ordre initial')
        ax.bar(x+w/2,[r['dimensions_MPS_optimise'] for r in records],w,label='Ordre optimisé')
        ax.set_xticks(x, names, rotation=12, ha='right')
        ax.set_ylabel('Dimension maximale de liaison nécessaire')
        ax.set_title('MPS à fidélité ≥ 99,99 % — 8 qubits')
        ax.legend()
        ax.set_ylim(0,17)
        fig.tight_layout()
        fig.savefig(OUT/'quantum_workspace_comparaison_02.png', dpi=175)
        plt.close(fig)
        fig, ax = plt.subplots(figsize=(6,5.2))
        im = ax.imshow(all_mi['Ising 1D (ordre brouillé)'], cmap='viridis')
        ax.set_title('Information mutuelle quantique — Ising 1D brouillé')
        ax.set_xlabel('Qubit'); ax.set_ylabel('Qubit')
        ax.set_xticks(range(N)); ax.set_yticks(range(N))
        fig.colorbar(im,ax=ax,label='Information mutuelle (bits)')
        fig.tight_layout()
        fig.savefig(OUT/'quantum_workspace_carte_intrication_02.png',dpi=175)
        plt.close(fig)
        print('Graphiques créés dans :', OUT)
    except ImportError:
        print('matplotlib absent : graphiques non générés')
    return records


if __name__ == '__main__':
    main()