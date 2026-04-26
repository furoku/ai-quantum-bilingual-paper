# English Guide

## What this repository contains

This repository publishes the bilingual package for the paper:

**Quantum-Assisted Harnesses for Verifiable AI Iteration: Candidate Search via Amplitude Amplification and Annealing**

The repository includes:

- the English PDF and source bundle;
- the reformatted Japanese PDF, DOCX, and Markdown version;
- reproducibility code;
- frozen numerical outputs used by the manuscript;
- generated figures;
- format rebuild and verification notes for the latest package.

## Recommended reading order

1. Read the English PDF: [`ai_quantum_bilingual_reformatted_latest/english/quantum_assisted_ai_harness_en_latest.pdf`](ai_quantum_bilingual_reformatted_latest/english/quantum_assisted_ai_harness_en_latest.pdf)
2. Read the reformatted Japanese PDF if needed: [`ai_quantum_bilingual_reformatted_latest/japanese/quantum_assisted_ai_harness_ja_reformatted.pdf`](ai_quantum_bilingual_reformatted_latest/japanese/quantum_assisted_ai_harness_ja_reformatted.pdf)
3. Check the format rebuild notes: [`ai_quantum_bilingual_reformatted_latest/README_FORMAT_REBUILD.md`](ai_quantum_bilingual_reformatted_latest/README_FORMAT_REBUILD.md)
4. Inspect the reproducibility package: [`ai_quantum_bilingual_reformatted_latest/shared/`](ai_quantum_bilingual_reformatted_latest/shared/)
5. Re-run the CPU simulation if needed.

## Directory map

```text
ai_quantum_bilingual_reformatted_latest/
  english/   English PDF, source bundle, and extracted source files
  japanese/  Reformatted Japanese PDF, DOCX, Markdown, Japanese figures, and short summary
  shared/    Python experiment code, frozen outputs, CSV files, and tests
```

## Reproducing the numerical outputs

Requirements:

- Python >= 3.10
- NumPy
- SciPy
- Matplotlib

Run:

```bash
cd ai_quantum_bilingual_reformatted_latest/shared
python3 quantum_agent_search_experiment.py --out results --test
```

The expected unit-test result is:

```text
Ran 4 tests
OK
```

The latest package notes state that the experiment code was re-run successfully and the unit tests passed.

## Main numerical results

- Grover search, `N = 65,536`, `M = 1`: classical expected verifier calls = `65,536`; Grover success probability = `0.999988`; expected verifier/oracle calls = `202.002`.
- QUBO verifier, 18 bits: `262,144` candidates; `76` zero-energy states; random expected attempts = `3,449.3`; simulated annealing success rate = `1.000` over `500` runs.
- Small closed-system quantum annealing: ground-state probability increases from `0.028523` at `T = 0.5` to `0.602547` at `T = 8.0`.

## Scope and limitations

This is a theoretical formulation and CPU-simulation validation package. It does not demonstrate quantum advantage on current quantum hardware. The manuscript studies when quantum search primitives could become relevant to AI harness design: the task must be discretized, mechanically verifiable, and resistant to verifier hacking, while coherent implementation and hardware constraints remain major barriers.

## AI assistance disclosure

The package states that GPT-5.5 Pro was used as an assistive tool for manuscript drafting, editing, code organization, and packaging. The human author is responsible for the final content.
