# Deploy Leapto AI on the same server as the website

One VPS or dedicated box can run **both**:

- **horizon** — static HTML (already on `leapto.co.uk`)
- **leapto-ai** — Python API on localhost, exposed via nginx

```
Browser  →  https://leapto.co.uk/fa/     →  nginx → static files (horizon)
Browser  →  https://api.leapto.co.uk/    →  nginx → 127.0.0.1:8080 (uvicorn)
```

Both hostnames can point to the **same IP** (two DNS A records).

---

## 1. Clone on the server

```bash
sudo mkdir -p /srv/leapto
sudo chown "$USER" /srv/leapto
cd /srv/leapto

git clone git@github.com:Ehsan92701528/horizon.git
git clone git@github.com:Ehsan92701528/leapto-ai.git   # after you create & push this repo
```

Deploy website files from `horizon/` to your existing web root (same as today).  
Keep `leapto-ai` at e.g. `/srv/leapto/leapto-ai`.

---

## 2. Install API dependencies

```bash
cd /srv/leapto/leapto-ai/api/pathmate-matcher
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Ensure programme cache exists (committed in repo, or rebuild):
python3 ../../data/university-portfolio/scripts/build_global_portfolio_cache.py
```

Optional: `cp .env.example .env` and add `LEAPTO_AI_API_KEY` for LLM features.

---

## 3. Run API with systemd (survives reboot)

Copy and edit the service file:

```bash
sudo cp /srv/leapto/leapto-ai/deploy/leapto-ai-api.service.example \
  /etc/systemd/system/leapto-ai-api.service
# Edit User= and paths if needed
sudo systemctl daemon-reload
sudo systemctl enable --now leapto-ai-api
sudo systemctl status leapto-ai-api
curl -s http://127.0.0.1:8080/health/ai
```

---

## 4. nginx — reverse proxy for `api.leapto.co.uk`

Add a **new server block** (do not replace the main site block):

```bash
sudo cp /srv/leapto/leapto-ai/deploy/nginx-api.leapto.co.uk.conf.example \
  /etc/nginx/sites-available/api.leapto.co.uk
sudo ln -sf /etc/nginx/sites-available/api.leapto.co.uk /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

DNS: create **A record** `api.leapto.co.uk` → same server IP as `leapto.co.uk`.

TLS (Let's Encrypt):

```bash
sudo certbot --nginx -d api.leapto.co.uk
```

---

## 5. CORS and widget

The API allows all origins today (`CORSMiddleware allow_origins=["*"]`), so the static site on `leapto.co.uk` can call `https://api.leapto.co.uk`.

After deploy, open `https://leapto.co.uk/fa/index.html` (or `/en/`), hard-refresh, run the path-mate widget.  
DevTools → Network should show `POST https://api.leapto.co.uk/match`.

---

## 6. Updates

**Website:**

```bash
cd /srv/leapto/horizon && git pull
# copy/sync to web root as you do today
```

**API:**

```bash
cd /srv/leapto/leapto-ai && git pull
source api/pathmate-matcher/.venv/bin/activate
pip install -r api/pathmate-matcher/requirements.txt
sudo systemctl restart leapto-ai-api
```

---

## 7. Resource note

The API is lightweight (FastAPI + JSON files). On a small VPS, 512MB–1GB RAM is usually enough alongside nginx and static hosting. Programme cache ~3MB on disk.

---

## Alternative: API on a path (no subdomain)

If you prefer `https://leapto.co.uk/api/` instead of `api.leapto.co.uk`, nginx can proxy `/api/` to uvicorn and you must set in horizon's `pathmate-finder.config.js`:

```javascript
apiBaseUrl: "https://leapto.co.uk/api"
```

Subdomain is simpler (no path prefix changes in FastAPI).
