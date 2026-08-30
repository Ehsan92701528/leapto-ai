# September 2027 planning catalogue

This is the working inventory requested before universities publish complete
2027/28 details. It uses current official university pages and keeps the
published source year on every extracted fact.

It must be labelled **planning data** in the product. A 2026/27 fee or intake
must not be displayed as a confirmed 2027 fact.

Run a small discovery batch:

```bash
python3 scripts/discover_official_uk_masters.py --limit-universities 2
```

Run the full 40-university collection:

```bash
python3 scripts/discover_official_uk_masters.py
```

The output contains official course URLs plus any tuition, IELTS, duration,
academic-year and start-term facts that can be extracted safely from the page.
Missing values stay empty and are reported; they are never guessed.

