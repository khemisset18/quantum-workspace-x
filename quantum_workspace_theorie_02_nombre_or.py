#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quantum Workspace X — Expérience exploratoire sur le nombre d'or.

Hypothèse : un ordre fixe inspiré de l'angle d'or réduirait la dimension MPS
à précision donnée. On le compare à l'ordre initial, à un contrôle aléatoire
et, sur les quatre cas de référence, à l'optimisation par information mutuelle.

Attention : ce n'est PAS un calculateur quantique, un modèle de pyramide, ni
une preuve d'effet universel du nombre d'or. Les états complets sont toujours
stockés pour servir de référence (8 qubits seulement).
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import quantum_workspace_theorie_01 as q

PHI = (1 + 5**0.5) / 2
SEED = 20261111
OUT = Path(__file__).resolve().parent


def golden_angle_order(n: int) -> tuple[int, ...]:
    """Ordonne les indices par la partie fractionnaire de i/phi.

    C'est un choix QUASI-PERIODIQUE mathématiquement défini, pas une loi physique.
    """
    return tuple(sorted(range(n), key=lambda i: ((i / PHI) % 1.0, i)))


def evaluate(psi: np.ndarray, order: tuple[int, ...]) -> dict:
    d, fidelity, parameters = q.required_bond(psi, order, q.TARGET_FIDELITY)
    return {"bond": d, "parameters": parameters, "fidelity": float(fidelity)}


def main() -> dict:
    n = q.N
    identity = tuple(range(n))
    golden = golden_angle_order(n)
    records = []
    for name, psi in q.make_cases().items():
        mi = q.mutual_information_map(psi)
        learned = q.best_order_exact(mi)
        records.append({"state": name, "identity": evaluate(psi, identity),
                        "golden": evaluate(psi, golden),
                        "mutual_information": evaluate(psi, learned)})

    # Test hors échantillon : pour chaque champ, 12 permutations aléatoires
    # indépendantes du rapport d'or; les performances de 3 ordres sont comparées.
    rng = np.random.default_rng(SEED)
    trials = []
    for field in (0.5, 1.0, 1.5):
        state = q.ising_ground(n=n, h=field)
        for _ in range(12):
            scramble = tuple(map(int, rng.permutation(n)))
            psi = q.reorder_state(state, scramble)
            random_order = tuple(map(int, rng.permutation(n)))
            trials.append({"field": field, "scramble": scramble,
                           "identity": evaluate(psi, identity),
                           "golden": evaluate(psi, golden),
                           "random": evaluate(psi, random_order)})

    def outcome(key: str) -> dict:
        better = sum(t["golden"]["parameters"] < t[key]["parameters"] for t in trials)
        same = sum(t["golden"]["parameters"] == t[key]["parameters"] for t in trials)
        worse = len(trials) - better - same
        return {"golden_better": better, "tie": same, "golden_worse": worse,
                "mean_parameters_golden": float(np.mean([t["golden"]["parameters"] for t in trials])),
                "mean_parameters_reference": float(np.mean([t[key]["parameters"] for t in trials]))}

    data = {"experiment": "Theory 02 — golden angle exploratory baseline",
            "n_qubits": n, "phi": PHI, "golden_order": golden,
            "target_fidelity": q.TARGET_FIDELITY, "seed": SEED,
            "reference_cases": records, "ising_trials": trials,
            "summary_vs_identity": outcome("identity"),
            "summary_vs_random": outcome("random"),
            "caveat": "Ranks and MPS coefficient counts, not actual RAM/time. No universal advantage established."}
    (OUT / "quantum_workspace_resultats_nombre_or_02.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print("ORDRE D'OR (n=8):", golden)
    print("CAS DE REFERENCE, coefficients MPS (normal / or / corrélations):")
    for item in records:
        print(item["state"], *(item[k]["parameters"] for k in ("identity", "golden", "mutual_information")))
    print("36 TESTS ISING — NOMBRE D'OR vs ORDRE INITIAL:", data["summary_vs_identity"])
    print("36 TESTS ISING — NOMBRE D'OR vs ORDRE ALÉATOIRE:", data["summary_vs_random"])
    return data


if __name__ == "__main__":
    main()
