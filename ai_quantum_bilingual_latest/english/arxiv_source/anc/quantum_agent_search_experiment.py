#!/usr/bin/env python3
"""
Computational experiments for the paper:
"AI iteration as verifiable candidate search with amplitude amplification and annealing".

This script is intentionally self-contained. It does not require a quantum SDK.
It provides:
  1. State-vector simulation of Grover/amplitude amplification on a verifier-defined success set.
  2. Classical random-retry baselines using the geometric distribution.
  3. A QUBO verifier for structured agent-trajectory constraints.
  4. A small closed-system adiabatic/quantum-annealing simulation on CPU.
  5. Unit tests for core correctness properties.

The experiments demonstrate scaling laws and feasibility of the *formulation*.
They do not claim quantum advantage on current hardware.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import random
import statistics
import unittest
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

import numpy as np

try:
    import matplotlib.pyplot as plt
except Exception:  # pragma: no cover
    plt = None

try:
    import scipy.sparse as sp
    import scipy.sparse.linalg as spla
except Exception:  # pragma: no cover
    sp = None
    spla = None


SEED = 20260425


@dataclass
class GroverResult:
    n_qubits: int
    n_candidates: int
    n_successes: int
    success_fraction: float
    classical_expected_queries: float
    classical_median_queries_mc: float
    classical_p95_queries_mc: float
    grover_iterations: int
    grover_success_probability: float
    quantum_expected_verifier_calls: float
    speedup_expected_queries: float
    analytic_success_probability: float


@dataclass
class QuboResult:
    n_bits: int
    n_candidates: int
    n_ground_states: int
    random_success_fraction: float
    random_expected_queries: float
    simulated_annealing_runs: int
    simulated_annealing_success_rate: float
    simulated_annealing_mean_best_energy: float
    simulated_annealing_median_steps_to_success: float | None


@dataclass
class QuantumAnnealingResult:
    n_bits: int
    n_candidates: int
    n_ground_states: int
    anneal_time: float
    n_time_steps: int
    ground_state_probability: float
    final_expected_energy: float
    norm_error: float


# ---------------------------------------------------------------------------
# Grover / amplitude amplification simulation
# ---------------------------------------------------------------------------

def optimal_grover_iterations(n_candidates: int, n_successes: int) -> int:
    """Return the standard near-optimal number of Grover iterations."""
    if n_successes <= 0 or n_successes > n_candidates:
        raise ValueError("n_successes must be in [1, n_candidates]")
    theta = math.asin(math.sqrt(n_successes / n_candidates))
    r = int(round(math.pi / (4 * theta) - 0.5))
    return max(0, r)


def analytic_grover_success(n_candidates: int, n_successes: int, iterations: int) -> float:
    """Analytic success probability after r Grover iterations."""
    theta = math.asin(math.sqrt(n_successes / n_candidates))
    return math.sin((2 * iterations + 1) * theta) ** 2


def grover_statevector_success(
    n_qubits: int,
    success_indices: Sequence[int],
    iterations: int,
) -> float:
    """Simulate Grover's algorithm by explicit state vector.

    success_indices define the verifier V(x)=1 success set.
    """
    n_candidates = 2**n_qubits
    state = np.ones(n_candidates, dtype=np.complex128) / math.sqrt(n_candidates)
    idx = np.array(list(success_indices), dtype=np.int64)
    for _ in range(iterations):
        # Oracle: phase-flip success states.
        state[idx] *= -1
        # Diffusion: reflection about the mean.
        mean_amp = np.mean(state)
        state = 2 * mean_amp - state
    prob = float(np.sum(np.abs(state[idx]) ** 2))
    return prob


def run_grover_scaling(
    n_values: Sequence[int] = (8, 10, 12, 14, 16),
    success_counts: Sequence[int] = (1, 4, 16),
    mc_trials: int = 20_000,
) -> List[GroverResult]:
    rng = np.random.default_rng(SEED)
    results: List[GroverResult] = []
    for n in n_values:
        n_candidates = 2**n
        for m in success_counts:
            if m >= n_candidates:
                continue
            # The actual indices are irrelevant to Grover dynamics, but we use a
            # random verifier success set to model unknown successful trajectories.
            success_indices = rng.choice(n_candidates, size=m, replace=False)
            r = optimal_grover_iterations(n_candidates, m)
            p_quantum = grover_statevector_success(n, success_indices, r)
            p_analytic = analytic_grover_success(n_candidates, m, r)
            p = m / n_candidates

            # Classical retry: geometric distribution with success probability p.
            classical_samples = rng.geometric(p, size=mc_trials)
            classical_expected = 1 / p
            classical_median = float(np.median(classical_samples))
            classical_p95 = float(np.percentile(classical_samples, 95))

            # Count verifier/oracle calls. Grover uses r oracle calls, and we add
            # one final verifier call to check the measured candidate.
            quantum_expected = (r + 1) / max(p_quantum, 1e-12)
            speedup = classical_expected / quantum_expected

            results.append(
                GroverResult(
                    n_qubits=n,
                    n_candidates=n_candidates,
                    n_successes=m,
                    success_fraction=p,
                    classical_expected_queries=classical_expected,
                    classical_median_queries_mc=classical_median,
                    classical_p95_queries_mc=classical_p95,
                    grover_iterations=r,
                    grover_success_probability=p_quantum,
                    quantum_expected_verifier_calls=quantum_expected,
                    speedup_expected_queries=speedup,
                    analytic_success_probability=p_analytic,
                )
            )
    return results


# ---------------------------------------------------------------------------
# QUBO verifier and simulated annealing baseline
# ---------------------------------------------------------------------------

def bits_from_int(x: int, n_bits: int) -> np.ndarray:
    return np.array([(x >> i) & 1 for i in range(n_bits)], dtype=np.int8)


def qubo_energy_18(bits: np.ndarray) -> float:
    """A toy QUBO-like energy for structured agent-trajectory constraints.

    Variables are interpreted as decisions in a candidate trajectory. Zero energy
    means every mechanical verifier constraint passes.

    Constraints:
      - bits 0..5 equal a fixed plan prefix.
      - bits 6..11 have exactly two selected tools/actions.
      - bits 12..17 have exactly three validation actions.
      - two pairwise consistency constraints couple plan and validation choices.

    This is quadratic because terms are of the form (linear expression)^2.
    """
    target = np.array([1, 0, 1, 1, 0, 0], dtype=np.int8)
    fixed = np.sum((bits[:6] - target) ** 2)
    group_a = (np.sum(bits[6:12]) - 2) ** 2
    group_b = (np.sum(bits[12:18]) - 3) ** 2
    consistency = (bits[6] - bits[12]) ** 2 + (bits[7] - bits[13]) ** 2
    return float(fixed + group_a + group_b + consistency)


def enumerate_qubo(n_bits: int = 18) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    n = 2**n_bits
    energies = np.zeros(n, dtype=np.float64)
    for i in range(n):
        energies[i] = qubo_energy_18(bits_from_int(i, n_bits))
    min_energy = float(np.min(energies))
    ground = np.where(energies == min_energy)[0]
    return energies, ground, energies[ground]


def simulated_annealing_qubo(
    n_bits: int = 18,
    runs: int = 500,
    steps: int = 1200,
    t_start: float = 4.0,
    t_end: float = 0.02,
) -> QuboResult:
    rng = random.Random(SEED)
    energies, ground, _ = enumerate_qubo(n_bits)
    ground_set = set(int(x) for x in ground)
    n_candidates = 2**n_bits
    successes = 0
    best_energies: List[float] = []
    steps_to_success: List[int] = []

    for _ in range(runs):
        x = rng.randrange(n_candidates)
        bits = bits_from_int(x, n_bits)
        e = qubo_energy_18(bits)
        best_e = e
        hit_step = None

        for step in range(steps):
            # Exponential temperature schedule.
            frac = step / max(1, steps - 1)
            temp = t_start * ((t_end / t_start) ** frac)
            j = rng.randrange(n_bits)
            bits_new = bits.copy()
            bits_new[j] ^= 1
            e_new = qubo_energy_18(bits_new)
            delta = e_new - e
            if delta <= 0 or rng.random() < math.exp(-delta / max(temp, 1e-9)):
                bits = bits_new
                e = e_new
                x ^= (1 << j)
                if e < best_e:
                    best_e = e
            if e == 0.0 and hit_step is None:
                hit_step = step + 1
                # Continue a little less aggressively? No need; record success.
                # We can break because zero energy is the objective.
                break

        best_energies.append(best_e)
        if x in ground_set or e == 0.0:
            successes += 1
            if hit_step is None:
                hit_step = steps
            steps_to_success.append(hit_step)

    p_random = len(ground) / n_candidates
    return QuboResult(
        n_bits=n_bits,
        n_candidates=n_candidates,
        n_ground_states=len(ground),
        random_success_fraction=p_random,
        random_expected_queries=1 / p_random,
        simulated_annealing_runs=runs,
        simulated_annealing_success_rate=successes / runs,
        simulated_annealing_mean_best_energy=float(statistics.mean(best_energies)),
        simulated_annealing_median_steps_to_success=(
            float(statistics.median(steps_to_success)) if steps_to_success else None
        ),
    )


# ---------------------------------------------------------------------------
# Small closed-system quantum annealing simulation
# ---------------------------------------------------------------------------

def qubo_energy_8(bits: np.ndarray) -> float:
    """Small QUBO for direct quantum annealing state-vector simulation."""
    # fixed prefix: b0=1, b1=0
    fixed = (bits[0] - 1) ** 2 + (bits[1] - 0) ** 2
    # exactly two of b2..b5 selected
    cardinality = (np.sum(bits[2:6]) - 2) ** 2
    # consistency constraints: b6=b2 and b7=not b3
    consistency = (bits[6] - bits[2]) ** 2 + (bits[7] + bits[3] - 1) ** 2
    return float(fixed + cardinality + consistency)


def problem_energies_8(n_bits: int = 8) -> np.ndarray:
    return np.array([qubo_energy_8(bits_from_int(i, n_bits)) for i in range(2**n_bits)], dtype=np.float64)


def sparse_x_sum_hamiltonian(n_bits: int):
    """Return H0 = -sum_i X_i as sparse matrix over computational basis."""
    if sp is None:
        raise RuntimeError("scipy is required for quantum annealing simulation")
    dim = 2**n_bits
    rows: List[int] = []
    cols: List[int] = []
    data: List[float] = []
    for state in range(dim):
        for i in range(n_bits):
            flipped = state ^ (1 << i)
            rows.append(flipped)
            cols.append(state)
            data.append(-1.0)
    return sp.csr_matrix((data, (rows, cols)), shape=(dim, dim), dtype=np.complex128)


def run_quantum_annealing_small(
    anneal_times: Sequence[float] = (0.5, 1.0, 2.0, 4.0, 8.0),
    n_bits: int = 8,
    time_steps: int = 160,
) -> List[QuantumAnnealingResult]:
    if sp is None or spla is None:
        raise RuntimeError("scipy is required for quantum annealing simulation")
    dim = 2**n_bits
    energies = problem_energies_8(n_bits)
    min_energy = float(np.min(energies))
    ground_mask = energies == min_energy
    n_ground = int(np.sum(ground_mask))
    H0 = sparse_x_sum_hamiltonian(n_bits)
    Hp = sp.diags(energies.astype(np.complex128), offsets=0, format="csr")
    psi0 = np.ones(dim, dtype=np.complex128) / math.sqrt(dim)
    results: List[QuantumAnnealingResult] = []

    for T in anneal_times:
        psi = psi0.copy()
        dt = T / time_steps
        for step in range(time_steps):
            s = (step + 0.5) / time_steps
            H = (1.0 - s) * H0 + s * Hp
            psi = spla.expm_multiply((-1j * dt) * H, psi)
            # Numerical cleanup.
            psi = psi / np.linalg.norm(psi)
        probs = np.abs(psi) ** 2
        ground_prob = float(np.sum(probs[ground_mask]))
        expected_e = float(np.dot(probs, energies))
        norm_error = float(abs(np.linalg.norm(psi) - 1.0))
        results.append(
            QuantumAnnealingResult(
                n_bits=n_bits,
                n_candidates=dim,
                n_ground_states=n_ground,
                anneal_time=float(T),
                n_time_steps=time_steps,
                ground_state_probability=ground_prob,
                final_expected_energy=expected_e,
                norm_error=norm_error,
            )
        )
    return results


# ---------------------------------------------------------------------------
# Plotting and persistence
# ---------------------------------------------------------------------------

def write_csv(path: Path, rows: Sequence[dict]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def make_plots(out_dir: Path, grover_results: List[GroverResult], qa_results: List[QuantumAnnealingResult]) -> None:
    if plt is None:
        return
    out_dir.mkdir(parents=True, exist_ok=True)

    # Plot 1: expected verifier calls for single-success search.
    single = [r for r in grover_results if r.n_successes == 1]
    xs = [r.n_candidates for r in single]
    classical = [r.classical_expected_queries for r in single]
    quantum = [r.quantum_expected_verifier_calls for r in single]
    plt.figure(figsize=(7, 4.5))
    plt.loglog(xs, classical, marker="o", label="Classical random retry")
    plt.loglog(xs, quantum, marker="o", label="Grover/amplitude amplification")
    plt.xlabel("Number of candidate trajectories N")
    plt.ylabel("Expected verifier/oracle calls")
    plt.title("Verifier calls: classical retry vs amplitude amplification")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_dir / "grover_query_scaling.png", dpi=180)
    plt.close()

    # Plot 2: quantum annealing ground probability vs anneal time.
    xs2 = [r.anneal_time for r in qa_results]
    ys2 = [r.ground_state_probability for r in qa_results]
    plt.figure(figsize=(7, 4.5))
    plt.plot(xs2, ys2, marker="o")
    plt.xlabel("Anneal time T, arbitrary units")
    plt.ylabel("Final ground-state probability")
    plt.title("Small closed-system quantum annealing simulation")
    plt.tight_layout()
    plt.savefig(out_dir / "quantum_annealing_ground_probability.png", dpi=180)
    plt.close()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class CoreTests(unittest.TestCase):
    def test_grover_matches_analytic(self) -> None:
        n = 5
        N = 2**n
        success_indices = [3]
        for r in range(0, 5):
            sim = grover_statevector_success(n, success_indices, r)
            ana = analytic_grover_success(N, 1, r)
            self.assertAlmostEqual(sim, ana, places=12)

    def test_optimal_iterations_improve_single_success(self) -> None:
        n = 8
        N = 2**n
        r = optimal_grover_iterations(N, 1)
        p = grover_statevector_success(n, [7], r)
        self.assertGreater(p, 0.95)

    def test_qubo_zero_energy_means_verifier_pass(self) -> None:
        energies, ground, _ = enumerate_qubo(18)
        self.assertGreater(len(ground), 0)
        for idx in ground[:20]:
            bits = bits_from_int(int(idx), 18)
            self.assertEqual(qubo_energy_18(bits), 0.0)
            self.assertEqual(int(np.sum(bits[:6] != np.array([1, 0, 1, 1, 0, 0]))), 0)
            self.assertEqual(int(np.sum(bits[6:12])), 2)
            self.assertEqual(int(np.sum(bits[12:18])), 3)
            self.assertEqual(int(bits[6]), int(bits[12]))
            self.assertEqual(int(bits[7]), int(bits[13]))

    def test_quantum_annealing_norm_preserved(self) -> None:
        if sp is None or spla is None:
            self.skipTest("scipy not installed")
        results = run_quantum_annealing_small(anneal_times=(0.5,), n_bits=8, time_steps=20)
        self.assertLess(results[0].norm_error, 1e-10)


def run_tests() -> unittest.result.TestResult:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(CoreTests)
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("results"))
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    if args.test:
        result = run_tests()
        summary = {
            "tests_run": result.testsRun,
            "failures": len(result.failures),
            "errors": len(result.errors),
            "was_successful": result.wasSuccessful(),
        }
        (args.out / "test_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        if not result.wasSuccessful():
            raise SystemExit(1)

    grover_results = run_grover_scaling()
    qubo_result = simulated_annealing_qubo()
    qa_results = run_quantum_annealing_small()

    data = {
        "seed": SEED,
        "grover": [asdict(x) for x in grover_results],
        "qubo": asdict(qubo_result),
        "quantum_annealing_small": [asdict(x) for x in qa_results],
    }
    (args.out / "results.json").write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    write_csv(args.out / "grover_results.csv", [asdict(x) for x in grover_results])
    write_csv(args.out / "quantum_annealing_results.csv", [asdict(x) for x in qa_results])
    write_csv(args.out / "qubo_result.csv", [asdict(qubo_result)])
    make_plots(args.out, grover_results, qa_results)

    print(json.dumps(data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
