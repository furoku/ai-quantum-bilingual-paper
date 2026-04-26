# Ancillary files for the arXiv submission

This directory contains reproducibility files for the paper:

**Quantum-Assisted Harnesses for Verifiable AI Iteration: Candidate Search via Amplitude Amplification and Annealing**

## Contents

- `quantum_agent_search_experiment.py`: self-contained CPU experiment script.
- `results.json`: frozen experiment output used in the paper.
- `grover_results.csv`: Grover/amplitude-amplification simulation table.
- `qubo_result.csv`: QUBO verifier and simulated annealing result.
- `quantum_annealing_results.csv`: small closed-system annealing result.
- `test_summary.json`: unit-test summary.

## Reproduction

```bash
python3 quantum_agent_search_experiment.py --out results --test
```

The script requires Python >= 3.10 plus NumPy, SciPy, and Matplotlib.

## Scope

These experiments are CPU simulations. They do not demonstrate quantum advantage on current quantum hardware.
