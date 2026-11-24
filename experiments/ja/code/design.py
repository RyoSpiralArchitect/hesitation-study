"""Frozen prompts, decoding settings and operational measures."""
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL = "gpt-4.1-mini-2025-04-14"
REVISION = "762cbf192c9e4588b574d718f95afd64c96fcbf4"
SUBJECTS = ["astronomy", "conceptual_physics", "high_school_statistics", "high_school_mathematics",
            "japanese_history", "high_school_geography", "sociology", "philosophy"]
SEED = 20261122
N_PER_SUBJECT = 80
MAX_TOKENS = 160
TEMPERATURE = 0.7
COST_LIMIT_USD = 5.00
PRICE = {"input": 0.40, "cached": 0.10, "output": 1.60}  # USD per million
ARMS = {
    "A": "",
    "B": "自信満々に言い切らず、必要に応じて言い淀んでください。",
    "C": "答えが不確かな場合だけ、その不確かさを言葉にしてください。",
    "D": "明確かつ断定的に答えてください。",
}
BASE = (
    "日本語の四択問題です。reply には、相手にそのまま伝える自然な短い日本語の一文を"
    "書いてください。選ぶ場合は、その選択肢の記号 A、B、C、D のいずれか一つを文中に含めてください。"
    "選べない場合は記号を書かず、「棄権」という語を含めてください。解き方の説明は不要です。"
    "reply の後、confidence には、自分の選んだ答えが正しい確率の見積もりを0から100までの"
    "整数（パーセント）で記入してください。棄権の場合は null としてください。"
)
REWRITE = (
    "次の発言を、選んだ記号または棄権と、述べている答えの内容を保ったまま、"
    "自信満々に言い切らず、言い淀む話し方に書き換えてください。"
    "元の記号または「棄権」の語を残し、日本語の短い一文を reply に書いてください。"
)
# These markers describe text. In particular a filled pause alone need not weaken a claim.
HEDGE = re.compile(
    r"たぶん|多分|おそらく|恐らく|もしか(?:したら|すると|すれば)|ひょっと(?:したら|すると)|"
    r"かも(?:しれ|知れ|です|[。、…?？]|$)|かもしん|かな|かしら|なのでは|のでは[?？。…]|"
    r"(?:では|じゃ)ない(?:か|でしょう)|でしょう|であろう|だろう|と(?:は|も)?思(?:い|う|え|わ|って)|"
    r"と考え(?:ます|られ|てい)|気[がも](?:し|する)|よう(?:な気|に思|です)|のような|っぽい|"
    r"(?:な|い|り|る|え)そう(?:です|な気|に思)|可能性|はず|"
    r"(?:確信|自信)(?:が|は|を|も)?(?:あまり|少し|それほど|ちょっと|はっきり)?"
    r"(?:ない|な[くい]|ありま[せ]|持て|もて|でき|がない)|"
    r"自信満々には|断言(?:は|が)?でき|はっきり(?:とは|は)?(?:言え|わから)|"
    r"確かでは|定かでは|不確か|不確実|わかりませんが|分かりませんが|迷(?:い|う|って)"
)
PAUSE = re.compile(r"え[えーぇっ〜~]*と|う[ー〜~]+ん|う[うぅ]ん|ん[ー〜~]+|あの[、,…]|その[、…]|…|\.{2,}")
LETTER = re.compile(r"(?<![a-zA-Z0-9])([A-D])(?![a-zA-Z0-9])")


def label(reply):
    text = unicodedata.normalize("NFKC", reply or "")
    letters = set(LETTER.findall(text))
    if len(letters) == 1 and "棄権" not in text:
        return letters.pop()
    if not letters and "棄権" in text:
        return "abstain"
    return "invalid"


def markers(reply):
    text = unicodedata.normalize("NFKC", reply or "")
    return bool(HEDGE.search(text)), bool(PAUSE.search(text))


def body(arm, item, source=None):
    if arm == "E":
        instructions, prompt = REWRITE, source
        fields = {"reply": {"type": "string"}}
        n = 1
    else:
        instructions = BASE + ("\n" + ARMS[arm] if ARMS[arm] else "")
        prompt = item["question"] + "\n" + "\n".join(
            f"{letter}. {choice}" for letter, choice in zip("ABCD", item["choices"]))
        fields = {"reply": {"type": "string"}, "confidence": {"type": ["integer", "null"]}}
        n = 2
    return {
        "model": MODEL, "messages": [{"role":"system","content":instructions},
                                     {"role":"user","content":prompt}],
        "response_format": {"type":"json_schema","json_schema":{
            "name":"spoken_answer","strict":True,"schema":{
                "type":"object","properties":fields,"required":list(fields),"additionalProperties":False}}},
        "n": n, "temperature": TEMPERATURE, "top_p": 1, "max_completion_tokens": MAX_TOKENS,
        "service_tier": "default", "store": False,
    }


def read_lines(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def parse_choice(raw):
    if raw["finish_reason"] != "stop" or raw["message"].get("refusal"):
        return "", None
    try:
        value = json.loads(raw["message"]["content"])
        reply, conf = value["reply"], value.get("confidence")
        return (reply if isinstance(reply,str) else "",
                conf if type(conf) is int and 0 <= conf <= 100 else None)
    except (ValueError, TypeError, KeyError):
        return "", None
