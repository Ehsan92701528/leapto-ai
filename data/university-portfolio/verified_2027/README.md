# Verified UK taught Master's catalogue — September 2027

This directory is the governed replacement for the synthetic programme cache.
It is deliberately separate from `seed/` and `cache/portfolio_global_msc.json`:
prototype rows must never be presented as verified 2027 application options.

## Scope

- September 2027 taught Master's courses
- 30–40 UK universities
- five subject families
- target of approximately 1,000 publishable courses
- official university sources only

The five initial subject families are:

1. Computing, data and AI
2. Business, management and finance
3. Engineering and technology
4. Health and life sciences
5. Economics and social policy

## Workflow

1. `university_sources.csv` defines the approved institutions and official domains.
2. Researchers place normalised CSVs in `incoming/`.
3. The publishing gate checks completeness, source ownership, freshness, intake,
   fees, requirements and cross-file consistency.
4. Only a zero-error run may create a candidate-facing JSON cache.

```bash
python3 scripts/verify_uk_masters_2027.py \
  --data-dir verified_2027/incoming \
  --source-registry verified_2027/university_sources.csv \
  --policy verified_2027/catalogue_policy.json \
  --report-json verified_2027/reports/latest.json
```

To publish after the catalogue contains verified rows:

```bash
python3 scripts/verify_uk_masters_2027.py \
  --data-dir verified_2027/incoming \
  --source-registry verified_2027/university_sources.csv \
  --policy verified_2027/catalogue_policy.json \
  --min-programmes 1 \
  --output-json cache/portfolio_gb_msc_verified_2027.json
```

The publication command fails closed: no output is produced when any validation
error exists. `source_status` in the registry describes collection readiness;
it does not imply that any individual programme has been verified.

