#!/usr/bin/env python3
"""Generate ~50 UK MSc seed CSV rows for Phase B (5 fields × 10 programmes)."""

from __future__ import annotations

import csv
from pathlib import Path

SEED_DIR = Path(__file__).resolve().parents[1] / "seed"

UNIVERSITIES = [
    ("University of Edinburgh", "Edinburgh", "top100", "https://www.ed.ac.uk"),
    ("University of Manchester", "Manchester", "top100", "https://www.manchester.ac.uk"),
    ("Imperial College London", "London", "top100", "https://www.imperial.ac.uk"),
    ("University College London", "London", "top100", "https://www.ucl.ac.uk"),
    ("King's College London", "London", "top100", "https://www.kcl.ac.uk"),
    ("University of Bristol", "Bristol", "top100", "https://www.bristol.ac.uk"),
    ("University of Warwick", "Coventry", "top100", "https://warwick.ac.uk"),
    ("University of Glasgow", "Glasgow", "top100", "https://www.gla.ac.uk"),
    ("University of Birmingham", "Birmingham", "top200", "https://www.birmingham.ac.uk"),
    ("University of Leeds", "Leeds", "top200", "https://www.leeds.ac.uk"),
    ("University of Sheffield", "Sheffield", "top200", "https://www.sheffield.ac.uk"),
    ("University of Nottingham", "Nottingham", "top200", "https://www.nottingham.ac.uk"),
    ("University of Southampton", "Southampton", "top200", "https://www.southampton.ac.uk"),
    ("Queen Mary University of London", "London", "top200", "https://www.qmul.ac.uk"),
    ("University of Liverpool", "Liverpool", "top200", "https://www.liverpool.ac.uk"),
    ("Newcastle University", "Newcastle", "top200", "https://www.ncl.ac.uk"),
    ("Cardiff University", "Cardiff", "top200", "https://www.cardiff.ac.uk"),
    ("University of Exeter", "Exeter", "top200", "https://www.exeter.ac.uk"),
    ("University of York", "York", "top200", "https://www.york.ac.uk"),
    ("London School of Economics", "London", "top100", "https://www.lse.ac.uk"),
]

PROGRAMMES = [
    # cs_data_science × 10
    ("cs_data_science", "MSc Data Science"),
    ("cs_data_science", "MSc Artificial Intelligence"),
    ("cs_data_science", "MSc Computer Science"),
    ("cs_data_science", "MSc Advanced Computer Science"),
    ("cs_data_science", "MSc Machine Learning"),
    ("cs_data_science", "MSc Data Analytics"),
    ("cs_data_science", "MSc Computing and Data Science"),
    ("cs_data_science", "MSc Software Engineering"),
    ("cs_data_science", "MSc Cyber Security"),
    ("cs_data_science", "MSc Robotics and Autonomous Systems"),
    # business_mba × 10
    ("business_mba", "MSc Management"),
    ("business_mba", "MSc Business Analytics"),
    ("business_mba", "MSc International Business"),
    ("business_mba", "MSc Marketing"),
    ("business_mba", "MSc Finance and Management"),
    ("business_mba", "MSc Entrepreneurship"),
    ("business_mba", "MSc Strategic Marketing"),
    ("business_mba", "MSc Global Business"),
    ("business_mba", "MSc Human Resource Management"),
    ("business_mba", "MSc Project Management"),
    # engineering_general × 10
    ("engineering_general", "MSc Advanced Mechanical Engineering"),
    ("engineering_general", "MSc Electrical Power Systems"),
    ("engineering_general", "MSc Civil Engineering"),
    ("engineering_general", "MSc Structural Engineering"),
    ("engineering_general", "MSc Renewable Energy Engineering"),
    ("engineering_general", "MSc Aerospace Engineering"),
    ("engineering_general", "MSc Materials Science and Engineering"),
    ("engineering_general", "MSc Biomedical Engineering"),
    ("engineering_general", "MSc Chemical Engineering"),
    ("engineering_general", "MSc Engineering Management"),
    # health_public × 10
    ("health_public", "MSc Public Health"),
    ("health_public", "MSc Global Health"),
    ("health_public", "MSc Health Data Science"),
    ("health_public", "MSc Epidemiology"),
    ("health_public", "MSc Health Policy"),
    ("health_public", "MSc Clinical Research"),
    ("health_public", "MSc Biomedical Sciences"),
    ("health_public", "MSc Nursing Studies"),
    ("health_public", "MSc Health Economics"),
    ("health_public", "MSc Medical Statistics"),
    # economics_finance × 10
    ("economics_finance", "MSc Economics"),
    ("economics_finance", "MSc Finance"),
    ("economics_finance", "MSc Financial Economics"),
    ("economics_finance", "MSc Accounting and Finance"),
    ("economics_finance", "MSc Banking and Finance"),
    ("economics_finance", "MSc Economics and Policy"),
    ("economics_finance", "MSc Quantitative Finance"),
    ("economics_finance", "MSc International Finance"),
    ("economics_finance", "MSc Money and Banking"),
    ("economics_finance", "MSc Applied Economics"),
]


def _tier(idx: int, ranking: str) -> tuple[float, float, float, int]:
    """Return min_gpa_20, min_ielts, tuition, confidence tier from uni ranking."""
    base_gpa = 14.0 if ranking == "top200" else 15.0
    base_ielts = 6.5 if ranking == "top200" else 7.0
    if ranking == "top100" and idx % 5 == 0:
        return base_gpa + 1.5, 7.0, 42000, 3  # reach-ish
    if ranking == "top100":
        return base_gpa + 0.5, 6.5, 36000, 2
    return base_gpa, 6.5, 28000, 1


def main() -> None:
    SEED_DIR.mkdir(parents=True, exist_ok=True)

    with (SEED_DIR / "countries.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["code", "name_en", "name_fa", "is_active", "source_url", "last_verified_at"])
        w.writerow(["GB", "United Kingdom", "انگلیس", "true", "https://www.gov.uk", "2026-05-01"])

    with (SEED_DIR / "leapto_field_tags.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["slug", "label_en", "label_fa", "leapto_category"])
        w.writerows(
            [
                ("cs_data_science", "Data Science & AI", "علوم داده و هوش مصنوعی", "Computer Engineering & Computer Science"),
                ("business_mba", "Business & MBA", "مدیریت و MBA", "Management, Business & Industrial Engineering"),
                ("engineering_general", "Engineering", "مهندسی", "Electrical Engineering"),
                ("health_public", "Public Health & Medicine", "سلامت و پزشکی", "Life Sciences & Medicine"),
                ("economics_finance", "Economics & Finance", "اقتصاد و مالی", "Economic & Financial Studies"),
            ]
        )

    uni_seen: dict[str, list] = {}
    prog_rows = []
    req_rows = []
    cost_rows = []
    intake_rows = []

    for i, (field_slug, title) in enumerate(PROGRAMMES):
        uni_name, city, ranking, web = UNIVERSITIES[i % len(UNIVERSITIES)]
        if uni_name not in uni_seen:
            source = f"{web}/study/postgraduate"
            uni_seen[uni_name] = ["GB", uni_name, "", city, ranking, web, source, "2026-05-01"]
        source = f"{web}/study/postgraduate"
        gpa20, ielts, tuition, _ = _tier(i, ranking)
        min_gpa4 = round(gpa20 / 20 * 4, 2)

        prog_rows.append([
            "GB", uni_name, title, "Master", field_slug, source, "12", "on_campus",
            source, "2026-05-01", "high" if i % 3 else "medium",
        ])
        req_rows.append([
            "GB", uni_name, title, str(ielts), "92", str(min_gpa4), str(gpa20),
            "false", "false", "", f"Upper second-class honours or equivalent", source, "2026-05-01",
        ])
        cost_rows.append([
            "GB", uni_name, title, "2025/26", str(tuition), "GBP", "12000", source, "2026-05-01",
        ])
        intake_rows.append([
            "GB", uni_name, title, "September 2026", "2026-07-31", "false", source, "2026-05-01",
        ])

    def write_csv(name: str, header: list[str], rows: list[list]) -> None:
        with (SEED_DIR / name).open("w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(header)
            w.writerows(rows)

    write_csv(
        "universities_import.csv",
        ["country_code", "name_en", "name_fa", "city_en", "ranking_band", "website_url", "source_url", "last_verified_at"],
        list(uni_seen.values()),
    )
    write_csv(
        "programmes_import.csv",
        [
            "country_code", "university_name_en", "title_en", "degree_level", "field_tag_slug",
            "programme_url", "duration_months", "delivery_mode", "source_url", "last_verified_at",
            "requirements_confidence",
        ],
        prog_rows,
    )
    write_csv(
        "programme_requirements_import.csv",
        [
            "country_code", "university_name_en", "programme_title_en", "min_ielts_overall",
            "min_toefl_ibt", "min_gpa_4", "min_gpa_20", "gre_required", "gmat_required",
            "work_experience_years_min", "entry_notes_en", "source_url", "last_verified_at",
        ],
        req_rows,
    )
    write_csv(
        "programme_costs_import.csv",
        [
            "country_code", "university_name_en", "programme_title_en", "academic_year",
            "tuition_amount", "currency", "living_cost_estimate", "source_url", "last_verified_at",
        ],
        cost_rows,
    )
    write_csv(
        "intakes_import.csv",
        [
            "country_code", "university_name_en", "programme_title_en", "start_term",
            "application_deadline", "is_rolling", "source_url", "last_verified_at",
        ],
        intake_rows,
    )

    print(f"Wrote seed CSVs to {SEED_DIR} ({len(PROGRAMMES)} programmes)")


if __name__ == "__main__":
    main()
