#!/usr/bin/env python3
"""Causal tests, probe budgets and numerical fidelity for Theory 07."""
import numpy as np
import quantum_workspace_theorie_07_budget as q7
import quantum_workspace_theorie_05_history_mps as q5
import quantum_workspace_theorie_06_observation_selective as q6


def main():
    for scenario in ('persistent', 'switching', 'random'):
        a = q7.seeded_batches(8, 3, scenario, 17)
        b = q7.seeded_batches(8, 3, scenario, 23)
        assert a != b, scenario
        row, engine = q7.run_budgeted(a, n=8, chi=16, budget=2)
        ref = q5.exact_state(8, a)
        assert q6.fidelity(engine.state_for_validation(), ref) > 1-1e-10
        assert row['pair_probes'] <= 2*row['probe_events']
        assert row['swaps'] == row['layout_swaps']+row['route_swaps']
        assert row['mi_measure_seconds'] <= row['elapsed_seconds']
        assert all(0 <= x['pressure']['utilisation'] <= 1 for x in row['trace'])

    # Identical prefix must lead to identical actions regardless of future.
    prefix = q7.seeded_batches(8, 3, 'persistent', 17)[:4]
    future_a = q7.seeded_batches(8, 3, 'persistent', 17)[4:]
    future_b = q7.seeded_batches(8, 3, 'random', 29)[4:]
    a, _ = q7.run_budgeted(prefix+future_a, n=8, chi=16, budget=2)
    b, _ = q7.run_budgeted(prefix+future_b, n=8, chi=16, budget=2)
    assert a['trace'][:len(prefix)] == b['trace'][:len(prefix)]

    cases = q7.seeded_batches(10, 3, 'switching', 31)
    row, mps = q7.run_budgeted(cases, n=10, chi=32, budget=2)
    assert q6.fidelity(mps.state_for_validation(), q5.exact_state(10, cases)) > 1-1e-10

    result = q7.benchmark(n=8, chi=16, repeats=2, seeds=(17, 23), budget=2)
    assert len(result['results']) == 6
    assert {r['policy'] for r in result['results'][0]['strategies']} == {
        'fixed', 'history', 'history_confident', 'budgeted'}
    assert len(q7.summaries(result)) == 12
    assert all(r['fidelity'] > 1-1e-10
               for row in result['results'] for r in row['strategies'])
    print('Theory 07 tests: causal routing, budget, numerical accuracy — OK')


if __name__ == '__main__':
    main()
