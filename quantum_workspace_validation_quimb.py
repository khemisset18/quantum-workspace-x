#!/usr/bin/env python3
"""Optional independent reference: quimb's established CircuitMPS backend.

Not part of the core numpy prototype; install with:
    python -m pip install -r requirements-reference.txt
    python quantum_workspace_validation_quimb.py

The reference implements *the same logical gates* in another library, with a
different MPS implementation. Only reconstruct dense states for n <= 8.
"""
from __future__ import annotations

import numpy as np
import quimb.tensor as qtn
import quantum_workspace_theorie_05_history_mps as q5
import quantum_workspace_theorie_07_budget as q7


def normalized_fidelity(a, b):
    return float(abs(np.vdot(a, b))**2 /
                 (np.vdot(a, a).real * np.vdot(b, b).real))


def independent_quimb_state(n, batches):
    if n > 8:
        raise ValueError('Dense validation restricted to n <= 8')
    circuit = qtn.CircuitMPS(n, max_bond=2**(n//2), cutoff=0.0)
    for qubit in range(n):
        circuit.apply_gate('H', qubit)
    for batch in batches:
        for gate in batch:
            if gate[0] == 'zz':
                # Our zz(theta) is exp(-i theta Z Z); quimb RZZ(phi) uses phi/2.
                circuit.apply_gate('RZZ', 2*gate[3], gate[1], gate[2])
            else:
                circuit.apply_gate('RY', gate[2], gate[1])
    return np.asarray(circuit.to_dense()).reshape(-1)


def main():
    for n in (6, 8):
        for scenario in ('persistent', 'random'):
            batches = q7.seeded_batches(n, 2, scenario, seed=37)
            quimb_state = independent_quimb_state(n, batches)
            exact = q5.exact_state(n, batches)
            assert normalized_fidelity(quimb_state, exact) > 1-1e-9
            row, mps = q7.run_budgeted(batches, n=n, chi=2**(n//2), budget=2)
            assert normalized_fidelity(quimb_state, mps.state_for_validation()) > 1-1e-9
            print(f'quimb reference OK: n={n}, {scenario}')
    print('Independent quimb cross-check passed.')


if __name__ == '__main__':
    main()
