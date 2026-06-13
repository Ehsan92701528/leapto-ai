# CSV import templates (Phase A)

Fill these files and import with:

```bash
python3 data/university-portfolio/scripts/import_programmes.py --dry-run path/to/*.csv
```

## Order

1. `countries.csv`
2. `leapto_field_tags.csv`
3. `universities_import.csv`
4. `programmes_import.csv`
5. `programme_requirements_import.csv`
6. `programme_costs_import.csv`
7. `intakes_import.csv`

Every row must include `source_url` and ideally `last_verified_at` (ISO date).
