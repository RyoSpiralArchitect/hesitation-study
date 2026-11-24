# 004 · Hesitating on request

**24 November 2026 · GPT-4.1 mini.** In the first experiment, the Japanese model added “えっと” to many rewrites. The instruction for first answers had said “when appropriate”, while the rewriting instruction directly requested hesitation. Here the same style sentence was appended to both tasks. We changed only “必要に応じて” to “必ず”, or “when appropriate” to “be sure to”, within each task. Both edits for each item used the very same ordinary answer as their source and received no question or choices.

| Context | Style clause | JA pauses | EN pauses | JA hedges | EN hedges |
|---|---|---:|---:|---:|---:|
| First answer | When appropriate | 6 | 0 | 118 | 45 |
| First answer | Required | 70 | 2 | 128 | 65 |
| Rewrite | When appropriate | 4 | 0 | 92 | 69 |
| Rewrite | Required | 32 | 1 | 121 | 98 |

Each frozen judge count is out of 128. A hesitation in speech and an epistemic hedge were judged separately. The same utterance can exhibit both. The bilingual judge saw no condition label. A secondary lexical check is available in the [diagnostics](../experiments/open-ja/diagnostics.json).

| Contrast in pause frequency | Japanese | English |
|---|---:|---:|
| Required minus optional, first answer | +50.0 [+41.4, +58.6] | +1.6 [+0.0, +3.9] |
| Required minus optional, rewrite | +21.9 [+14.1, +29.7] | +0.8 [+0.0, +2.3] |
| Rewrite minus first answer, optional | -1.6 [-6.2, +3.1] | +0.0 [+0.0, +0.0] |
| Rewrite minus first answer, required | -29.7 [-41.4, -18.0] | -0.8 [-2.3, +0.0] |
| Difference in wording effects, rewrite minus first answer | -28.1 [-39.8, -16.4] | -0.8 [-2.3, +0.0] |

Entries are percentage-point differences with paired 95% item-bootstrap intervals. In English, the corresponding hedge counts for required first answers and rewrites were 65 and 98. A second AI reading examined 24 replies where the earlier lexical rule and the judge disagreed about a pause. Under the revised reading, optional → required counts in Japanese were **8 → 74** for first answers and **3 → 38** for rewrites. In English they were **1 → 3** and **0 → 1**. Both English revisions counted a missed “Hmm” in first answers. The intervals in the table above use the frozen judge labels. [Counts and reading decisions](../experiments/open-ja/followup.json)

Within Japanese, requiring hesitation increased pauses more strongly in original answers than in rewrites. The earlier near-universal Japanese rewrite fillers did not repeat under this matched wording and new task. The two studies also differ in question set, output instructions and sampling. This new comparison does not apportion the original effect retrospectively.

Editing could also remove an answer. One ordinary Japanese response explicitly named the monk Ikkyū Sōjun. The mandatory rewrite said “たしか、そうだったような気もしますが、間違っているかもしれません。” A listener given only the rewrite would have no name to recover. The [paired close reading](005-reading-the-whole-answer.md) tracks cases where a rewrite kept a name, withdrew it, or changed what was said about it.

**日本語要約**　初答と編集で同じ文体指示を使うと、「必要に応じて」を「必ず」に替える効果を直接比べられる。日本語ではフィラーが最も多かったのは「初答で必ず言い淀む」条件だった。編集で元の名前が消える例も観察できた。

[Japanese prompts and all outputs](../experiments/open-ja/) · [English prompts and all outputs](../experiments/open-en/) · [Previous multiple-choice observation](001-choice-and-commitment.md)
