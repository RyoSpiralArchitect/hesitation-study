# 003 · Did conditional hedging pick out errors?

**24 November 2026 · Same 128 short-answer questions per language.** The C instruction asks the model to express uncertainty only when it is uncertain. We looked at how often that expression accompanied a wrong identification and how often it accompanied a correct one. The larger configurations often answered the question correctly, leaving few mistakes on which to test that distinction.

| Model / effort | JA errors, A → C | JA C hedged wrong / hedged correct¹ | EN errors, A → C | EN C hedged wrong / hedged correct¹ |
|---|---:|---|---:|---|
| GPT-4.1 mini | 21 → 23 | 3/23 vs 1/104 | 27 → 23 | 0/23 vs 0/103 |
| GPT-4.1 | 9 → 10 | 0/10 vs 3/118 | 13 → 14 | 1/14 vs 2/114 |
| GPT-5.4 none | 1 → 4 | 0/4 vs 1/124 | 13 → 12 | 0/12 vs 2/116 |
| GPT-5.4 low | 0 → 1 | 0/1 vs 1/127 | 7 → 9 | 0/9 vs 1/119 |

¹ These are the frozen judge labels. Each fraction is hedged answers divided by all answers of that type under C. Values such as 0/0 are undefined. A is ordinary generation. Model names specify API snapshots, without known parameter counts.

Our selectivity measure subtracts the hedge rate on correct answers from the hedge rate on wrong answers. For GPT-4.1 mini the change in selectivity from A to C was +12.1 [-0.9, +27.6] points in Japanese and +0.0 [+0.0, +0.0] in English. These are observational conditional rates. The set of wrong answers may itself change between instructions. The [0, 0] interval on English mini comes from observing no hedging in either arm. The empirical resamples carry that same boundary.

A second AI reading of 212 selected A/C outputs covered every judge-wrong answer and the other replies flagged by either the judge or the lexical detector. It found two missed hedges. English GPT-5.4 low C had **1/9** hedged wrong answers on this reading. The missed case was “You’re probably thinking of the three peas of communication.” With 1/119 for correct answers and no hedges in the observed low baseline, C-minus-A selectivity moves from −0.84 to +10.27 points. In Japanese, GPT-4.1 C had **4/118** hedged correct answers after counting 「目だと思います」. A one-utterance change can change the sign of the English low contrast. [Counts and reading decisions](../experiments/open-ja/followup.json)

For the GPT-5.4 comparison, we changed only the requested reasoning effort within the same snapshot. The API reported positive reasoning-token usage on 320/384 Japanese and 317/384 English low-effort calls, counting A, B and C together. An effort setting gives access to a model configuration. The underlying reasoning and any subjective certainty were unobserved. In particular, the Japanese low-effort baseline had zero concrete errors, leaving its A-to-C change in selectivity undefined. These observations do not locate a model-size or reasoning threshold.

**日本語要約**　「不確かな場合だけ」と頼んだとき、誤答と正答に留保が付く割合を別々に数えた。高性能な設定ほど誤答の分母が小さく、推論設定を上げると自己評価が働き始める、という閾値の判定には足りなかった。読み直しでは、英語のGPT-5.4 lowで “probably” を見落とした1件があり、条件Cの誤答中の留保は0/9から1/9になった。

[Matched comparisons and finite bootstrap sample counts](../experiments/open-ja/analysis.json) · [Model settings](../experiments/open-ja/design.py)
