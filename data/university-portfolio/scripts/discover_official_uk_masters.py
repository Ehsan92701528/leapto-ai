#!/usr/bin/env python3
"""Discover current taught Master's course pages on approved UK university domains.

This creates a planning inventory, not a verified 2027 publication. Extracted
facts retain their published academic year and may be incomplete.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import re
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urljoin, urlparse, urlunparse

import httpx
from bs4 import BeautifulSoup

PORTFOLIO_DIR = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = PORTFOLIO_DIR / "verified_2027" / "university_sources.csv"
DEFAULT_OUTPUT = PORTFOLIO_DIR / "planning_2027" / "discovered_programmes.csv"
DEFAULT_REPORT = PORTFOLIO_DIR / "planning_2027" / "discovery_report.json"

USER_AGENT = "LeaptoCatalogueResearch/1.0 (+https://leapto.co.uk)"
DEGREE_RE = re.compile(r"\b(MSc|M\.Sc\.?|MA|M\.A\.?|MBA|MPH|LLM|MFA|MArch|MEd|MEng|MFin|MAcc|MPhil|MSt)\b", re.I)
EXCLUDE_RE = re.compile(r"\b(undergraduate|bsc|ba\s|phd|doctorate|mres|pgcert|pgdip|short course)\b", re.I)
COURSE_URL_RE = re.compile(r"/(course|courses|postgraduate|masters?|graduate|study)/", re.I)
SKIP_URL_RE = re.compile(r"(login|apply-now|contact|events?|news|blog|privacy|terms|accessibility|\.pdf$)", re.I)
OUT_OF_SCOPE_RE = re.compile(
    r"\b(online|distance learning|bahrain|china|dubai|hong kong|malaysia|oman|qatar|singapore|uae)\b",
    re.I,
)

FAMILY_RULES: list[tuple[str, tuple[str, ...], str]] = [
    ("computing-data-ai", ("computer", "computing", "data science", "artificial intelligence", "machine learning", "cyber", "software", "information technology", "fintech", "business analytics"), "Computer Engineering & Computer Science"),
    ("business-management-finance", ("business", "management", "finance", "accounting", "marketing", "entrepreneur", "human resource", "supply chain", "project management", "mba"), "Management, Business & Industrial Engineering"),
    ("engineering-technology", ("engineering", "robotics", "renewable energy", "telecommunication", "materials", "manufacturing", "aerospace", "mechatronic", "construction"), "Mechanical, Material & Mining Engineering"),
    ("health-life-sciences", ("public health", "health", "biomedical", "biotechnology", "bioscience", "pharmacy", "clinical", "neuroscience", "nutrition", "genomic", "microbiology", "immunology"), "Life Sciences & Medicine"),
    ("economics-social-policy", ("economics", "economic", "social policy", "public policy", "international relations", "development studies", "politics", "sociology"), "Economics and Finance"),
]

OUTPUT_FIELDS = [
    "university_name_en", "city_en", "title_en", "degree_award",
    "subject_family", "leapto_category", "programme_url", "duration_months",
    "delivery_mode", "min_ielts_overall", "international_tuition_gbp",
    "tuition_evidence_status",
    "source_academic_year", "published_start_term", "application_deadline",
    "collection_status", "last_checked_at",
]


def clean_url(url: str) -> str:
    parsed = urlparse(url)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path.rstrip("/"), "", parsed.query, ""))


def host_matches(url: str, official_domain: str) -> bool:
    host = (urlparse(url).hostname or "").lower().removeprefix("www.")
    domain = official_domain.lower().removeprefix("www.")
    return host == domain or host.endswith("." + domain)


def likely_course_url(url: str, official_domain: str) -> bool:
    return (
        url.startswith("https://")
        and host_matches(url, official_domain)
        and bool(COURSE_URL_RE.search(urlparse(url).path + "/"))
        and not SKIP_URL_RE.search(url)
    )


def classify(title: str) -> tuple[str, str] | None:
    lowered = title.lower()
    scored: list[tuple[int, str, str]] = []
    for family, terms, category in FAMILY_RULES:
        score = sum(1 for term in terms if term in lowered)
        if score:
            scored.append((score, family, category))
    if not scored:
        return None
    _, family, category = max(scored)
    return family, category


def extract_title(soup: BeautifulSoup) -> str:
    h1 = soup.find("h1")
    value = h1.get_text(" ", strip=True) if h1 else ""
    if not value and soup.title:
        value = soup.title.get_text(" ", strip=True)
    value = re.sub(r"\s+", " ", value)
    value = re.split(r"\s+[|–—]\s+", value)[0].strip()
    return value


def extract_first(patterns: Iterable[re.Pattern[str]], text: str) -> str:
    for pattern in patterns:
        match = pattern.search(text)
        if match:
            return match.group(1).replace(",", "").strip()
    return ""


def extract_course(
    html: str,
    url: str,
    university: dict[str, str],
    checked_at: str,
    title_hint: str = "",
) -> dict[str, str] | None:
    soup = BeautifulSoup(html, "lxml")
    title = extract_title(soup)
    # Some universities put the award only in the catalogue card, while the
    # detail-page H1 contains just the subject name. Retain the official card
    # title so those genuine course pages are not discarded.
    if title_hint and (not DEGREE_RE.search(title) or EXCLUDE_RE.search(title)):
        title = re.sub(r"\s+", " ", title_hint).strip()
    if (
        not title
        or not DEGREE_RE.search(title)
        or EXCLUDE_RE.search(title)
        or OUT_OF_SCOPE_RE.search(title)
        or OUT_OF_SCOPE_RE.search(url.replace("-", " ").replace("_", " "))
    ):
        return None
    family = classify(title)
    if family is None:
        return None
    subject_family, category = family
    degree_match = DEGREE_RE.search(title)
    degree = degree_match.group(1).replace(".", "") if degree_match else "Master"
    text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))
    tuition = extract_first(
        (
            re.compile(r"(?:international|overseas)[^£]{0,220}(?:tuition\s+)?fees?[^£]{0,80}£\s*([0-9][0-9,]{3,})", re.I),
        ),
        text,
    )
    ielts = extract_first(
        (re.compile(r"IELTS(?:\s+Academic)?[^0-9]{0,80}([5-9](?:\.\d)?)", re.I),), text
    )
    duration = extract_first(
        (
            re.compile(r"(?:duration|full[- ]time)[^0-9]{0,40}([0-9]{1,2})\s+months?", re.I),
            re.compile(r"([0-9]{1,2})\s+months?\s+(?:full[- ]time|duration)", re.I),
        ),
        text,
    )
    source_year = extract_first(
        (re.compile(r"\b(202[5-8]\s*[/–-]\s*(?:2[6-9]|202[6-9]))\b"),), text
    ).replace(" ", "")
    start_term = extract_first(
        (re.compile(r"\b((?:September|October|January)\s+202[6-8])\b", re.I),), text
    )
    return {
        "university_name_en": university["university_name_en"],
        "city_en": university["city_en"],
        "title_en": title,
        "degree_award": degree.upper() if len(degree) <= 4 else degree,
        "subject_family": subject_family,
        "leapto_category": category,
        "programme_url": clean_url(url),
        "duration_months": duration,
        "delivery_mode": "on_campus",
        "min_ielts_overall": ielts,
        "international_tuition_gbp": tuition,
        "tuition_evidence_status": "unreviewed_regex" if tuition else "missing",
        "source_academic_year": source_year,
        "published_start_term": start_term,
        "application_deadline": "",
        "collection_status": "latest_official_page",
        "last_checked_at": checked_at,
    }


class Crawler:
    def __init__(self, timeout: float, workers: int):
        self.client = httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xml;q=0.9,*/*;q=0.8"},
        )
        self.workers = workers
        self.title_hints: dict[str, str] = {}

    def close(self) -> None:
        self.client.close()

    def get(self, url: str) -> tuple[str, str, int]:
        try:
            response = self.client.get(url)
            if response.status_code >= 400:
                return "", str(response.url), response.status_code
            content = response.content
            if str(response.url).endswith(".gz"):
                content = gzip.decompress(content)
            return content.decode(response.encoding or "utf-8", errors="replace"), str(response.url), response.status_code
        except Exception:
            return "", url, 0

    def sitemap_urls(self, university: dict[str, str], maximum_sitemaps: int = 6) -> set[str]:
        base = "https://" + university["official_domain"].removeprefix("www.")
        sitemap_queue = [base + "/sitemap.xml", base + "/sitemap_index.xml"]
        robots, _, _ = self.get(base + "/robots.txt")
        for line in robots.splitlines():
            if line.lower().startswith("sitemap:"):
                sitemap_queue.append(line.split(":", 1)[1].strip())
        seen_maps: set[str] = set()
        candidates: set[str] = set()
        while sitemap_queue and len(seen_maps) < maximum_sitemaps:
            sitemap = sitemap_queue.pop(0)
            if sitemap in seen_maps:
                continue
            seen_maps.add(sitemap)
            xml, final_url, _ = self.get(sitemap)
            if not xml:
                continue
            try:
                root = ET.fromstring(xml)
            except ET.ParseError:
                continue
            locations = [element.text.strip() for element in root.iter() if element.tag.endswith("loc") and element.text]
            if root.tag.endswith("sitemapindex"):
                focused = [loc for loc in locations if re.search(r"course|study|postgraduate|master", loc, re.I)]
                sitemap_queue.extend(focused or locations[:maximum_sitemaps])
            else:
                for loc in locations:
                    if likely_course_url(loc, university["official_domain"]):
                        candidates.add(clean_url(loc))
        return candidates

    def catalogue_links(self, university: dict[str, str], maximum_listing_pages: int = 60) -> tuple[set[str], int]:
        links: set[str] = set()
        if university["official_domain"].removeprefix("www.") == "manchester.ac.uk":
            feed_url = "https://www.manchester.ac.uk/study/masters/courses/list/json/?level=pgt"
            payload, _, status = self.get(feed_url)
            try:
                course_ids = json.loads(payload).get("i", [])
            except (json.JSONDecodeError, AttributeError):
                course_ids = []
            links.update(
                f"https://www.manchester.ac.uk/study/masters/courses/list/{course_id}/"
                for course_id in course_ids
            )
            return links, status
        queue = [university["postgraduate_catalogue_url"]]
        seen: set[str] = set()
        first_status = 0
        catalogue_path = urlparse(university["postgraduate_catalogue_url"]).path.rstrip("/")
        while queue and len(seen) < maximum_listing_pages:
            listing_url = queue.pop(0)
            if listing_url in seen:
                continue
            seen.add(listing_url)
            html, final_url, status = self.get(listing_url)
            if first_status == 0:
                first_status = status
            if not html:
                continue
            soup = BeautifulSoup(html, "lxml")
            for anchor in soup.find_all("a", href=True):
                raw_href = anchor["href"]
                url = clean_url(urljoin(final_url, raw_href))
                if likely_course_url(url, university["official_domain"]):
                    links.add(url)
                    anchor_title = anchor.get_text(" ", strip=True)
                    if DEGREE_RE.search(anchor_title):
                        self.title_hints[url] = anchor_title
                parsed = urlparse(url)
                if (
                    host_matches(url, university["official_domain"])
                    and parsed.path.rstrip("/") == catalogue_path
                    and re.search(r"(?:^|[?&])(page|p)=\d+", url, re.I)
                    and url not in seen
                ):
                    queue.append(url)
        return links, first_status

    def discover_university(
        self, university: dict[str, str], *, maximum_candidates: int, maximum_courses: int,
        use_sitemaps: bool,
    ) -> tuple[list[dict[str, str]], dict[str, Any]]:
        started = time.monotonic()
        checked_at = datetime.now(timezone.utc).isoformat()
        direct, catalogue_status = self.catalogue_links(university)
        sitemap = self.sitemap_urls(university) if use_sitemaps else set()
        # Catalogue links are the strongest identities and should never be
        # displaced by thousands of broad sitemap URLs.
        candidates = (sorted(direct) + sorted(sitemap - direct))[:maximum_candidates]
        found: list[dict[str, str]] = []
        failures = 0
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {executor.submit(self.get, url): url for url in candidates}
            for future in as_completed(futures):
                html, final_url, status = future.result()
                if not html:
                    failures += 1
                    continue
                course = extract_course(
                    html,
                    final_url,
                    university,
                    checked_at,
                    self.title_hints.get(clean_url(final_url), self.title_hints.get(futures[future], "")),
                )
                if course:
                    found.append(course)
        unique: dict[tuple[str, str], dict[str, str]] = {}
        for row in sorted(found, key=lambda item: (item["title_en"], item["programme_url"])):
            unique.setdefault((row["title_en"].lower(), row["programme_url"]), row)
        courses = list(unique.values())[:maximum_courses]
        report = {
            "university": university["university_name_en"],
            "catalogue_status": catalogue_status,
            "direct_links": len(direct),
            "sitemap_links": len(sitemap),
            "candidate_pages_checked": len(candidates),
            "fetch_failures": failures,
            "courses_found": len(courses),
            "elapsed_seconds": round(time.monotonic() - started, 1),
        }
        return courses, report


def read_registry(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_course_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(sorted(rows, key=lambda row: (row["university_name_en"], row["title_en"])))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--university", action="append", help="Exact university name; repeat to select several")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--limit-universities", type=int)
    parser.add_argument("--max-candidates-per-university", type=int, default=350)
    parser.add_argument("--max-courses-per-university", type=int, default=100)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--use-sitemaps", action="store_true", help="Use only for sites whose sitemap is known to respond quickly")
    parser.add_argument("--append", action="store_true", help="Merge results into an existing output CSV")
    args = parser.parse_args()

    universities = read_registry(args.registry)
    if args.university:
        selected = set(args.university)
        universities = [row for row in universities if row["university_name_en"] in selected]
    if args.limit_universities:
        universities = universities[: args.limit_universities]
    crawler = Crawler(args.timeout, args.workers)
    all_courses: list[dict[str, str]] = []
    if args.append and args.output.exists():
        with args.output.open(encoding="utf-8-sig", newline="") as handle:
            all_courses = list(csv.DictReader(handle))
    reports: list[dict[str, Any]] = []
    try:
        for index, university in enumerate(universities, start=1):
            print(f"[{index}/{len(universities)}] {university['university_name_en']}", flush=True)
            courses, report = crawler.discover_university(
                university,
                maximum_candidates=args.max_candidates_per_university,
                maximum_courses=args.max_courses_per_university,
                use_sitemaps=args.use_sitemaps,
            )
            existing_keys = {(row["university_name_en"], row["programme_url"]) for row in all_courses}
            all_courses.extend(
                row for row in courses
                if (row["university_name_en"], row["programme_url"]) not in existing_keys
            )
            reports.append(report)
            write_course_csv(args.output, all_courses)
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(
                json.dumps({
                    "status": "running",
                    "universities_completed": len(reports),
                    "universities_total": len(universities),
                    "courses_found": len(all_courses),
                    "universities": reports,
                }, indent=2),
                encoding="utf-8",
            )
            print(f"  found {report['courses_found']} courses from {report['candidate_pages_checked']} pages", flush=True)
    finally:
        crawler.close()

    all_courses.sort(key=lambda row: (row["university_name_en"], row["title_en"]))
    write_course_csv(args.output, all_courses)
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "universities_attempted": len(universities),
        "universities_with_courses": sum(1 for row in reports if row["courses_found"]),
        "courses_found": len(all_courses),
        "with_tuition": sum(1 for row in all_courses if row["international_tuition_gbp"]),
        "with_ielts": sum(1 for row in all_courses if row["min_ielts_overall"]),
        "with_published_start_term": sum(1 for row in all_courses if row["published_start_term"]),
        "subject_family_counts": {
            family: sum(1 for row in all_courses if row["subject_family"] == family)
            for family, _, _ in FAMILY_RULES
        },
        "universities": reports,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0 if all_courses else 2


if __name__ == "__main__":
    raise SystemExit(main())
