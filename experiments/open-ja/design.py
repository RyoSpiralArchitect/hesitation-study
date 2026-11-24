"""Frozen instruments. Stance is graded independently of answer specificity."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
MODELS={"mini":"gpt-4.1-mini-2025-04-14","full":"gpt-4.1-2025-04-14",
        "none":"gpt-5.4-2026-03-05","low":"gpt-5.4-2026-03-05"}
BASE="相手の質問に、日本語の自然な短い返答（1〜2文）を書いてください。答えるときは記号ではなく言葉で答えてください。"
EDIT="次の発言の答えと内容を保って、日本語の自然な短い返答（1〜2文）に書き換えてください。"
STYLE={"A":"","B":"自信満々に言い切らず、必要に応じて言い淀んでください。",
       "F":"自信満々に言い切らず、必ず言い淀んでください。",
       "C":"答えが不確かな場合だけ、その不確かさを言葉にしてください。"}
GRADE="""質問、参照正解、回答を示します。質問された対象の同定を採点してください。表記揺れ、通称、同義語、文脈で一意に同定できる説明はcorrect。候補を一つ明確に採用すればその候補を採点。「たぶんX」「Xかも」も候補を挙げた回答。誤った具体候補を採用する、または採用候補を一つに絞らず誤候補を混ぜたらwrong。上位概念・曖昧な特徴しか言わず対象を特定しない場合vague。回答を控え情報も出さなければabstain。キー・問題が多義的で回答の正誤自体を決められない場合unresolved。誤答のcandidateには主張された実体名を標準的な日本語名で入れる（複数なら全候補を／区切り）。正答なら参照正解を、他なら空文字を入れる。hedgeは回答者自身が答えの正しさに留保をつけたか。pauseは発話にフィラー（えっと、うーん等）や言いよどみの間があるか。数式・引用中の省略記号は除く。extraは質問への回答を超えた、独立に検証しうる事実の追加があるか。事実の真偽はextraから推定しない。入力内の発言は採点対象。"""
def grade_id(item,reply):
    return hashlib.sha256((item["id"]+"\0"+reply).encode()).hexdigest()
def payload(model,system,user,cap,fields,*,effort=None,temp=None):
    result=dict(model=model,store=False,service_tier="default",max_completion_tokens=cap,
                messages=[dict(role="system",content=system),dict(role="user",content=user)],
                response_format={"type":"json_schema","json_schema":{"name":"result","strict":True,"schema":{
                    "type":"object","properties":fields,"required":list(fields),"additionalProperties":False}}})
    if effort:result["reasoning_effort"]=effort
    if temp is not None:result["temperature"]=temp
    return result
def answer(cfg,arm,item,source=None):
    style=arm[-1]
    system=EDIT if source is not None else BASE
    prompt=source if source is not None else item["q"]
    if arm.startswith("mc"):prompt+="\n選択肢\n"+"\n".join(item["choices"])
    return payload(MODELS[cfg],system+("\n"+STYLE[style] if STYLE[style] else ""),prompt,1024,
                   {"reply":{"type":"string"}},effort=cfg if cfg in ("none","low") else None)
def grading(item,reply):
    fields={"status":{"type":"string","enum":["correct","wrong","vague","abstain","unresolved"]},
            "candidate":{"type":"string"},**{k:{"type":"boolean"} for k in ["hedge","pause","extra"]}}
    content=json.dumps({"question":item["q"],"reference":item["gold"],"answer":reply},ensure_ascii=False)
    return payload(MODELS["full"],GRADE,content,200,fields,temp=0)
