# Leapto Product v2 — Vision (conversation-first + flexible commerce)

**Status:** Direction for total FE/BE rework · **Date:** 2026-06

---

## Why v2

The current path-mate widget is a **rule-based wizard** (chips + fixed steps). It does not feel like the **Zapier-style conversation** you want: clarify goals, propose options, handle objections, confirm before action.

**Data:** UK portfolio now targets **1,000 programmes** in seed cache (plus other countries). Seed rows are for product/dev — replace with verified imports over time.

---

## Target experience (like your Zapier chat)

| Zapier pattern | Leapto equivalent |
|----------------|-------------------|
| User states goal in natural language | «می‌خوام MSc تو انگلیس، بودجه محدود، دو جلسه با منتور» |
| Assistant clarifies blockers & options | «برای Xero نیاز به paid plan دارید» → «برای منتور می‌تونیم ۱ یا ۲ جلسه بگیریم» |
| Proposes a workflow / package | «پیشنهاد: ۳ هم‌مسیر + ۵ اپلای + ۲ جلسه — £X» |
| User confirms one step to test | «اول یک invoice / یک جلسه / یک اپلای تست کنیم» |
| Executes with tools | Match mentors, portfolio, book session, (later) create Stripe checkout |

**Architecture:**

```text
User message
    → Conversation agent (LLM + system prompt + tools)
    → Tools (always grounded):
         extract_intake, match_mentors, match_portfolio, rag_programmes,
         quote_package, create_checkout_session
    → Validated state (StudentIntake + Cart)
    → Human confirm for money / applications
```

Rules engine stays as **fallback** and **validation layer** — not the primary UX.

---

## Flexible pricing (your requirements)

### Product units (SKUs)

| Unit | Default | Configurable |
|------|---------|--------------|
| Mentor sessions | 1 | 1, 2, pack of 5 |
| Session scheduling | Single | Back-to-back or separate dates |
| University applications (future) | 5 | 3, 5, 10, custom |
| Portfolio report | Included | Add-on |
| Unipass / full service | Tiered | Custom quote |

### Commerce model

1. **`ProductCatalog`** in API — base prices, bundles, min/max quantities  
2. **`POST /quote`** — intake + user choices → line items + total (no payment yet)  
3. **`POST /checkout`** — Stripe Checkout Session with metadata → Xero invoice on `checkout.session.completed`  
4. **Widget** — agent offers quote in chat; user taps «Pay» or «Book free intro»

Example cart JSON:

```json
{
  "line_items": [
    { "sku": "mentor_session", "qty": 2, "mentor_id": "kaveh-numvar" },
    { "sku": "application_pack", "qty": 10, "variant": "standard" }
  ],
  "currency": "GBP"
}
```

### Stripe ↔ Xero (your separate need)

| Approach | When |
|----------|------|
| **Zapier** (1 invoice test) | Quick validation; needs paid plan for Xero |
| **Stripe + Xero native** | If available on your Stripe/Xero accounts |
| **Own webhook** | `checkout.session.completed` → create Xero invoice via API (best long-term for Leapto) |

Recommend: **one test transaction** via Stripe Dashboard → manual Xero entry first, then automate webhook once fields map correctly.

---

## v2 build phases

### Phase A — Data (now)
- [x] UK **1,000** programmes in `portfolio_global_msc.json`
- [ ] Verified UK CSV import pipeline (replace seed over time)
- [ ] Full-text search index for RAG at 1k+ scale

### Phase B — Conversation core (4–6 weeks)
- [ ] Replace chip wizard with **single thread UI**
- [ ] LLM agent with tools: extract, match, portfolio, quote
- [ ] Confirm gates before payment / applications
- [ ] Keep `run_eval.py` as regression suite

### Phase C — Commerce (3–4 weeks)
- [ ] `ProductCatalog` + `/quote` + Stripe Checkout
- [ ] Webhook → order record + email
- [ ] Stripe → Xero invoice sync (webhook or Zapier)

### Phase D — Applications automation (later)
- [ ] Application pack SKU (5 default, 10 custom)
- [ ] Human-in-the-loop before submit

---

## What to claim today vs after v2

| Today (v1) | After v2 |
|------------|----------|
| Rule-based chat + API extract/RAG | Agent conversation + tools |
| Fixed mentor booking link | Configurable session packs |
| Portfolio tab | Quote + checkout in chat |
| 1,000 UK seed programmes | Same + verified data path |

---

## Immediate next step for you

1. Restart API → confirm `health/portfolio` shows **~1,560** programmes (1000 UK + others)  
2. Decide: **Phase B first** (conversation) or **Phase C first** (Stripe quote for 1–2 sessions)  
3. For Stripe/Xero: export **one** Stripe invoice PDF + create **one** manual Xero invoice to lock field mapping before automation
