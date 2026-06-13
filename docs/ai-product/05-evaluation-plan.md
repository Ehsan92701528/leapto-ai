# Evaluation Plan — Leapto AI

## Purpose

Prove probabilistic AI features are **fit to release** — same mindset as Infosys/Barclays AI PO roles require.

## Suites

| Suite | Gold set | Primary metrics | Release gate |
|-------|----------|-----------------|--------------|
| **Intent** | `eval/intake_gold_set.json` | Intent accuracy | ≥ 90% |
| **Extraction** | Same file | Country F1, field exact match | F1 ≥ 85%, field ≥ 80% |
| **RAG** | `eval/rag_gold_set.json` | Citation accuracy, abstain correctness | ≥ 95% |

## Run

```bash
cd api/pathmate-matcher
python3 eval/run_eval.py              # intake suites
python3 eval/run_eval.py --suite rag
python3 eval/run_eval.py --suite all
```

## Intent labels

`study_abroad` · `work_abroad` · `alternatives_to_study` · `emigration_explore` · `unclear`

## Extraction fields scored

- `destination_countries` — set F1 (per case)
- `field_of_study` — exact or mapped match
- `target_degree` — exact
- `path_intent` — exact

## RAG scoring

Each case has:

- `question` — user query (FA or EN)
- `expect_programme_ids` — must appear in citations (or empty if abstain)
- `expect_abstain` — true if no programme should be claimed

**Pass:** All expected IDs cited AND no extra fabricated programmes when abstain expected.

## Human evaluation (monthly)

Sample 30 live or staged sessions:

| Dimension | Scale |
|-----------|-------|
| Match relevance | 1–5 |
| Conversation naturalness | 1–5 |
| Trust / would book mentor | Yes/No |

## Continuous improvement

| Signal | Action |
|--------|--------|
| Eval regression on PR | Block merge |
| Funnel drop at step X | UX backlog item |
| Intent `unclear` rate ↑ | Add gold cases + rules |
| RAG abstain rate ↑ | Data coverage review |

## Adding cases

1. Add row to gold JSON with `id`, input, `expected` block
2. Run eval locally
3. Fix rules/prompt until pass
4. Commit gold + code together
