"""PostgreSQL access for university portfolio (optional — JSON cache fallback)."""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any, Iterator, Optional

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://leapto:leapto@127.0.0.1:5433/leapto_portfolio",
)


def is_postgres_configured() -> bool:
    return bool(DATABASE_URL.strip())


@contextmanager
def postgres_connection() -> Iterator[Any]:
    try:
        import psycopg2
        import psycopg2.extras
    except ImportError as exc:
        raise RuntimeError("psycopg2-binary is required for PostgreSQL portfolio access") from exc

    conn = psycopg2.connect(DATABASE_URL)
    try:
        yield conn
    finally:
        conn.close()


def fetch_programme_rows() -> Optional[list[dict[str, Any]]]:
    if not is_postgres_configured():
        return None
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
            i.application_deadline::text AS application_deadline
        FROM programmes p
        JOIN universities u ON u.id = p.university_id
        JOIN countries c ON c.id = u.country_id
        LEFT JOIN leapto_field_tags ft ON ft.id = p.field_tag_id
        LEFT JOIN programme_requirements pr ON pr.programme_id = p.id
        LEFT JOIN programme_costs pc ON pc.programme_id = p.id
        LEFT JOIN LATERAL (
            SELECT start_term, application_deadline
            FROM intakes
            WHERE programme_id = p.id
            ORDER BY application_deadline NULLS LAST
            LIMIT 1
        ) i ON TRUE
        WHERE p.is_active AND u.is_active
        ORDER BY p.id
    """
    try:
        with postgres_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                columns = [desc[0] for desc in cur.description]
                rows = []
                for record in cur.fetchall():
                    row = dict(zip(columns, record))
                    for key in (
                        "min_ielts_overall",
                        "min_gpa_4",
                        "min_gpa_20",
                        "tuition_amount",
                        "living_cost_estimate",
                    ):
                        if row.get(key) is not None:
                            row[key] = float(row[key])
                    rows.append(row)
                return rows
    except Exception:
        return None
