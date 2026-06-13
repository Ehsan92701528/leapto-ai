#!/usr/bin/env python3
"""
Extract Leapto path-mate (mentor) data from static HTML into structured JSON.

Usage:
  python3 extract_mentors.py
  python3 extract_mentors.py --lang fa --horizon-dir /path/to/horizon
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from typing import Any

try:
    from bs4 import BeautifulSoup
except ImportError:
    print(
        "Missing dependency: beautifulsoup4\n"
        "Install with: pip install beautifulsoup4",
        file=sys.stderr,
    )
    sys.exit(1)


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_HORIZON = SCRIPT_DIR.parent.parent / "horizon"
DEFAULT_OUTPUT_DIR = SCRIPT_DIR.parent.parent / "data"

COUNTRY_FA_TO_EN: dict[str, str] = {
    "آلمان": "Germany",
    "آمریکا": "United States",
    "اسپانیا": "Spain",
    "استرالیا": "Australia",
    "انگلیس": "United Kingdom",
    "ایتالیا": "Italy",
    "ترکیه": "Turkey",
    "اتریش": "Austria",
    "سوئد": "Sweden",
    "سوئیس": "Switzerland",
    "فرانسه": "France",
    "فنلاند": "Finland",
    "کانادا": "Canada",
    "نیوزلند": "New Zealand",
    "هلند": "Netherlands",
    "کره‌جنوبی": "South Korea",
    "کره جنوبی": "South Korea",
}

DEGREE_CLASS_TO_LEVEL: dict[str, str] = {
    "bookmark-icon-phd": "PhD",
    "bookmark-icon-master": "Master",
    "bookmark-icon-bachelor": "Bachelor",
}


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", unescape(value)).strip()


def slug_from_profile_href(href: str) -> str:
    name = Path(href.strip()).name
    if name.startswith("profile-details-"):
        name = name[len("profile-details-") :]
    return name.removesuffix(".html")


@dataclass
class MentorRecord:
    id: str
    name: str
    name_en: str = ""
    location_text: str = ""
    current_city: str = ""
    current_country_fa: str = ""
    current_country_en: str = ""
    degree_level: str = ""
    fields: list[str] = field(default_factory=list)
    specializations: list[str] = field(default_factory=list)
    universities_listed: list[str] = field(default_factory=list)
    image_path: str = ""
    profile_url: str = ""
    profile_url_en: str = ""
    card_index: int = 0
    active: bool = False
    profile_exists: bool = False
    meta_description: str = ""
    intro: str = ""
    education: list[dict[str, str]] = field(default_factory=list)
    work_experience: list[dict[str, str]] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)
    qualification: str = ""
    experience_years: str = ""
    gender: str = ""
    age_range: str = ""
    search_text: str = ""

    def finalize(self) -> None:
        parts = [
            self.name,
            self.name_en,
            self.location_text,
            self.current_city,
            self.current_country_fa,
            self.current_country_en,
            self.degree_level,
            *self.fields,
            *self.specializations,
            *self.universities_listed,
            self.intro,
            self.meta_description,
            self.qualification,
            *self.languages,
        ]
        for item in self.education:
            parts.extend(item.values())
        for item in self.work_experience:
            parts.extend(item.values())
        self.search_text = clean_text(" ".join(p for p in parts if p))


def parse_location(sub_title: str) -> tuple[str, str, str]:
    text = clean_text(sub_title)
    if not text:
        return "", "", ""

    resident_prefix = "ساکن "
    if text.startswith(resident_prefix):
        text = text[len(resident_prefix) :].strip()
    elif text.lower().startswith("based in "):
        text = text[9:].strip()

    country_fa = ""
    country_en = ""
    city = text

    for fa_name, en_name in sorted(COUNTRY_FA_TO_EN.items(), key=lambda x: len(x[0]), reverse=True):
        if text == fa_name or text.endswith(f" {fa_name}") or fa_name in text:
            country_fa = fa_name
            country_en = en_name
            city = clean_text(text.replace(fa_name, ""))
            break

    if not country_fa:
        lowered = text.lower()
        for token in ("canada", "germany", "switzerland", "uk", "united kingdom", "usa", "australia"):
            if token in lowered:
                city = text
                break

    city = city.strip(" ,،")
    return text, city, country_fa if country_fa else ""


def infer_country_en(country_fa: str, location_text: str) -> str:
    if country_fa:
        return COUNTRY_FA_TO_EN.get(country_fa, "")
    lowered = location_text.lower()
    english_map = {
        "canada": "Canada",
        "germany": "Germany",
        "switzerland": "Switzerland",
        "united kingdom": "United Kingdom",
        "uk": "United Kingdom",
        "usa": "United States",
        "united states": "United States",
        "australia": "Australia",
        "france": "France",
        "italy": "Italy",
        "spain": "Spain",
        "netherlands": "Netherlands",
        "sweden": "Sweden",
        "austria": "Austria",
        "turkey": "Turkey",
        "finland": "Finland",
        "new zealand": "New Zealand",
        "south korea": "South Korea",
    }
    for key, value in english_map.items():
        if key in lowered:
            return value
    return ""


def parse_degree_level(team_item) -> str:
    for node in team_item.find_all(class_=re.compile(r"bookmark-icon-(phd|master|bachelor)")):
        for class_name in node.get("class", []):
            if class_name in DEGREE_CLASS_TO_LEVEL:
                return DEGREE_CLASS_TO_LEVEL[class_name]
    hover = team_item.find(class_=re.compile(r"bookmark-icon-hover"))
    if hover:
        label = clean_text(hover.get_text())
        if label:
            return label
    return ""


def parse_universities(desc_html: str) -> list[str]:
    lines = [clean_text(line) for line in re.split(r"<br\s*/?>", desc_html, flags=re.I)]
    return [line for line in lines if line]


def extract_cards(index_html: Path, lang: str) -> list[MentorRecord]:
    soup = BeautifulSoup(index_html.read_text(encoding="utf-8"), "html.parser")
    records: list[MentorRecord] = []

    for index, item in enumerate(soup.select(".team-item"), start=1):
        title_link = item.select_one(".content .title a")
        if not title_link:
            continue

        href = title_link.get("href", "")
        slug = slug_from_profile_href(href)
        name = clean_text(title_link.get_text())
        sub_title = clean_text(item.select_one(".content .sub-title").get_text()) if item.select_one(".content .sub-title") else ""
        location_text, city, country_fa = parse_location(sub_title)
        country_en = infer_country_en(country_fa, location_text)

        desc_node = item.select_one(".content p.desc")
        universities = parse_universities(desc_node.decode_contents()) if desc_node else []

        fields = [clean_text(node.get_text()) for node in item.select(".AcademicField")]
        specializations = [clean_text(node.get_text()) for node in item.select(".AcademicSpecialization")]

        img = item.select_one(".thumb img")
        image_path = img.get("data-src") or img.get("src", "") if img else ""

        degree_level = parse_degree_level(item)

        record = MentorRecord(
            id=slug,
            name=name,
            location_text=location_text or sub_title,
            current_city=city,
            current_country_fa=country_fa,
            current_country_en=country_en,
            degree_level=degree_level,
            fields=fields,
            specializations=specializations,
            universities_listed=universities,
            image_path=clean_text(image_path),
            profile_url=href,
            card_index=index,
        )
        records.append(record)

    return records


def profile_is_active(html: str) -> bool:
    lowered = html.lower()
    if 'content="noindex,nofollow"' in lowered and "this page is unavailable" in lowered:
        return False
    if 'http-equiv="refresh"' in lowered and "index.html" in lowered and "team-details-area" not in lowered:
        return False
    return "team-details-area" in lowered


def parse_education(section) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for item in section.select(".candidate-details-content .content-item"):
        title = clean_text(item.select_one(".title").get_text()) if item.select_one(".title") else ""
        institution_node = item.select_one(".sub-title")
        institution = clean_text(institution_node.get_text()) if institution_node else ""
        institution_url = institution_node.select_one("a").get("href", "") if institution_node and institution_node.select_one("a") else ""
        entries.append(
            {
                "title": title,
                "institution": institution,
                "institution_url": institution_url,
            }
        )
    return entries


def parse_sidebar_table(profile_soup: BeautifulSoup) -> dict[str, str]:
    data: dict[str, str] = {}
    for row in profile_soup.select(".summery-info tr"):
        cells = row.find_all("td")
        if len(cells) < 3:
            continue
        key = clean_text(cells[0].get_text())
        value = clean_text(cells[2].get_text())
        if key:
            data[key] = value
    return data


def enrich_from_profile(record: MentorRecord, profile_path: Path, lang: str) -> None:
    record.profile_exists = profile_path.exists()
    if not record.profile_exists:
        return

    html = profile_path.read_text(encoding="utf-8")
    record.active = profile_is_active(html)
    soup = BeautifulSoup(html, "html.parser")

    meta = soup.find("meta", attrs={"name": "description"})
    record.meta_description = clean_text(meta.get("content")) if meta else ""

    title = soup.find("title")
    if title and lang == "en":
        title_text = clean_text(title.get_text())
        match = re.search(r"Path mate\s+(.+)$", title_text, re.I)
        if match:
            record.name_en = clean_text(match.group(1))

    intro_node = soup.select_one(".team-details-item .content p.desc")
    record.intro = clean_text(intro_node.get_text()) if intro_node else ""

    header_name = soup.select_one(".team-details-info .title")
    if header_name and lang == "fa":
        record.name = clean_text(header_name.get_text()) or record.name
    if header_name and lang == "en" and not record.name_en:
        record.name_en = clean_text(header_name.get_text())

    header_sub = soup.select_one(".team-details-info .sub-title")
    if header_sub:
        sub_text = clean_text(header_sub.get_text(" ", strip=True))
        if sub_text and not record.intro:
            record.intro = sub_text

    location_node = soup.select_one(".team-details-info .info-list li")
    if location_node:
        loc = clean_text(location_node.get_text())
        if loc:
            record.location_text = loc
            _, city, country_fa = parse_location(loc)
            if city:
                record.current_city = city
            if country_fa:
                record.current_country_fa = country_fa
                record.current_country_en = COUNTRY_FA_TO_EN.get(country_fa, record.current_country_en)

    for wrap in soup.select(".candidate-details-wrap"):
        heading = wrap.select_one(".content-title")
        heading_text = clean_text(heading.get_text()) if heading else ""
        if "تحصیلات" in heading_text or heading_text.lower() == "education":
            record.education = parse_education(wrap)
        elif "تجارب" in heading_text or "سابقه" in heading_text or "experience" in heading_text.lower():
            record.work_experience = parse_education(wrap)

    sidebar = parse_sidebar_table(soup)
    if sidebar.get("Language"):
        record.languages = [clean_text(x) for x in re.split(r",|،", sidebar["Language"]) if clean_text(x)]
    record.qualification = sidebar.get("Qualification", record.qualification)
    record.experience_years = sidebar.get("Experience", record.experience_years)
    record.gender = sidebar.get("Gender", record.gender)
    record.age_range = sidebar.get("Age", record.age_range)

    img = soup.select_one(".team-details-info .thumb img")
    if img:
        record.image_path = clean_text(img.get("data-src") or img.get("src", "")) or record.image_path


def attach_english_profile_urls(records: list[MentorRecord], en_dir: Path) -> None:
    for record in records:
        en_path = en_dir / f"profile-details-{record.id}.html"
        if not en_path.exists():
            continue
        record.profile_url_en = f"profile-details-{record.id}.html"
        en_html = en_path.read_text(encoding="utf-8")
        if not profile_is_active(en_html):
            continue
        en_soup = BeautifulSoup(en_html, "html.parser")
        header_name = en_soup.select_one(".team-details-info .title")
        if header_name:
            record.name_en = clean_text(header_name.get_text())
        if not record.name_en:
            title = en_soup.find("title")
            if title:
                match = re.search(r"Path mate\s+(.+)$", clean_text(title.get_text()), re.I)
                if match:
                    record.name_en = clean_text(match.group(1))


def build_report(records: list[MentorRecord], lang: str) -> dict[str, Any]:
    missing_profiles = [r.id for r in records if not r.profile_exists]
    inactive_profiles = [r.id for r in records if r.profile_exists and not r.active]
    missing_country = [r.id for r in records if not r.current_country_en and not r.current_country_fa]
    missing_degree = [r.id for r in records if not r.degree_level]
    missing_fields = [r.id for r in records if not r.fields]
    missing_specializations = [r.id for r in records if not r.specializations]

    active_bookable = [r for r in records if r.active]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "language": lang,
        "total_cards_in_index": len(records),
        "profile_files_found": sum(1 for r in records if r.profile_exists),
        "active_profiles": len(active_bookable),
        "inactive_or_disabled_profiles": len(inactive_profiles),
        "missing_profile_files": missing_profiles,
        "inactive_profile_ids": inactive_profiles,
        "missing_country": missing_country,
        "missing_degree_level": missing_degree,
        "missing_fields": missing_fields,
        "missing_specializations": missing_specializations,
        "countries_represented": sorted({r.current_country_en for r in records if r.current_country_en}),
        "degree_levels": {
            level: sum(1 for r in records if r.degree_level == level)
            for level in sorted({r.degree_level for r in records if r.degree_level})
        },
    }


def export_language(horizon_dir: Path, lang: str, output_dir: Path) -> tuple[Path, Path]:
    lang_dir = horizon_dir / lang
    index_html = lang_dir / "index.html"
    if not index_html.exists():
        raise FileNotFoundError(f"Missing index file: {index_html}")

    records = extract_cards(index_html, lang)
    for record in records:
        profile_path = lang_dir / record.profile_url
        enrich_from_profile(record, profile_path, lang)
        record.finalize()

    if lang == "fa":
        attach_english_profile_urls(records, horizon_dir / "en")

    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"mentors.{lang}.json"
    report_path = output_dir / f"mentors.{lang}.report.json"

    payload = {
        "meta": {
            "source": str(index_html),
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "language": lang,
            "count": len(records),
        },
        "mentors": [asdict(record) for record in records],
    }

    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    report_path.write_text(
        json.dumps(build_report(records, lang), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return json_path, report_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Export Leapto mentor/path-mate data from HTML.")
    parser.add_argument("--horizon-dir", type=Path, default=DEFAULT_HORIZON, help="Path to horizon website root")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Directory for JSON output")
    parser.add_argument(
        "--lang",
        choices=("fa", "en", "both"),
        default="fa",
        help="Which language index to export (default: fa)",
    )
    args = parser.parse_args()

    langs = ["fa", "en"] if args.lang == "both" else [args.lang]
    for lang in langs:
        json_path, report_path = export_language(args.horizon_dir, lang, args.output_dir)
        report = json.loads(report_path.read_text(encoding="utf-8"))
        print(f"[{lang}] wrote {json_path}")
        print(
            f"[{lang}] cards={report['total_cards_in_index']} "
            f"active={report['active_profiles']} "
            f"missing_files={len(report['missing_profile_files'])} "
            f"inactive={len(report['inactive_profile_ids'])}"
        )
        print(f"[{lang}] report {report_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
