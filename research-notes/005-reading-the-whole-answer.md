# 005 · What survives a hedge?

**24 November 2026 · Post hoc reading of the 128 matched Japanese and English items.** We returned to the archived GPT-4.1 mini replies from the open-response wave. Each pair shares one question. The two first answers were generated separately. Each rewrite saw only its ordinary answer. All counts below refer to these recorded utterances.

## Four names restored many open-answer errors

| Language | Instruction | Open wrong → four names correct | Open correct → four names wrong | Change in all-item correct rate |
|---|---|---:|---:|---:|
| Japanese | Ordinary | 20/21 | 0/106 | +16.4 pp [+10.2, +22.7] |
| Japanese | Hesitate when appropriate | 23/26 | 1/100 | +18.8 pp [+11.7, +25.8] |
| English | Ordinary | 19/27 | 0/99 | +15.6 pp [+9.4, +21.9] |
| English | Hesitate when appropriate | 19/24 | 1/104 | +14.1 pp [+7.8, +20.3] |

The final column uses all 128 paired questions and 95% item-bootstrap intervals, including changes from vague answers. For example, the ordinary Japanese open answer to the hybrid question named a liger and the corresponding four-name reply named a tigon. The choice list contains the expected name and three distractors, so recalling a name independently and recognizing it among candidates pose different tasks. [Frozen instruments](../experiments/open-ja/design.py) · [Transition counts](../experiments/open-ja/followup.json)

## Hedges became more common on wrong answers

| Language | Concrete wrong, ordinary → hesitant | Wrong without a hedge, frozen judge | Wrong without a hedge, second reading | Both replies correct, extra-content flag gained / lost |
|---|---:|---:|---:|---:|
| Japanese | 21 → 26 | 21 → 1 | 21 → 0 | 25 / 3 of 93 pairs |
| English | 27 → 24 | 27 → 9 | 27 → 3 | 29 / 10 of 97 pairs |

The second AI reading covered every mini open A and B reply judged wrong. It found seven missed hedges under B. Six were English, including “I believe” before the misidentification of Haumea. The change in unhedged errors was clearer than the change in the number of wrong targets. The table keeps target-answer judgments fixed. Under B the frozen judge also found hedges on 91 of 100 Japanese correct replies and 30 of 104 English correct replies. Those correct B replies were outside the second stance reading.

The judge flagged more potentially checkable content in the hesitant answers even among pairs judged correct in both arms. These flags include details carried over from the question. In English, “The theme park is called KidZania” became a hedged reply that repeated the date, location and activity listed in the prompt. In Japanese, an answer identifying an éclair restated the prompt's French etymology. The flags measure the judge's reading of the utterance. The truth of independent claims remains a separate measurement. [Counts](../experiments/open-ja/followup.json) · [English items and replies](../experiments/open-en/) · [Japanese items and replies](../experiments/open-ja/)

## The source itself can carry clues

On the dwarf-planet question, the English ordinary answer named **Haumea** and repeated the year and the Easter Island clue. Both rewrites switched to **Makemake**. The Japanese ordinary answer said only 「その準惑星の名前はエリスです。」 Both rewrites kept **Eris** and qualified it. The two source utterances gave their editors different evidence. This single pair leaves both the source text and language available as explanations.

In a second English pair, a rewrite kept the word **liger** but swapped “a male tiger and a female lion” for “a male lion and a female tiger.” This changed the relationship the answer asserted. In Japanese, a required rewrite said 「たぶん合計は25じゃなくてもっと大きい気もします」 after the source had correctly reported the sum as 25. Another Japanese pair retained **tonkatsu** as its sole specific candidate under a hedge, even though the judge moved it from correct to wrong.

A second AI reading examined 38 source–rewrite pairs. The set included all cases flagged by a changed target-answer category or a changed normalized wrong name, plus the four matched hybrid rewrites. The reader saw the question and the two utterances, with condition and judge labels hidden. The reading marked 29 names or answer descriptions as retained, four as withdrawn, three as changed and two as unclear. These counts describe the selected cases. The screen can miss changes when the judge gives both replies the same label. Full factual equivalence would require checking the clauses beyond the requested answer. [Examples, counts and reading files](../experiments/open-ja/README.md#post-hoc-reading)

**日本語要約**　四択で候補を見せると、自由記述の誤答のうち通常条件で日本語20/21件、英語19/27件が正答になった。「言い淀んで」と頼むと誤答を読み直すと、留保なしの誤答は日本語21→0件、英語27→3件。正しい答えにも留保や補足が見られた。事後編集では、元の文に残った手掛かりから誤答を直した例、同じ名前のまま説明を書き換えた例、正しい数値を取り下げた例があった。
