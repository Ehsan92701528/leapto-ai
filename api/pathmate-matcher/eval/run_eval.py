#!/usr/bin/env python3
"""Run Leapto AI evaluation suites (intake + RAG)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parent
APP_DIR = EVAL_DIR.parent
sys.path.insert(0, str(APP_DIR))

from ai.extract_rules import build_student_intake, extract_from_text
from rag.portfolio_rag import answer_programme_question
from schemas.ai_models import RagRequest


def _load_json(name: str) -> list[dict]:
    return json.loads((EVAL_DIR / name).read_text(encoding="utf-8"))


def _set_f1(expected: set[str], actual: set[str]) -> tuple[float, float, float]:
    if not expected and not actual:
        return 1.0, 1.0, 1.0
    if not expected or not actual:
        return 0.0, 0.0, 0.0
    tp = len(expected & actual)
    prec = tp / len(actual) if actual else 0.0
    rec = tp / len(expected) if expected else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
    return prec, rec, f1


def run_intake_eval() -> dict:
    cases = _load_json("intake_gold_set.json")
    intent_ok = 0
    intent_total = 0
    country_f1s: list[float] = []
    field_ok = 0
    field_total = 0
    valid_ok = 0
    valid_total = 0
    failures: list[str] = []

    for case in cases:
        text = case["text"]
        exp = case.get("expected", {})
        meta = extract_from_text(text)

        if "valid" in exp:
            valid_total += 1
            want = exp["valid"]
            got = meta["valid"]
            if want == got:
                valid_ok += 1
            else:
                failures.append(f"{case['id']}: valid expected {want}, got {got}")

        if "path_intent" in exp:
            intent_total += 1
            got_intent = meta["path_intent"]
            if got_intent == exp["path_intent"]:
                intent_ok += 1
            else:
                failures.append(
                    f"{case['id']}: intent expected {exp['path_intent']}, got {got_intent}"
                )

        if exp.get("valid", True) and meta["valid"]:
            intake, _ = build_student_intake(text)
            partial = meta.get("partial_intake") or {}

            if "destination_countries" in exp:
                exp_c = set(exp["destination_countries"])
                act_c = set(partial.get("destination_countries") or [])
                _, _, f1 = _set_f1(exp_c, act_c)
                country_f1s.append(f1)
                if f1 < 1.0:
                    failures.append(f"{case['id']}: countries expected {exp_c}, got {act_c}")

            if "field_of_study" in exp:
                field_total += 1
                got_field = partial.get("field_of_study")
                if got_field == exp["field_of_study"]:
                    field_ok += 1
                else:
                    failures.append(
                        f"{case['id']}: field expected {exp['field_of_study']}, got {got_field}"
                    )

            if intake and "target_degree" in exp:
                if intake.target_degree.value != exp["target_degree"]:
                    failures.append(
                        f"{case['id']}: degree expected {exp['target_degree']}, "
                        f"got {intake.target_degree.value}"
                    )

            if intake and "gpa" in exp and intake.gpa != exp["gpa"]:
                failures.append(f"{case['id']}: gpa expected {exp['gpa']}, got {intake.gpa}")

            if intake and "ielts_overall" in exp and intake.ielts_overall != exp["ielts_overall"]:
                failures.append(
                    f"{case['id']}: ielts expected {exp['ielts_overall']}, got {intake.ielts_overall}"
                )

    country_f1_avg = sum(country_f1s) / len(country_f1s) if country_f1s else 1.0
    return {
        "intent_accuracy": intent_ok / intent_total if intent_total else 1.0,
        "valid_accuracy": valid_ok / valid_total if valid_total else 1.0,
        "country_f1_avg": country_f1_avg,
        "field_accuracy": field_ok / field_total if field_total else 1.0,
        "failures": failures,
        "counts": {
            "intent": intent_total,
            "valid": valid_total,
            "country_cases": len(country_f1s),
            "field": field_total,
        },
    }


def run_rag_eval() -> dict:
    cases = _load_json("rag_gold_set.json")
    ok = 0
    failures: list[str] = []

    for case in cases:
        resp = answer_programme_question(
            RagRequest(
                question=case["question"],
                language=case.get("language", "en"),
                max_results=5,
            )
        )
        want_abstain = case.get("expect_abstain", False)
        min_ids = case.get("expect_programme_ids_min", 0)

        if resp.abstain != want_abstain:
            failures.append(
                f"{case['id']}: abstain expected {want_abstain}, got {resp.abstain}"
            )
            continue

        n_cites = len(resp.citations)
        if n_cites < min_ids:
            failures.append(f"{case['id']}: expected >={min_ids} citations, got {n_cites}")
            continue

        ok += 1

    return {
        "rag_pass_rate": ok / len(cases) if cases else 1.0,
        "failures": failures,
        "counts": {"rag_cases": len(cases)},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Leapto AI eval runner")
    parser.add_argument(
        "--suite",
        choices=["intake", "rag", "all"],
        default="intake",
    )
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    exit_code = 0

    if args.suite in ("intake", "all"):
        result = run_intake_eval()
        print("=== Intake eval ===")
        print(f"Intent accuracy:  {result['intent_accuracy']:.1%}")
        print(f"Valid accuracy:   {result['valid_accuracy']:.1%}")
        print(f"Country F1 avg:   {result['country_f1_avg']:.1%}")
        print(f"Field accuracy:   {result['field_accuracy']:.1%}")
        if result["failures"]:
            print(f"Failures ({len(result['failures'])}):")
            for f in result["failures"][:20]:
                print(f"  - {f}")
            if args.verbose:
                for f in result["failures"][20:]:
                    print(f"  - {f}")
        gates = (
            result["intent_accuracy"] >= 0.90,
            result["country_f1_avg"] >= 0.85,
        )
        if not all(gates):
            exit_code = 1
            print("FAIL: intake release gates not met (intent≥90%, country F1≥85%)")
        else:
            print("PASS: intake release gates met")

    if args.suite in ("rag", "all"):
        result = run_rag_eval()
        print("\n=== RAG eval ===")
        print(f"RAG pass rate:    {result['rag_pass_rate']:.1%}")
        if result["failures"]:
            for f in result["failures"]:
                print(f"  - {f}")
        if result["rag_pass_rate"] < 0.95:
            exit_code = 1
            print("FAIL: RAG release gate not met (≥95%)")
        else:
            print("PASS: RAG release gate met")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
