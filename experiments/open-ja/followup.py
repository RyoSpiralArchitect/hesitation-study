"""Read matched pairs and reproduce the post hoc checks from the archived responses."""
import argparse
import csv
import json
import random
import runpy
import unicodedata
from collections import Counter
from pathlib import Path

import numpy as np

from analyze import BASE, KANJI_ERRATUM, NAME_OVERLAP, REFERENCE_ISSUES, csvout, interval, lines
from design import grade_id

LANGUAGES = ("ja", "en")
REWRITE_ARMS = ("editB", "editF")
HESITATION_ARMS = ("openB", "openF", *REWRITE_ARMS)
AUDIT_DIR = BASE / "open-ja"


def read_csv(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load():
    rows = {}
    items = {}
    for language in LANGUAGES:
        folder = BASE / f"open-{language}"
        rows[language] = {
            (row["id"], row["model"], row["arm"]): row
            for row in read_csv(folder / "scored.csv")
        }
        items[language] = {item["id"]: item for item in lines(folder / "items.jsonl")}
    assert list(items["ja"]) == list(items["en"])
    assert len(items["ja"]) == 128
    return rows, items


def review_cases(rows, items):
    cases = {"hedge": [], "pause": [], "rewrite": []}
    for language in LANGUAGES:
        patterns = runpy.run_path(str(BASE / language / "code/design.py"))
        for (item_id, model, arm), row in rows[language].items():
            utterance = row["reply"]
            normalized = unicodedata.normalize("NFKC", utterance)
            if arm in ("openA", "openC") and (
                row["status"] == "wrong" or row["hedge"] == "1" or patterns["HEDGE"].search(normalized)
            ):
                cases["hedge"].append((language, row, {"reply": utterance}))
            if model != "mini":
                continue
            if arm in HESITATION_ARMS and bool(patterns["PAUSE"].search(normalized)) != (row["pause"] == "1"):
                cases["pause"].append((language, row, {"reply": utterance}))
            if arm in REWRITE_ARMS:
                source = rows[language][item_id, model, "openA"]
                changed_label = row["status"] != source["status"]
                changed_wrong_name = row["status"] == source["status"] == "wrong" and (
                    row["candidate"] != source["candidate"]
                )
                # Also read the same-candidate pair identified by the fresh reviewer.
                if changed_label or changed_wrong_name or item_id == "QA20QBIK-0783":
                    presentation = {
                        "question": items[language][item_id]["q"],
                        "source": source["reply"],
                        "rewrite": utterance,
                    }
                    cases["rewrite"].append((language, row, presentation))

    rng = random.Random(20261127)
    packets = {}
    for kind, entries in cases.items():
        rng.shuffle(entries)
        packets[kind] = {
            f"{kind[0].upper()}{i:03d}": entry
            for i, entry in enumerate(entries, start=1)
        }
    return packets


def bootstrap_differences(differences):
    count = len(differences[0])
    rng = np.random.default_rng(20261125)
    resamples = rng.multinomial(count, [1 / count] * count, size=10_000).astype(np.int32)
    table = np.asarray(differences, dtype=np.int32)
    return np.vstack([table.sum(axis=1), resamples @ table.T]) / count


def describe_open_pairs(records, ids):
    pairs = [(records[i, "mini", "openA"], records[i, "mini", "openB"]) for i in ids]
    same_correct = [(a, b) for a, b in pairs if a["status"] == b["status"] == "correct"]
    extra_delta = [int(b["extra"]) - int(a["extra"]) for a, b in pairs]
    same_correct_delta = [int(b["extra"]) - int(a["extra"]) for a, b in same_correct]
    return {
        "n_both_correct": len(same_correct),
        "extra_flag_gained_among_both_correct": same_correct_delta.count(1),
        "extra_flag_lost_among_both_correct": same_correct_delta.count(-1),
        "extra_flag_rate_difference": interval(bootstrap_differences([extra_delta])[:, 0]),
        "wrong_without_hedge": [
            sum(row["status"] == "wrong" and row["hedge"] == "0" for row in group)
            for group in zip(*pairs)
        ],
        "wrong_with_hedge": [
            sum(row["status"] == "wrong" and row["hedge"] == "1" for row in group)
            for group in zip(*pairs)
        ],
    }


def format_effect(records, ids, condition):
    pairs = [
        (records[i, "mini", f"open{condition}"], records[i, "mini", f"mc{condition}"])
        for i in ids
    ]
    transitions = Counter(f'{a["status"]}->{b["status"]}' for a, b in pairs)
    delta = [int(b["status"] == "correct") - int(a["status"] == "correct") for a, b in pairs]
    return {
        "transitions": dict(sorted(transitions.items())),
        "correct_rate_difference": interval(bootstrap_differences([delta])[:, 0]),
    }


def read_status_overrides(language):
    folder = BASE / f"open-{language}"
    statuses = {}
    for file in ["audit-read.csv", "review-read.csv"]:
        for row in read_csv(folder / file):
            prior = statuses.setdefault(row["key"], row["status"])
            if prior != row["status"]:
                raise ValueError(f"Conflicting readings for {language}/{row['key']}")
    return statuses


def primary_sensitivity(rows, ids, *, audited=False):
    differences = []
    for language in LANGUAGES:
        override = read_status_overrides(language) if audited else {}
        wrong = []
        for item_id in ids:
            pair = [rows[language][item_id, "mini", arm] for arm in ("openA", "openB")]
            wrong.append([
                override.get(grade_id(row, row["reply"]), row["status"]) == "wrong"
                for row in pair
            ])
        differences.append([int(b) - int(a) for a, b in wrong])
    ja, en = bootstrap_differences(differences).T
    return {language: interval(estimates) for language, estimates in zip(
        ("ja", "en", "en_minus_ja"), (ja, en, en - ja)
    )}


def read_annotations(packets):
    decisions = {}
    for kind in packets:
        filename = "rewrite-reading.csv" if kind == "rewrite" else "stance-reading.csv"
        selected = [
            row for row in read_csv(AUDIT_DIR / filename)
            if row["id"].startswith(kind[0].upper())
        ]
        decisions[kind] = {row["id"]: row["reading"] for row in selected}
        if len(selected) != len(decisions[kind]) or decisions[kind].keys() != packets[kind].keys():
            raise ValueError(f"Missing or duplicate {kind} readings")
    return decisions


def stance_sensitivity(rows, packets, decisions, ids):
    result = {}
    for kind in ("hedge", "pause"):
        corrections = []
        delta = {}
        for index, (lang, row, _) in packets[kind].items():
            value = int(decisions[kind][index])
            assert value in (0, 1)
            delta[lang, row["id"], row["model"], row["arm"]] = value
            if value != int(row[kind]):
                corrections.append({
                    "item": row["id"], "language": lang, "model": row["model"],
                    "arm": row["arm"], "judge": int(row[kind]), "reading": value,
                })

        def marks(lang, model, arm, outcome=None):
            pairs = [
                (delta.get((lang, i, model, arm), int(rows[lang][i, model, arm][kind])),
                 rows[lang][i, model, arm]["status"])
                for i in ids
            ]
            return [flag for flag, status in pairs if outcome is None or status == outcome]

        report = {"screened": len(packets[kind]), "corrections": corrections, "counts": {}}
        for lang in LANGUAGES:
            if kind == "pause":
                report["counts"][lang] = {arm: sum(marks(lang, "mini", arm)) for arm in HESITATION_ARMS}
            else:
                counts = {}
                for model in ("mini", "full", "none", "low"):
                    for arm in ("openA", "openC"):
                        for status in ("correct", "wrong"):
                            flags = marks(lang, model, arm, status)
                            counts[f"{model}/{arm}/{status}"] = {"count": sum(flags), "n": len(flags)}
                report["counts"][lang] = counts
        result[kind] = report
    return result


def rewrite_reading(packets, decisions):
    counts = {lang: {arm: Counter() for arm in REWRITE_ARMS} for lang in LANGUAGES}
    for index, (lang, row, _) in packets["rewrite"].items():
        value = decisions["rewrite"][index]
        assert value in ("retained", "dropped", "changed", "added", "unclear")
        counts[lang][row["arm"]][value] += 1
    return {
        lang: {arm: dict(sorted(count.items())) for arm, count in arms.items()}
        for lang, arms in counts.items()
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packets", type=Path, help="Write unlabeled packets to this directory")
    args = parser.parse_args()
    rows, items = load()
    packets = review_cases(rows, items)
    if args.packets:
        args.packets.mkdir(parents=True, exist_ok=True)
        for kind, entries in packets.items():
            csvout(args.packets / f"{kind}.csv", [
                {"id": index, **entry[2]} for index, entry in entries.items()
            ])
        return

    ids = list(items["ja"])
    exclude = NAME_OVERLAP | REFERENCE_ISSUES | {KANJI_ERRATUM}
    retained_ids = [item_id for item_id in ids if item_id not in exclude]
    decisions = read_annotations(packets)
    report = {
        "items": len(ids),
        "audited_primary": primary_sensitivity(rows, ids, audited=True),
        "primary_after_errata": {
            "items": len(retained_ids),
            "excluded": sorted(exclude),
            "paired_estimates": primary_sensitivity(rows, retained_ids),
        },
        "open_pairs": {lang: describe_open_pairs(rows[lang], ids) for lang in LANGUAGES},
        "format": {
            lang: {arm: format_effect(rows[lang], ids, arm) for arm in ("A", "B")}
            for lang in LANGUAGES
        },
        "stance_review": stance_sensitivity(rows, packets, decisions, ids),
        "rewrite_reading": rewrite_reading(packets, decisions),
    }
    (AUDIT_DIR / "followup.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
