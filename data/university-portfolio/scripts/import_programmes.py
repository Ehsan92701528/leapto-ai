#!/usr/bin/env python3
"""Validate, load, and export university portfolio CSV data (Phase B)."""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
SEED_DIR = REPO_ROOT / "seed"
CACHE_DIR = REPO_ROOT / "cache"

REQUIRED_COLUMNS = {
    "countries.csv": {"code", "name_en", "source_url"},
    "leapto_field_tags.csv": {"slug", "label_en"},
    "universities_import.csv": {"country_code", "name_en", "source_url"},
    "programmes_import.csv": {
        "country_code",
        "university_name_en",
        "title_en",
        "degree_level",
        "programme_url",
        "source_url",
    },
    "programme_requirements_import.csv": {
        "country_code",
        "university_name_en",
        "programme_title_en",
        "source_url",
    },
    "programme_costs_import.csv": {
        "country_code",
        "university_name_en",
        "programme_title_en",
        "academic_year",
        "tuition_amount",
        "currency",
        "source_url",
    },
    "intakes_import.csv": {
        "country_code",
        "university_name_en",
        "programme_title_en",
        "start_term",
        "source_url",
    },
}

IMPORT_ORDER = [
    "countries.csv",
    "leapto_field_tags.csv",
    "universities_import.csv",
    "programmes_import.csv",
    "programme_requirements_import.csv",
    "programme_costs_import.csv",
    "intakes_import.csv",
]


def parse_bool(value: str) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y"}


def parse_dt(value: str) -> Optional[datetime]:
    value = (value or "").strip()
    if not value:
        return None
    if len(value) == 10:
        return datetime.fromisoformat(value)
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def validate_csv(path: Path) -> list[str]:
    errors: list[str] = []
    required = REQUIRED_COLUMNS.get(path.name)
    if required is None:
        return [f"No validator for {path.name}"]

    with path.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None:
            return [f"{path.name}: empty file"]
        missing = required - set(reader.fieldnames)
        if missing:
            errors.append(f"{path.name}: missing columns {sorted(missing)}")
            return errors
        for i, row in enumerate(reader, start=2):
            for col in required:
                if not (row.get(col) or "").strip():
                    errors.append(f"{path.name} row {i}: empty {col}")
    return errors


def database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql://leapto:leapto@127.0.0.1:5433/leapto_portfolio",
    )


def connect():
    try:
        import psycopg2
    except ImportError as exc:
        raise RuntimeError("Install psycopg2-binary: pip3 install psycopg2-binary") from exc
    import psycopg2

    return psycopg2.connect(database_url())


def apply_schema(conn) -> None:
    schema_path = REPO_ROOT / "schema.sql"
    sql = schema_path.read_text(encoding="utf-8")
    statements: list[str] = []
    buffer: list[str] = []
    for line in sql.splitlines():
        stripped = line.strip().upper()
        if stripped in {"BEGIN;", "COMMIT;"}:
            continue
        buffer.append(line)
        if line.rstrip().endswith(";"):
            stmt = "\n".join(buffer).strip()
            if stmt:
                statements.append(stmt)
            buffer = []
    with conn.cursor() as cur:
        for stmt in statements:
            cur.execute(stmt)
    conn.commit()


def upsert_country(cur, row: dict[str, str]) -> int:
    cur.execute(
        """
        INSERT INTO countries (code, name_en, name_fa, is_active, source_url, last_verified_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (code) DO UPDATE SET
            name_en = EXCLUDED.name_en,
            name_fa = EXCLUDED.name_fa,
            is_active = EXCLUDED.is_active,
            source_url = EXCLUDED.source_url,
            last_verified_at = EXCLUDED.last_verified_at,
            updated_at = NOW()
        RETURNING id
        """,
        (
            row["code"].strip(),
            row["name_en"].strip(),
            (row.get("name_fa") or "").strip() or None,
            parse_bool(row.get("is_active", "true")),
            row["source_url"].strip(),
            parse_dt(row.get("last_verified_at", "")),
        ),
    )
    return int(cur.fetchone()[0])


def upsert_field_tag(cur, row: dict[str, str]) -> int:
    cur.execute(
        """
        INSERT INTO leapto_field_tags (slug, label_en, label_fa, leapto_category)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (slug) DO UPDATE SET
            label_en = EXCLUDED.label_en,
            label_fa = EXCLUDED.label_fa,
            leapto_category = EXCLUDED.leapto_category
        RETURNING id
        """,
        (
            row["slug"].strip(),
            row["label_en"].strip(),
            (row.get("label_fa") or "").strip() or None,
            (row.get("leapto_category") or "").strip() or None,
        ),
    )
    return int(cur.fetchone()[0])


def get_country_id(cur, code: str) -> int:
    cur.execute("SELECT id FROM countries WHERE code = %s", (code.strip(),))
    row = cur.fetchone()
    if not row:
        raise ValueError(f"Unknown country code: {code}")
    return int(row[0])


def get_field_tag_id(cur, slug: str) -> Optional[int]:
    if not slug:
        return None
    cur.execute("SELECT id FROM leapto_field_tags WHERE slug = %s", (slug.strip(),))
    row = cur.fetchone()
    return int(row[0]) if row else None


def upsert_university(cur, row: dict[str, str]) -> int:
    country_id = get_country_id(cur, row["country_code"])
    cur.execute(
        """
        INSERT INTO universities (
            country_id, name_en, name_fa, city_en, ranking_band, website_url,
            source_url, last_verified_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (country_id, name_en) DO UPDATE SET
            name_fa = EXCLUDED.name_fa,
            city_en = EXCLUDED.city_en,
            ranking_band = EXCLUDED.ranking_band,
            website_url = EXCLUDED.website_url,
            source_url = EXCLUDED.source_url,
            last_verified_at = EXCLUDED.last_verified_at,
            updated_at = NOW()
        RETURNING id
        """,
        (
            country_id,
            row["name_en"].strip(),
            (row.get("name_fa") or "").strip() or None,
            (row.get("city_en") or "").strip() or None,
            (row.get("ranking_band") or "").strip() or None,
            (row.get("website_url") or "").strip() or None,
            row["source_url"].strip(),
            parse_dt(row.get("last_verified_at", "")),
        ),
    )
    return int(cur.fetchone()[0])


def get_university_id(cur, country_code: str, name_en: str) -> int:
    country_id = get_country_id(cur, country_code)
    cur.execute(
        "SELECT id FROM universities WHERE country_id = %s AND name_en = %s",
        (country_id, name_en.strip()),
    )
    row = cur.fetchone()
    if not row:
        raise ValueError(f"Unknown university: {name_en} ({country_code})")
    return int(row[0])


def upsert_programme(cur, row: dict[str, str]) -> int:
    university_id = get_university_id(cur, row["country_code"], row["university_name_en"])
    field_tag_id = get_field_tag_id(cur, row.get("field_tag_slug", ""))
    cur.execute(
        """
        INSERT INTO programmes (
            university_id, title_en, title_fa, degree_level, field_tag_id,
            programme_url, duration_months, delivery_mode, source_url,
            last_verified_at, requirements_confidence
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (university_id, title_en, degree_level) DO UPDATE SET
            field_tag_id = EXCLUDED.field_tag_id,
            programme_url = EXCLUDED.programme_url,
            duration_months = EXCLUDED.duration_months,
            delivery_mode = EXCLUDED.delivery_mode,
            source_url = EXCLUDED.source_url,
            last_verified_at = EXCLUDED.last_verified_at,
            requirements_confidence = EXCLUDED.requirements_confidence,
            updated_at = NOW()
        RETURNING id
        """,
        (
            university_id,
            row["title_en"].strip(),
            (row.get("title_fa") or "").strip() or None,
            row["degree_level"].strip(),
            field_tag_id,
            row["programme_url"].strip(),
            int(row["duration_months"]) if (row.get("duration_months") or "").strip() else None,
            (row.get("delivery_mode") or "").strip() or None,
            row["source_url"].strip(),
            parse_dt(row.get("last_verified_at", "")),
            (row.get("requirements_confidence") or "medium").strip(),
        ),
    )
    return int(cur.fetchone()[0])


def get_programme_id(cur, country_code: str, university_name: str, title: str) -> int:
    university_id = get_university_id(cur, country_code, university_name)
    cur.execute(
        """
        SELECT id FROM programmes
        WHERE university_id = %s AND title_en = %s AND degree_level = 'Master'
        """,
        (university_id, title.strip()),
    )
    row = cur.fetchone()
    if not row:
        raise ValueError(f"Unknown programme: {title} at {university_name}")
    return int(row[0])


def upsert_requirements(cur, row: dict[str, str]) -> None:
    programme_id = get_programme_id(
        cur, row["country_code"], row["university_name_en"], row["programme_title_en"]
    )

    def num(value: str) -> Optional[float]:
        value = (value or "").strip()
        return float(value) if value else None

    cur.execute(
        """
        INSERT INTO programme_requirements (
            programme_id, min_ielts_overall, min_toefl_ibt, min_gpa_4, min_gpa_20,
            gre_required, gmat_required, work_experience_years_min,
            entry_notes_en, source_url, last_verified_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (programme_id) DO UPDATE SET
            min_ielts_overall = EXCLUDED.min_ielts_overall,
            min_toefl_ibt = EXCLUDED.min_toefl_ibt,
            min_gpa_4 = EXCLUDED.min_gpa_4,
            min_gpa_20 = EXCLUDED.min_gpa_20,
            gre_required = EXCLUDED.gre_required,
            gmat_required = EXCLUDED.gmat_required,
            work_experience_years_min = EXCLUDED.work_experience_years_min,
            entry_notes_en = EXCLUDED.entry_notes_en,
            source_url = EXCLUDED.source_url,
            last_verified_at = EXCLUDED.last_verified_at,
            updated_at = NOW()
        """,
        (
            programme_id,
            num(row.get("min_ielts_overall", "")),
            int(row["min_toefl_ibt"]) if (row.get("min_toefl_ibt") or "").strip() else None,
            num(row.get("min_gpa_4", "")),
            num(row.get("min_gpa_20", "")),
            parse_bool(row.get("gre_required", "")) if row.get("gre_required") else None,
            parse_bool(row.get("gmat_required", "")) if row.get("gmat_required") else None,
            num(row.get("work_experience_years_min", "")),
            (row.get("entry_notes_en") or "").strip() or None,
            row["source_url"].strip(),
            parse_dt(row.get("last_verified_at", "")),
        ),
    )


def upsert_cost(cur, row: dict[str, str]) -> None:
    programme_id = get_programme_id(
        cur, row["country_code"], row["university_name_en"], row["programme_title_en"]
    )
    cur.execute(
        """
        INSERT INTO programme_costs (
            programme_id, academic_year, tuition_amount, currency,
            living_cost_estimate, source_url, last_verified_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (programme_id, academic_year) DO UPDATE SET
            tuition_amount = EXCLUDED.tuition_amount,
            currency = EXCLUDED.currency,
            living_cost_estimate = EXCLUDED.living_cost_estimate,
            source_url = EXCLUDED.source_url,
            last_verified_at = EXCLUDED.last_verified_at,
            updated_at = NOW()
        """,
        (
            programme_id,
            row["academic_year"].strip(),
            float(row["tuition_amount"]),
            row["currency"].strip(),
            float(row["living_cost_estimate"]) if (row.get("living_cost_estimate") or "").strip() else None,
            row["source_url"].strip(),
            parse_dt(row.get("last_verified_at", "")),
        ),
    )


def upsert_intake(cur, row: dict[str, str]) -> None:
    programme_id = get_programme_id(
        cur, row["country_code"], row["university_name_en"], row["programme_title_en"]
    )
    deadline = (row.get("application_deadline") or "").strip() or None
    start_term = row["start_term"].strip()
    cur.execute(
        "DELETE FROM intakes WHERE programme_id = %s AND start_term = %s",
        (programme_id, start_term),
    )
    cur.execute(
        """
        INSERT INTO intakes (
            programme_id, start_term, application_deadline, is_rolling,
            source_url, last_verified_at
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (
            programme_id,
            row["start_term"].strip(),
            deadline,
            parse_bool(row.get("is_rolling", "false")),
            row["source_url"].strip(),
            parse_dt(row.get("last_verified_at", "")),
        ),
    )


def load_directory(conn, directory: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    loaders = {
        "countries.csv": lambda cur, row: upsert_country(cur, row),
        "leapto_field_tags.csv": lambda cur, row: upsert_field_tag(cur, row),
        "universities_import.csv": lambda cur, row: upsert_university(cur, row),
        "programmes_import.csv": lambda cur, row: upsert_programme(cur, row),
        "programme_requirements_import.csv": lambda cur, row: upsert_requirements(cur, row),
        "programme_costs_import.csv": lambda cur, row: upsert_cost(cur, row),
        "intakes_import.csv": lambda cur, row: upsert_intake(cur, row),
    }

    with conn.cursor() as cur:
        for filename in IMPORT_ORDER:
            path = directory / filename
            if not path.exists():
                raise FileNotFoundError(path)
            rows = read_csv(path)
            loader = loaders[filename]
            for row in rows:
                loader(cur, row)
            counts[filename] = len(rows)
    conn.commit()
    return counts


def export_json_cache(conn, out_path: Path) -> int:
    query = """
        SELECT
            p.id AS programme_id,
            c.name_en AS country_en,
            c.code AS country_code,
            u.name_en AS university_en,
            u.city_en,
            u.ranking_band,
            p.title_en AS programme_title,
            p.degree_level,
            ft.slug AS field_tag_slug,
            ft.label_en AS field_tag_en,
            ft.leapto_category,
            p.programme_url,
            p.requirements_confidence,
            pr.min_ielts_overall,
            pr.min_gpa_4,
            pr.min_gpa_20,
            pr.entry_notes_en,
            pc.tuition_amount,
            pc.currency,
            pc.living_cost_estimate,
            i.start_term,
            i.application_deadline
        FROM programmes p
        JOIN universities u ON u.id = p.university_id
        JOIN countries c ON c.id = u.country_id
        LEFT JOIN leapto_field_tags ft ON ft.id = p.field_tag_id
        LEFT JOIN programme_requirements pr ON pr.programme_id = p.id
        LEFT JOIN programme_costs pc ON pc.programme_id = p.id
        LEFT JOIN intakes i ON i.programme_id = p.id
        WHERE p.is_active AND u.is_active
        ORDER BY p.id
    """
    with conn.cursor() as cur:
        cur.execute(query)
        columns = [desc[0] for desc in cur.description]
        rows = [dict(zip(columns, row)) for row in cur.fetchall()]

    for row in rows:
        if row.get("application_deadline") is not None:
            row["application_deadline"] = row["application_deadline"].isoformat()
        for key in ("min_ielts_overall", "min_gpa_4", "min_gpa_20", "tuition_amount", "living_cost_estimate"):
            if row.get(key) is not None:
                row[key] = float(row[key])

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({"programmes": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="University portfolio CSV tools")
    parser.add_argument("--data-dir", type=Path, default=SEED_DIR, help="CSV directory")
    parser.add_argument("--dry-run", action="store_true", help="Validate CSVs only")
    parser.add_argument("--apply-schema", action="store_true", help="Apply schema.sql before load")
    parser.add_argument("--load", action="store_true", help="Load CSVs into PostgreSQL")
    parser.add_argument("--export-json", type=Path, help="Export DB rows to JSON cache file")
    args = parser.parse_args()

    data_dir = args.data_dir
    if not data_dir.exists():
        print(f"Missing data directory: {data_dir}", file=sys.stderr)
        print("Run: python3 scripts/generate_uk_msc_seed.py", file=sys.stderr)
        return 1

    paths = [data_dir / name for name in IMPORT_ORDER if (data_dir / name).exists()]
    all_errors: list[str] = []
    for path in paths:
        all_errors.extend(validate_csv(path))

    if all_errors:
        print("Validation failed:")
        for err in all_errors:
            print(f"  - {err}")
        return 1

    print(f"OK: validated {len(paths)} CSV file(s) in {data_dir}")
    if args.dry_run and not args.load and not args.export_json and not args.apply_schema:
        return 0

    conn = connect()
    try:
        if args.apply_schema:
            apply_schema(conn)
            print("Applied schema.sql")

        if args.load:
            counts = load_directory(conn, data_dir)
            for name, n in counts.items():
                print(f"  loaded {n} rows from {name}")

        if args.export_json:
            n = export_json_cache(conn, args.export_json)
            print(f"Exported {n} programmes to {args.export_json}")
    finally:
        conn.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
