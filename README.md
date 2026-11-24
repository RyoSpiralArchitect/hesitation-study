# Hesitation Study

同じ誤答でも、モデルはどこまで言い切るのか。日本語の四択640問とその英訳を使い、正答、言葉による留保、自己申告した正答確率を比較する。

[日本語実験](experiments/ja/report.md) · [英語追試と日英比較](REPORT.md) · [英語追試の計画](experiments/en/protocol.md)

## Experimental design

Eight JMMLU subjects, 80 items per subject. Each model snapshot receives two samples in each condition. A is an ordinary answer, B requests hesitation, C asks for uncertainty only when uncertain, D requests an assertive answer. E rewrites each A utterance without seeing the question, options, gold or confidence. The Japanese archive is preserved byte-for-byte by file. English translations are aligned by item, choice index and original answer key.

## Reproduce offline

With Python 3.12, install the pinned dependencies and run from the repository root.

```sh
python3 -m pip install -r requirements.txt
python3 experiments/ja/code/analyze.py
python3 experiments/ja/code/rescore.py score
python3 experiments/en/code/analyze.py
python3 experiments/en/code/rescore.py score
python3 comparison.py
```

The committed raw responses are sufficient for all of these commands. The English translation, evaluation and one-item repair runners read OPENAI_API_KEY for live generation. The saved data allow offline reproduction with no API key. Use a separate checkout for a new stochastic run.

## License and attribution

Original software is licensed under [Apache-2.0](LICENSE). The selected JMMLU benchmark data, English translations and benchmark excerpts are distributed under [CC BY-SA 4.0](experiments/en/data/LICENSE-JMMLU.txt). See [NOTICE](NOTICE) for source and attribution.
