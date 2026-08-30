#!/usr/bin/env python3
"""Fail-closed validation and publication for the verified UK Master's catalogue."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

PORTFOLIO_DIR = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = PORTFOLIO_DIR / "verified_2027"

FILES = {
    "programmes.csv": {
        "university_name_en", "title_en", "subject_family", "leapto_category",
        "programme_url", "duration_months", "delivery_mode", "last_verified_at",
    },
    "requirements.csv": {
        "university_name_en", "programme_title_en", "entry_notes_en",
        "source_url", "last_verified_at",
    },
    "costs.csv": {
        "university_name_en", "programme_title_en", "academic_year",
        "tuition_amount", "currency", "source_url", "last_verified_at",
    },
    "intakes.csv": {
        "university_name_en", "programme_title_en", "start_term",
        "application_deadline", "is_rolling", "source_url", "last_verified_at",
    },
}


@dataclass
class Result:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    rows: list[dict[str, Any]] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)


def read_csv(path: Path) -> tuple[list[dict[str, str]], set[str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader), set(reader.fieldnames or [])


def clean(value: Any) -> str:
    return str(value or "").strip()


def parse_bool(value: Any) -> bool:
    return clean(value).lower() in {"1", "true", "yes", "y"}


def row_key(row: dict[str, str], title_field: str) -> tuple[str, str]:
    return clean(row.get("university_name_en")), clean(row.get(title_field))


def hostname(url: str) -> str:
    return (urlparse(url).hostname or "").lower().removeprefix("www.")


def is_official_url(url: str, domain: str, *, programme_specific: bool = False) -> bool:
    parsed = urlparse(clean(url))
    host = (parsed.hostname or "").lower().removeprefix("www.")
    expected = clean(domain).lower().removeprefix("www.")
    if parsed.scheme != "https" or not host or not (host == expected or host.endswith("." + expected)):
        return False
    if programme_specific and clean(parsed.path) in {"", "/"}:
        return False
    return True


def parse_iso_date(value: str, label: str, result: Result) -> date | None:
    try:
        return date.fromisoformat(clean(value)[:10])
    except ValueError:
        result.errors.append(f"{label}: expected ISO date, got {value!r}")
        return None


def validate_verified_date(
    value: str, label: str, as_of: date, maximum_age_days: int, result: Result
) -> None:
    verified = parse_iso_date(value, label, result)
    if verified is None:
        return
    age = (as_of - verified).days
    if age < 0:
        result.errors.append(f"{label}: verification date is in the future")
    elif age > maximum_age_days:
        result.errors.append(f"{label}: verification is {age} days old (maximum {maximum_age_days})")


def index_one(
    rows: list[dict[str, str]], filename: str, title_field: str, result: Result
) -> dict[tuple[str, str], dict[str, str]]:
    indexed: dict[tuple[str, str], dict[str, str]] = {}
    for line, row in enumerate(rows, start=2):
        key = row_key(row, title_field)
        if not all(key):
            result.errors.append(f"{filename} row {line}: missing university or programme title")
            continue
        if key in indexed:
            result.errors.append(f"{filename} row {line}: duplicate record for {key[0]} / {key[1]}")
        indexed[key] = row
    return indexed


def validate(
    data_dir: Path,
    source_registry: Path,
    policy_path: Path,
    *,
    as_of: date,
    minimum_programmes: int = 0,
) -> Result:
    result = Result()
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    maximum_age = int(policy["maximum_verification_age_days"])

    source_rows, source_columns = read_csv(source_registry)
    required_source_columns = {
        "university_name_en", "city_en", "official_domain",
        "postgraduate_catalogue_url", "priority", "source_status",
    }
    missing_source_columns = required_source_columns - source_columns
    if missing_source_columns:
        result.errors.append(f"source registry: missing columns {sorted(missing_source_columns)}")

    sources: dict[str, dict[str, str]] = {}
    domains: set[str] = set()
    for line, row in enumerate(source_rows, start=2):
        name = clean(row.get("university_name_en"))
        domain = clean(row.get("official_domain")).lower().removeprefix("www.")
        if not name or not domain:
            result.errors.append(f"source registry row {line}: missing university name or domain")
            continue
        if name in sources:
            result.errors.append(f"source registry row {line}: duplicate university {name}")
        if domain in domains:
            result.errors.append(f"source registry row {line}: duplicate domain {domain}")
        if not is_official_url(clean(row.get("postgraduate_catalogue_url")), domain):
            result.errors.append(f"source registry row {line}: catalogue URL is not on {domain}")
        sources[name] = row
        domains.add(domain)

    source_count = len(sources)
    min_universities = int(policy["target_university_count_min"])
    max_universities = int(policy["target_university_count_max"])
    if not min_universities <= source_count <= max_universities:
        result.errors.append(
            f"source registry: expected {min_universities}–{max_universities} universities, found {source_count}"
        )

    tables: dict[str, list[dict[str, str]]] = {}
    for filename, required_columns in FILES.items():
        path = data_dir / filename
        if not path.exists():
            result.errors.append(f"missing required file: {path}")
            tables[filename] = []
            continue
        rows, columns = read_csv(path)
        missing = required_columns - columns
        if missing:
            result.errors.append(f"{filename}: missing columns {sorted(missing)}")
        tables[filename] = rows

    programmes = index_one(tables["programmes.csv"], "programmes.csv", "title_en", result)
    requirements = index_one(tables["requirements.csv"], "requirements.csv", "programme_title_en", result)
    costs = index_one(tables["costs.csv"], "costs.csv", "programme_title_en", result)
    intakes = index_one(tables["intakes.csv"], "intakes.csv", "programme_title_en", result)

    if len(programmes) < minimum_programmes:
        result.errors.append(f"catalogue: expected at least {minimum_programmes} programmes, found {len(programmes)}")

    subject_families = set(policy["subject_families"])
    flattened: list[dict[str, Any]] = []
    for key, programme in programmes.items():
        university, title = key
        label = f"{university} / {title}"
        source = sources.get(university)
        if source is None:
            result.errors.append(f"{label}: university is not in the approved source registry")
            continue
        domain = clean(source["official_domain"])
        family = clean(programme.get("subject_family"))
        if family not in subject_families:
            result.errors.append(f"{label}: unsupported subject family {family!r}")
        if clean(programme.get("delivery_mode")) != policy["delivery_mode"]:
            result.errors.append(f"{label}: only {policy['delivery_mode']} delivery is publishable")
        if not is_official_url(clean(programme.get("programme_url")), domain, programme_specific=True):
            result.errors.append(f"{label}: programme URL is not a specific page on {domain}")
        validate_verified_date(
            clean(programme.get("last_verified_at")), f"{label} programme", as_of, maximum_age, result
        )

        related: dict[str, dict[str, str]] = {}
        for table_name, index in (("requirements", requirements), ("costs", costs), ("intakes", intakes)):
            row = index.get(key)
            if row is None:
                result.errors.append(f"{label}: missing {table_name} record")
            else:
                related[table_name] = row
                if not is_official_url(clean(row.get("source_url")), domain, programme_specific=True):
                    result.errors.append(f"{label}: {table_name} source is not a specific page on {domain}")
                validate_verified_date(
                    clean(row.get("last_verified_at")), f"{label} {table_name}", as_of, maximum_age, result
                )
        if len(related) != 3:
            continue

        requirement = related["requirements"]
        cost = related["costs"]
        intake = related["intakes"]
        if not clean(requirement.get("entry_notes_en")):
            result.errors.append(f"{label}: entry requirements notes are required")
        if clean(cost.get("academic_year")) != policy["academic_year"]:
            result.errors.append(f"{label}: cost must be for academic year {policy['academic_year']}")
        if clean(cost.get("currency")) != policy["currency"]:
            result.errors.append(f"{label}: tuition currency must be {policy['currency']}")
        try:
            tuition = float(clean(cost.get("tuition_amount")))
            if tuition <= 0:
                raise ValueError
        except ValueError:
            result.errors.append(f"{label}: tuition must be a positive number")
            tuition = 0.0
        if clean(intake.get("start_term")) != policy["target_intake"]:
            result.errors.append(f"{label}: intake must be {policy['target_intake']}")
        deadline_text = clean(intake.get("application_deadline"))
        rolling = parse_bool(intake.get("is_rolling"))
        deadline = parse_iso_date(deadline_text, f"{label} application deadline", result) if deadline_text else None
        if deadline is None and not rolling:
            result.errors.append(f"{label}: deadline is required unless admissions are officially rolling")
        if deadline is not None and deadline <= as_of:
            result.errors.append(f"{label}: application deadline is not in the future")

        flattened.append({
            "country_en": "United Kingdom",
            "country_code": policy["country_code"],
            "university_en": university,
            "city_en": clean(source.get("city_en")),
            "ranking_band": "",
            "programme_title": title,
            "degree_level": policy["degree_level"],
            "field_tag_slug": family,
            "field_tag_en": family.replace("-", " ").title(),
            "leapto_category": clean(programme.get("leapto_category")),
            "programme_url": clean(programme.get("programme_url")),
            "requirements_confidence": "high",
            "min_ielts_overall": float(clean(requirement.get("min_ielts_overall"))) if clean(requirement.get("min_ielts_overall")) else None,
            "min_gpa_4": float(clean(requirement.get("min_gpa_4"))) if clean(requirement.get("min_gpa_4")) else None,
            "min_gpa_20": float(clean(requirement.get("min_gpa_20"))) if clean(requirement.get("min_gpa_20")) else None,
            "entry_notes_en": clean(requirement.get("entry_notes_en")),
            "tuition_amount": tuition,
            "currency": policy["currency"],
            "living_cost_estimate": None,
            "start_term": policy["target_intake"],
            "application_deadline": deadline_text or None,
            "last_verified_at": clean(programme.get("last_verified_at")),
        })

    programme_keys = set(programmes)
    for name, index in (("requirements", requirements), ("costs", costs), ("intakes", intakes)):
        for orphan in set(index) - programme_keys:
            result.errors.append(f"{name}: orphan record for {orphan[0]} / {orphan[1]}")

    flattened.sort(key=lambda row: (row["university_en"], row["programme_title"]))
    for programme_id, row in enumerate(flattened, start=1):
        row["programme_id"] = programme_id
    result.rows = flattened
    result.metrics = {
        "approved_universities": source_count,
        "programmes": len(programmes),
        "publishable_rows": len(flattened) if not result.errors else 0,
        "universities_with_programmes": len({key[0] for key in programmes}),
        "subject_family_counts": dict(Counter(row.get("subject_family", "") for row in programmes.values())),
        "target_programmes": int(policy["target_programme_count"]),
    }
    if not programmes:
        result.warnings.append("Catalogue structure is valid but contains no verified programme rows yet")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_ROOT / "incoming")
    parser.add_argument("--source-registry", type=Path, default=DEFAULT_ROOT / "university_sources.csv")
    parser.add_argument("--policy", type=Path, default=DEFAULT_ROOT / "catalogue_policy.json")
    parser.add_argument("--as-of", type=date.fromisoformat, default=date.today())
    parser.add_argument("--min-programmes", type=int, default=0)
    parser.add_argument("--report-json", type=Path)
    parser.add_argument("--output-json", type=Path)
    args = parser.parse_args()

    result = validate(
        args.data_dir,
        args.source_registry,
        args.policy,
        as_of=args.as_of,
        minimum_programmes=args.min_programmes,
    )
    report = {
        "status": "pass" if not result.errors else "fail",
        "checked_at": datetime.now().astimezone().isoformat(),
        "as_of": args.as_of.isoformat(),
        "metrics": result.metrics,
        "errors": result.errors,
        "warnings": result.warnings,
    }
    if args.report_json:
        args.report_json.parent.mkdir(parents=True, exist_ok=True)
        args.report_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if result.errors:
        return 1
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "catalogue": "uk-taught-masters-2027",
            "generated_at": report["checked_at"],
            "quality": "verified-official-sources",
            "programmes": result.rows,
        }
        args.output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Published {len(result.rows)} verified programmes to {args.output_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
