# AI Quantum Harness Paper - Bilingual Latest Package

This package contains the synchronized Japanese and English latest versions of the paper:

**Quantum-Assisted Harnesses for Verifiable AI Iteration: Candidate Search via Amplitude Amplification and Annealing**

Japanese title:
**検証可能なAIイテレーションのための量子支援ハーネス：振幅増幅とアニーリングによる候補探索**

## Author information

- Author / 著者: Mojofull Furoku
- Affiliation / 所属: none listed / なし
- Email: mojofull.furoku@gmail.com
- Date: 2026-04-26

## What was synchronized

Both Japanese and English versions reflect:

- the same title and author information;
- no affiliation listed;
- no external funding or additional acknowledgments;
- AI assistance disclosure;
- the same numerical results;
- the same Python source code and frozen outputs;
- the same figures and references;
- README requirement updated to Python >= 3.10;
- Anthropic Skills reference year updated to 2026.

## Directory structure

```text
english/
  quantum_assisted_ai_harness_en_latest.pdf
  quantum_assisted_ai_harness_en_latest.tex
  references_en_latest.bib
  main_en_latest.bbl
  arxiv_source_upload_en_latest.zip
  ARXIV_METADATA_EN_LATEST.txt
  README_ancillary_en_latest.md
  arxiv_source/

japanese/
  quantum_assisted_ai_harness_ja_latest.pdf
  quantum_assisted_ai_harness_ja_latest.docx
  quantum_assisted_ai_harness_ja_latest.md
  JAPANESE_METADATA_LATEST.txt

shared/
  quantum_agent_search_experiment.py
  results.json
  grover_results.csv
  qubo_result.csv
  quantum_annealing_results.csv
  test_summary.json
  requirements.txt
  LICENSE
  grover_query_scaling.png
  quantum_annealing_ground_probability.png

qa/
  Rendered page images and re-run logs used for local verification.
```

## Reproduction

```bash
cd shared
python3 quantum_agent_search_experiment.py --out results --test
```

The expected unit-test summary is:

```text
Ran 4 tests
OK
```

The reproduced `results.json` matched the frozen `shared/results.json` in the latest package.

## Scope

The experiments are CPU simulations. The paper does not claim quantum advantage on current quantum hardware.

## AI assistance disclosure

The author used GPT-5.5 Pro as an assistive tool for manuscript drafting, editing, code organization, and packaging. The human author is responsible for the final content.
