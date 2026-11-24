# Hesitation Study

How does asking a language model to hesitate change what it says, the answer it chooses and the confidence it reports? We collect small, paired experiments in Japanese and English. Our primary record is a series of English research notes with Japanese summaries.

[Research notes](research-notes/README.md) · [Multiple-choice report in Japanese](REPORT.md) · [Data and protocols](experiments/)

日本語と英語で同じ問いを出し、モデルが何を答え、どこまで言い切ったかを観察する研究です。各ノートの末尾に日本語要約を置いています。

## Multiple-choice experiments

Eight JMMLU subjects, 80 items per subject. Each model snapshot receives two samples in each condition. A is an ordinary answer, B requests hesitation, C asks for uncertainty only when uncertain, D requests an assertive answer. E rewrites each A utterance without seeing the question, options, gold or confidence. The Japanese archive is preserved byte-for-byte by file. English translations are aligned by item, choice index and original answer key.

## Reproduce the multiple-choice results offline

With Python 3.12, install the pinned dependencies and run from the repository root.

```sh
python3 -m pip install -r requirements.txt
python3 experiments/ja/code/analyze.py
python3 experiments/ja/code/rescore.py score
python3 experiments/en/code/analyze.py
python3 experiments/en/code/rescore.py score
python3 experiments/en/code/check.py
python3 comparison.py
python3 plot.py
```

The committed raw responses are sufficient for all of these commands. The English translation, evaluation and one-item repair runners read OPENAI_API_KEY for live generation. The saved data allow offline reproduction with no API key. Use a separate checkout for a new stochastic run.

## License and attribution

Original software is licensed under [Apache-2.0](LICENSE). The selected JMMLU benchmark data, English translations and benchmark excerpts are distributed under [CC BY-SA 4.0](experiments/en/data/LICENSE-JMMLU.txt). See [NOTICE](NOTICE) for source and attribution.

The paired open-response wave uses a subset of the JAQKET development data (CC BY-SA 4.0). Its protocol, prompts and analysis are in [open-ja](experiments/open-ja/) and [open-en](experiments/open-en/).
