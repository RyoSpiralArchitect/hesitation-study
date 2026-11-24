# 日本語の言い淀みと四択正答率

OpenAI Chat Completions API の実測データと再集計用コード。日付は2026年11月22日。モデルは gpt-4.1-mini-2025-04-14。計画・指示は protocol.md と code/design.py に、結果の読み取りは report.md に収録した。

## データ

| ファイル | 内容 |
|---|---|
| data/manifest.jsonl | 設問ID、科目、設問、元の順序の4選択肢、公開正解キー |
| data/freeze.json | 抽出日時、抽出元のハッシュ、採点規則・プロトコル・設問表の実行前ハッシュ |
| results/responses.jsonl | 成功した要求ごとのAPI出力。応答ID、モデル、fingerprint、本文、終了理由、実測トークンを含む |
| results/requests.jsonl | 送信予約と決済・通信異常を記録したローカル台帳。金額は公示単価による概算 |
| results/scored.csv | 予定した全出力の判定。rep は1から始まる。hedge は留保語形、pause はフィラー等。E の確率は空欄 |
| results/summary.csv, effects.csv, subjects.csv | 条件ごとの総計、Aとの差と設問対応区間、科目別の集計 |
| results/transitions.json, calibration.csv | 条件間・反復間の答えの移動、自己申告確率のビン別集計 |
| results/audit_blind.csv, audit_key.csv, audit_read.csv | 盲検点検用の文、対応表、条件別集計を読む前のAIの判定 |
| results/rescore_blind.csv, rescore_key.csv, rescore_read.csv | 事後に行った形式無効の点検票、対応、選択判定 |
| results/sensitivity.csv, sensitivity_effects.csv, sensitivity_transitions.json | 形式無効を読み直した場合の総計、差、選択の一致 |
| results/verification.json | 件数、料金、同じ選択に対する申告確率、盲検点検結果の検算 |
| results/figure.png | 実験結果の図 |

割合はCSVでは0–1。記号は発言本文から抽出している。choiceの正解・誤答という判定は四択の選択についてのもので、個々の説明節や事実性全般の採点ではない。

## 手元での再集計

Python 3.12.6、numpy 2.2.3、matplotlib 3.10.6、httpx 0.28.1 を使用した。展開したフォルダで次を実行できる。再集計にはAPIアクセスは不要。

```sh
python3 -m pip install -r requirements.txt
python3 code/analyze.py
python3 code/rescore.py score
python3 code/verify.py
python3 code/figure.py
```

図には、日本語フォントとして macOS のヒラギノ角ゴシックか Linux の Noto Sans CJK を使う。配布した manifest.jsonl は固定済み。問題の当初の抽出を再現するときは別コピーで data/manifest.jsonl を退避してから、固定コミットの JMMLU/JMMLU ディレクトリを引数に prepare.py を実行する。抽出時刻だけは変わる。

生成スクリプト code/run.py は OPENAI_API_KEY を環境から読み、既存の results/responses.jsonl を確認して未完の要求だけを実行する。新規にライブ生成を行う場合は別コピーの results を空にして使う。確率的生成のため、再実行時の回答は変わり得る。

## 出典とライセンス

問題・選択肢・正解キーは Ziqi Yin、Hao Wang、Kaito Horio、Daisuke Kawahara、Satoshi Sekine らの JMMLU から、CC BY-SA 4.0 の対象フォルダの8科目を抽出した。CSVの前後の空白とBOMを整え、元データの行番号に基づく ID を加えて JSONL に変換した。これらのデータとその翻案には同じライセンスが適用される。全文は data/LICENSE-JMMLU.txt を参照。

[JMMLU の固定リビジョン](https://github.com/nlp-waseda/JMMLU/tree/762cbf192c9e4588b574d718f95afd64c96fcbf4) · [原著論文](https://aclanthology.org/2024.sicon-1.2/) · [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) · [OpenAI モデルとトークン単価](https://developers.openai.com/api/docs/models/gpt-4.1-mini)
