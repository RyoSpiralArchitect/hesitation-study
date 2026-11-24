# Matched Japanese / English open-response experiment

[Research note](../../research-notes/002-open-answers.md) · [Frozen Japanese protocol](protocol.md) · [English companion](../open-en/protocol.md)

The variant codes in the result tables are mini (GPT-4.1 mini), full (GPT-4.1), none and low (two reasoning-effort settings of the same GPT-5.4 snapshot). A = ordinary, B = hesitate when appropriate, F = always hesitate, C = express uncertainty only when uncertain. MC provides four names, and both languages use the same distractors in the same order. The judge sees only a question, its reference and an utterance. A candidate string is the judge's normalization, not a model self-report.

To reproduce the results without network access, install the repository requirements and run from its root:

```sh
python3 experiments/open-ja/analyze.py
python3 experiments/open-ja/diagnostics.py
python3 experiments/open-ja/figure.py
```

The result arrays in analysis.json contain the observed proportion (or difference), lower and upper 95% item-bootstrap limits, and the number of finite resamples. The bootstrap preserves the English/Japanese, model, instruction, format and source/rewrite links of each item. Tables in the research note use percentage points. No multiplicity adjustment was applied; interpret exploratory contrasts jointly with their event counts.

The official dev2 release is the input to sample.py. The original source and SHA-256 are documented in the repository NOTICE and sample.py. items.jsonl is the frozen selected set. responses.jsonl stores the original generations and blinded API judgments, distinguished by job key; ledger.jsonl stores the cost estimates. The separate audit CSV stores a second AI reading. Treat benchmark text and translated or quoted content under the original data terms.

Primary scoring concerns the requested entity. The `extra` column flags additional checkable claims and does not certify or refute them. Bootstrap intervals represent variability across items in this sample, with one realization per cell. The study does not directly measure stable item-level response probabilities.

Total successful API usage at the recorded standard rates was approximately USD 7.04, including both languages, translation and scoring. There were 4,352 response generations, 3,857 distinct grading requests and 128 translations. See diagnostics.json for language-specific accounting.
