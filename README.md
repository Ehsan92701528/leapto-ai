# Leapto AI API

Backend for the Leapto path-mate widget: mentor matching, programme portfolio, governed extraction, and conversational programme chat.

**Website (static):** [Ehsan92701528/horizon](https://github.com/Ehsan92701528/horizon)  
**This repo:** API + data + eval + product docs

## Quick start (local)

```bash
cd api/pathmate-matcher
python3 -m pip install -r requirements.txt
python3 -m uvicorn main:app --host 127.0.0.1 --port 8080
```

Health: http://127.0.0.1:8080/health/ai

With the horizon site locally, the widget auto-calls `http://127.0.0.1:8080`.

## Same server as the website

You do **not** need a second machine. Typical setup:

| Service | How |
|---------|-----|
| Static site (`horizon`) | nginx serves files for `leapto.co.uk` |
| This API | uvicorn on `127.0.0.1:8080`, nginx proxies `api.leapto.co.uk` → API |

See **[docs/DEPLOY-SAME-SERVER.md](docs/DEPLOY-SAME-SERVER.md)** for nginx + systemd steps.

The widget already uses `https://api.leapto.co.uk` when the page is on `leapto.co.uk` (`pathmate-finder.config.js` in horizon).

## Layout

```
api/pathmate-matcher/     FastAPI app
data/                     mentors JSON, programme cache
docs/ai-product/          product / RAI / roadmap docs
tools/mentor-export/      regenerate mentor JSON from horizon HTML
scripts/                  dev helpers
.github/workflows/        CI eval gates
```

## Eval

```bash
cd api/pathmate-matcher
python3 eval/run_eval.py --suite all
```

## Optional LLM

Copy `api/pathmate-matcher/.env.example` → `.env` and set `LEAPTO_AI_API_KEY`. Never commit `.env`.
