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
COST_LIMIT_USD = 4.00
PRICE = {"input": 0.40, "cached": 0.10, "output": 1.60}  # USD per million
ARMS = {
    "A": "",
    "B": "Avoid sounding overly confident, and hesitate when appropriate.",
    "C": "Express your uncertainty in words only when you are uncertain about the answer.",
    "D": "Answer clearly and assertively.",
}
BASE = (
    "This is a multiple-choice question in English. In reply, write one short, natural English sentence "
    "that you would say directly to the person asking. If you choose an answer, include exactly one "
    "of the option letters A, B, C, or D in your sentence. If you cannot choose, include the word "
    "'abstain' without an option letter. No explanation of how you solved it is needed. "
    "After reply, enter in confidence your estimated probability that the answer you chose is correct, "
    "as an integer percentage from 0 to 100. If you abstain, enter null."
)
REWRITE = (
    "Rewrite the following statement in a hesitant way, avoiding sounding overly confident, while "
    "preserving the chosen letter or abstention and the content of the stated answer. Retain the "
    "original letter or the word 'abstain' and write one short English sentence in reply."
)
HEDGE = re.compile(
    r"\b(?:maybe|perhaps|probably|possibly|presumably|apparently|likely|unlikely|might|could be|may be|"
    r"seems?|appears? to|not (?:entirely |completely |quite )?(?:sure|certain|confident)|uncertain|"
    r"unsure|I (?:think|believe|guess|suspect|suppose|lean|reckon|feel)|I(?:'d| would) (?:say|guess|lean|go with)|"
    r"if I (?:had|have) to (?:choose|guess)|as far as I (?:know|can tell)|if I recall|my (?:best )?guess)\b", re.I)
PAUSE = re.compile(r"\b(?:um+|uh+|erm+|hmm+|er)\b|\bwell[, …]|…|\.{2,}", re.I)
LETTER = re.compile(r"(?<![a-zA-Z0-9])([A-D])(?![a-zA-Z0-9])")


def label(reply):
    text = unicodedata.normalize("NFKC", reply or "")
    letters = set(LETTER.findall(text))
    if len(letters) == 1 and not re.search(r"\babstain\b", text, re.I):
        return letters.pop()
    if not letters and re.search(r"\babstain\b", text, re.I):
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
