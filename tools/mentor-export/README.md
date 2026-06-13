# Mentor data export

Extracts Leapto path-mate cards from static HTML into structured JSON for the AI matching layer.

## Setup

```bash
cd tools/mentor-export
pip install -r requirements.txt
```

## Run

From anywhere:

```bash
python3 tools/mentor-export/extract_mentors.py
```

Options:

```bash
python3 tools/mentor-export/extract_mentors.py --lang fa
python3 tools/mentor-export/extract_mentors.py --lang en
python3 tools/mentor-export/extract_mentors.py --lang both
python3 tools/mentor-export/extract_mentors.py --horizon-dir /path/to/horizon --output-dir /path/to/data
```

## Output

| File | Description |
|------|-------------|
| `data/mentors.fa.json` | All FA index cards + enriched profile data |
| `data/mentors.fa.report.json` | Quality report (missing files, countries, etc.) |
| `data/mentors.en.json` | EN index export |
| `data/mentors.en.report.json` | EN quality report |

Each mentor record includes card data (country, field, degree), profile bio/education/work history, and a `search_text` field for semantic matching.

Re-run this script whenever mentors are added or profile pages change.
