"""English instruments for the same task. The blinded grading rubric is shared."""
import importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parent
SHARED=ROOT.parent/"open-ja"
spec=importlib.util.spec_from_file_location("japanese_design",SHARED/"design.py")
ja=importlib.util.module_from_spec(spec)
spec.loader.exec_module(ja)
MODELS,grade_id,grading=ja.MODELS,ja.grade_id,ja.grading
BASE="Write a natural, short reply in English (one or two sentences) to the person's question. When answering, give the answer in words rather than a letter or symbol."
EDIT="Rewrite the following statement as a natural, short reply in English (one or two sentences), preserving its answer and content."
STYLE={"A":"","B":"Avoid sounding overly confident, and hesitate when appropriate.",
       "F":"Avoid sounding overly confident, and be sure to hesitate.",
       "C":"Express your uncertainty in words only when you are uncertain about the answer."}
def answer(cfg,arm,item,source=None):
    system=EDIT if source is not None else BASE
    prompt=source if source is not None else item["q"]
    if arm.startswith("mc"):prompt+="\nOptions\n"+"\n".join(item["choices"])
    style=STYLE[arm[-1]]
    return ja.payload(MODELS[cfg],system+("\n"+style if style else ""),prompt,1024,
                      {"reply":{"type":"string"}},effort=cfg if cfg in ("none","low") else None)
