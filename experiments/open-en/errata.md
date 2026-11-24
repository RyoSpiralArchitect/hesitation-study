# English instrument checks

A scan after generation found literal English answer names, ignoring disambiguators such as “(sewing)” in five questions. IDs are QA20CAPR-0295 (iron), QA20CAPR-0347 (coral), QA20QBIK-0559 (cowboy), QA20QBIK-0599 (bobbin), and QA20QBIK-0989 (laissez-faire). A paired sensitivity analysis drops these from both languages, leaving 123 questions.

Three further reference problems became apparent when reading outputs. The corresponding 120-item analysis removes these three IDs from both languages as well. The immutable raw records retain what was actually shown. This is a diagnostic exclusion using information learned after data collection.

| ID | Problem | Source |
|---|---|---|
| QA20CAPR-0683 | Japanese マントヒヒ was rendered “Mandrill”. The corresponding English species is the hamadryas baboon. | [Chiba Zoological Park](https://www.city.chiba.jp/zoo/zone/data-hamadryas_baboon.html) |
| QA20CAPR-0897 | 筮竹 was rendered “Saichiku”. The Japanese reading is zeichiku. Translated responses that describe or name a different set of divination sticks need semantic review. | [Kobe Women's University Library](https://lib.yg.kobe-wu.ac.jp/exhibition12.html) |
| QA20QBIK-0839 | The Japanese title ある愛の詩 was translated literally as “A Certain Love Poem”. The conventional English title “Love Story” appears elsewhere in the option set. The Japanese source question itself also attributes the film to Arthur Miller. The credited director is Arthur Hiller. | [Paramount Japan](https://paramount.jp/search/detail.php?id=8306) |

Kanji rebuses, titles and culturally specific names can remain unequal in difficulty across languages even after removing these eight items. The sensitivity checks do not establish that every remaining question is translation-equivalent.

A further review flagged QA20QBIK-0381. The Japanese rebus replaces the four dots of 鳥 with 木 to form 梟. The English wording describes turning 鳥 itself into 木. The mini model objected to this premise in A and B, with closely related replies scored as vague and wrong. A [119-item sensitivity](../open-ja/followup.json) also excludes this ID from both languages. The 123- and 120-item analyses reflect the earlier stages of the errata.
