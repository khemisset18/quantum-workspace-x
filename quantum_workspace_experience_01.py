"""Quantum Workspace X — Expérience 01 : influence de l'ordre des qubits.

Démonstration reproductible (pas une nouvelle découverte scientifique).
8 qubits contenant 4 paires de Bell : (0,4), (1,5), (2,6), (3,7).
Compare le rang de Schmidt à chaque coupure dans deux ordres de représentation.

Exécution : python quantum_workspace_experience_01.py
Dépendance : numpy
"""
import numpy as np

N = 8
etat = np.zeros((2,) * N, dtype=float)
for valeur in range(16):
    bits = [(valeur >> (3 - index)) & 1 for index in range(4)]
    etat[tuple(bits + bits)] = 0.25  # 16 amplitudes de 1/4 : norme = 1


def rangs_de_schmidt(ordre):
    """Rangs exacts pour chaque coupure d'une chaîne MPS virtuelle."""
    resultat = []
    reordonne = np.transpose(etat, axes=ordre)
    for coupure in range(1, N):
        matrice = reordonne.reshape(2**coupure, 2**(N-coupure))
        valeurs = np.linalg.svd(matrice, compute_uv=False)
        rang = int(np.sum(valeurs > 1e-10))
        probabilites = valeurs**2
        entropie = float(-np.sum(probabilites[probabilites > 1e-12] *
                                 np.log2(probabilites[probabilites > 1e-12])))
        resultat.append((coupure, rang, entropie))
    return resultat


def main():
    ordre_simple = list(range(8))
    ordre_paires = [0, 4, 1, 5, 2, 6, 3, 7]
    simple = rangs_de_schmidt(ordre_simple)
    paires = rangs_de_schmidt(ordre_paires)
    print('Quantum Workspace X — Expérience 01')
    print('État : 4 paires intriquées, 8 qubits')
    print('Coupure | Rang ordre simple | Rang ordre par paires | Entropie simple | Entropie paires')
    for gauche, droite in zip(simple, paires):
        print(f'{gauche[0]:7d} | {gauche[1]:17d} | {droite[1]:21d} | '
              f'{gauche[2]:15.2f} | {droite[2]:14.2f}')
    print(f'Rang maximal : {max(x[1] for x in simple)} -> {max(x[1] for x in paires)}')
    print('Note : seule la représentation change. La physique reste identique.')
    print('Ce principe est déjà connu; il sert ici de banc d’essai initial.')


if __name__ == '__main__':
    main()