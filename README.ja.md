# 日本語ガイド

## このリポジトリの内容

このリポジトリは、次の論文の英日バイリンガル資料一式を公開するものです。

**検証可能なAIイテレーションのための量子支援ハーネス：振幅増幅とアニーリングによる候補探索**

英語タイトル:

**Quantum-Assisted Harnesses for Verifiable AI Iteration: Candidate Search via Amplitude Amplification and Annealing**

含まれているものは次の通りです。

- 英語版 PDF と LaTeX ソース
- 日本語版 PDF、DOCX、Markdown
- 再現用 Python コード
- 論文で使った固定済み数値結果
- 図表
- 最新パッケージの検証メモ

## まず見るファイル

1. 日本語 PDF: [`ai_quantum_bilingual_latest/japanese/quantum_assisted_ai_harness_ja_latest.pdf`](ai_quantum_bilingual_latest/japanese/quantum_assisted_ai_harness_ja_latest.pdf)
2. 英語 PDF: [`ai_quantum_bilingual_latest/english/quantum_assisted_ai_harness_en_latest.pdf`](ai_quantum_bilingual_latest/english/quantum_assisted_ai_harness_en_latest.pdf)
3. 最新確認ステータス: [`ai_quantum_bilingual_latest/CHECKED_STATUS_LATEST.txt`](ai_quantum_bilingual_latest/CHECKED_STATUS_LATEST.txt)
4. 再現用コードとデータ: [`ai_quantum_bilingual_latest/shared/`](ai_quantum_bilingual_latest/shared/)

## フォルダ構成

```text
ai_quantum_bilingual_latest/
  english/   英語版 PDF、LaTeX ソース、BibTeX 関連ファイル、arXiv 用ソース一式
  japanese/  日本語版 PDF、DOCX、Markdown、メタデータ
  shared/    実験コード、固定済み出力、CSV、図、テスト、ライセンス
```

## 数値結果を再現する方法

必要な環境:

- Python >= 3.10
- NumPy
- SciPy
- Matplotlib

実行手順:

```bash
cd ai_quantum_bilingual_latest/shared
python3 quantum_agent_search_experiment.py --out results --test
```

期待されるテスト結果:

```text
Ran 4 tests
OK
```

同梱の検証メモでは、再実行した `results.json` が固定済みの `shared/results.json` と一致したと記録されています。

## 主な数値結果

- Grover 探索、`N = 65,536`、`M = 1`: 古典的な期待検証回数 = `65,536`、Grover 成功確率 = `0.999988`、期待 verifier/oracle 呼び出し回数 = `202.002`
- QUBO 検証器、18 bit: 候補数 `262,144`、ゼロエネルギー状態 `76`、ランダム探索の期待試行回数 `3,449.3`、模擬アニーリングの成功率 `500` 回中 `1.000`
- 小規模な閉鎖系量子アニーリング: 基底状態確率が `T = 0.5` の `0.028523` から `T = 8.0` の `0.602547` へ増加

## 範囲と注意点

これは理論的な定式化と CPU シミュレーションによる検証パッケージです。現在の量子ハードウェア上で量子優位性を実証したものではありません。論文の焦点は、AI エージェントの反復を機械的に検証可能な候補探索として整理し、どの条件で量子探索の考え方が AI ハーネス設計に入りうるかを示すことです。

## AI 利用の開示

同梱資料では、原稿作成、編集、コード整理、パッケージ化の補助として GPT-5.5 Pro を使用したと記載されています。最終内容の責任は人間の著者にあります。
