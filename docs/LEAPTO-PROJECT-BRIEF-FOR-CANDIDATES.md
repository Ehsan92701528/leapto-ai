# Leapto — Project Brief & Scope

**Document purpose:** Share with candidates (advisors, co-builders, senior hires)  
**Organisation:** Leapto · [leapto.co.uk](https://leapto.co.uk)  
**Version:** 1.0  
**Date:** June 2026  
**Confidential:** For discussion under mutual interest only

---

## 1. One-page summary

**Leapto** is a hybrid **AI + human marketplace** for international university admissions.

We help students who want to study abroad by:

1. **Understanding their profile** — background, grades, exams (IELTS, GRE, etc.), budget, and goals  
2. **Building a realistic university portfolio** — reach, match, and safety programmes aligned to their potential  
3. **Connecting them to verified graduate mentors** — 260+ alumni who have already walked a similar path  
4. **Supporting applications end-to-end** — guidance, essay quality, and (on the roadmap) reducing the administrative burden of applying to multiple universities  

Parents and students already spend **thousands** on consultants. Leapto aims to deliver **better outcomes at lower friction** by combining governed AI with a mentor network we have already built — not starting from zero on supply.

**Our edge:** Most competitors stop at “here’s your list” or a generic AI essay. We combine **data-backed portfolio design**, a **live mentor marketplace**, and a long-term bet on **application automation** — while keeping humans in the loop where it matters (authenticity, strategy, accountability).

---

## 2. The problem we solve

| Pain | Today’s reality |
|------|------------------|
| **Information overload** | Hundreds of programmes, changing requirements, opaque “chances” |
| **Expensive consultants** | Premium firms charge £10k–£50k+; out of reach for many families |
| **Generic AI tools** | Chatbots invent requirements or produce detectable AI essays — risky in 2026 admissions |
| **Mentor discovery** | Hard to find someone who actually studied your target degree in your target country |
| **Application fatigue** | Students re-enter the same data across UCAS, institution portals, and country-specific systems |

Leapto addresses the full journey: **clarity → portfolio → people → applications** — not just one step.

---

## 3. How Leapto works (target end-to-end flow)

```
Student shares profile & goals (conversation or structured intake)
        ↓
AI + rules analyse fit → university & subject portfolio (reach / match / safety)
        ↓
Student refines list with graduate mentors (1:1 or packaged sessions)
        ↓
Application support: checklists, documents, essays (mentor-polished, not generic AI)
        ↓
[Future] Secure assisted application filling across major portals
        ↓
Offers, decisions, and ongoing mentor support where needed
```

**Principle:** AI for **scale, structure, and search**; mentors for **judgment, authenticity, and trust**.

---

## 4. The three pillars (product & positioning)

### Pillar 1 — AI portfolio & university matching

**What it is:** Given GPA, language scores, field, budget, and preferences, the platform recommends a **portfolio of programmes** with transparent reasoning — not a black-box “fit score” alone.

**Market reality:** Many players (Leap Scholar, Leverage Edu, CollegeFit, Unive.ai, AbroBot, etc.) offer profile-to-university matching. **Matching alone is crowded.**

**Leapto approach:**  
- Ground recommendations in a **structured programme database** (tuition, IELTS, field, URLs, verification dates)  
- Show **reach / match / safety** buckets — the same framing serious counselors use  
- Bilingual **Persian and English** — core audience for leapto.co.uk  
- **No hallucinated entry requirements** — if we don’t have data, we say so  

**Stage today:** Working prototype — mentor matcher, portfolio matcher, conversational programme chat, ~3,000 MSc programme records (UK-weighted seed data expanding toward verified imports).

---

### Pillar 2 — 260+ graduate mentor network (supply-side moat)

**What it is:** Verified alumni (“path mates”) who offer **paid** short or long-form advisory time — strategy calls, essay reviews, country-specific guidance, portfolio sanity-checks.

**Market reality:** Startups often fail the **chicken-and-egg** problem (no mentors without students). Leapto **already has 260+ mentors** exported from the live site, with profiles across countries and fields (UK, Canada, Germany, US, and others).

**Why it matters:**  
- Trust: “Someone like me got into Manchester / HEC / TU Munich”  
- Anti-AI-essay trap: mentors **polish and humanise** application writing — universities increasingly reject generic AI SOPs  
- **Micro-consulting:** Students can buy 1-hour reviews or deeper packages instead of £10k retainers upfront  

**Stage today:** Live mentor profiles on leapto.co.uk; path-mate matching widget (rule-based, bilingual); booking flows via existing Leapto commerce infrastructure.

---

### Pillar 3 — Application filling & admin automation (strategic differentiator)

**What it is:** Student enters details **once**; the platform helps complete repetitive application forms across international systems (UCAS, direct university PG portals, and others over time).

**Market reality:** Most EdTech stops at **checklists and essays**. Students still manually re-type data into multiple portals. **This is the “tired of forms” opportunity.**

**Leapto vision (marketing angle):**  
*“Give us your details once — we help you apply to your chosen universities with far less admin.”*

**Stage today:** **Roadmap / R&D priority** — not yet in production. Requires careful design for security, consent, portal terms of service, and human confirmation before submission. Portfolio design and mentor support come first.

---

## 5. Competitive landscape (honest map)

| Player type | Examples | What they do well | Gap Leapto fills |
|-------------|----------|-------------------|------------------|
| **Large study-abroad brands** | Leap Scholar, Leverage Edu | Scale, brand, counselor networks | Often generic; less peer-mentor authenticity; weak on admin automation |
| **AI-native admissions** | Unive.ai, AbroBot | Predictive fit, strategy timelines | Less emphasis on verified peer mentors; essay authenticity risk |
| **Premium mentorship** | Crimson Education | Top-university mentors, high touch | £10k–£50k+ — inaccessible; not marketplace-flexible |
| **Fit-score tools** | CollegeFit, MyChance, Aspiria | Quick % fit | Commodity; no human network or application execution |

**Where Leapto does not try to win (v1):**  
- Visa or immigration **legal** advice via AI  
- Fully autonomous “AI applies without you” with no human review  
- Generic ChatGPT essays with no mentor review  

**Where Leapto can win:**  
- **Hybrid AI + 260 mentors** in one product  
- **Persian/English** and diaspora trust  
- **Portfolio + mentors + (future) form automation** in one journey  
- **Micro-payments** for mentor time vs. only high-ticket consulting  

---

## 6. Business model (current direction)

| Revenue stream | Description |
|----------------|-------------|
| **Mentor sessions** | 1, 2, or packs of sessions; mentors paid; platform fee |
| **Application packs** | Bundles (e.g. 5 or 10 university applications supported) — planned |
| **Advisory tiers** | Deeper packages combining portfolio + mentor hours + document support |
| **Future** | Stripe checkout → order → fulfilment; integration with accounting (e.g. Xero) |

Lower **barrier to entry** than traditional consultants: start with one affordable mentor call, expand as trust builds.

---

## 7. Project scope — what we are building **at this stage**

This section defines **current phase scope** (approx. next 6–12 months). Share this with candidates so expectations are clear.

### In scope (Phase 1 — now → near term)

| # | Capability | Status |
|---|------------|--------|
| 1 | Bilingual website (FA/EN) with mentor directory | **Live** |
| 2 | Conversational path-mate finder (intake → mentor match) | **Built**; deploying with API |
| 3 | University programme portfolio (reach / match / safety) | **Built** (data expanding) |
| 4 | Programme Q&A chat grounded in database | **Built** |
| 5 | Governed AI extraction (rules + optional LLM, validated) | **Built** |
| 6 | Programme database growth (UK focus → verified imports) | **In progress** |
| 7 | API on same server as website (`api.leapto.co.uk`) | **Deploying** |
| 8 | Mentor marketplace monetisation (sessions, packages) | **Partially live**; packaging improving |
| 9 | Essay / document workflow with **mentor review** (not raw AI essays) | **Process + product design** |

### On the roadmap (Phase 2 — next)

| # | Capability |
|---|------------|
| 10 | Full conversation agent (Zapier-style UX) with tool calling |
| 11 | PostgreSQL programme & university database at scale |
| 12 | Semantic search over mentors and programmes |
| 13 | Quote & checkout (Stripe) for session and application packs |
| 14 | Application checklist and document assembly per programme |

### Strategic bet (Phase 3 — differentiation)

| # | Capability |
|---|------------|
| 15 | Secure, consent-based **application form assistance** across major portals |
| 16 | Human-in-the-loop submission approval |
| 17 | Analytics on portfolio → offer outcomes (with consent) |

### Explicitly out of scope (for now)

- AI-generated visa or immigration legal advice  
- Unreviewed autonomous application submission  
- Training on private student chats without consent  

---

## 8. Technology (high level — for candidate context)

| Layer | Approach |
|-------|----------|
| **Website** | Static FA/EN site (horizon repo); FTP deploy to OVH |
| **API** | Python FastAPI — matching, extraction, programme chat (leapto-ai repo) |
| **Data** | Mentor JSON from site; programme cache → future PostgreSQL |
| **AI** | Rules-first; optional LLM with validation, citations, eval tests |
| **Hosting** | OVH Cloud — single server, `leapto.co.uk` + `api.leapto.co.uk` |

Technical architecture detail is available separately for due diligence.

---

## 9. Why now

- **Market size:** Global international student mobility is multi-billion; families pay heavily for edge.  
- **AI shift:** Students will use AI anyway — Leapto channels that into **governed tools + human mentors** instead of risky shortcuts.  
- **Admissions backlash:** Universities penalise generic AI writing — **mentor-polished** applications are a defensible model.  
- **Supply advantage:** **260+ mentors** is rare at this stage for a startup.  
- **Product foundation:** Matching, portfolio, and chat prototypes exist — this is execution and scale, not a slide deck only.

---

## 10. What we look for in collaborators

Depending on role, we value experience in some combination of:

- EdTech, marketplaces, or two-sided platforms (supply + demand)  
- AI product management with **responsible AI** and eval discipline  
- International admissions, counseling, or university partnerships  
- Full-stack or API engineering (Python, data pipelines)  
- Growth in Persian/English diaspora or UK/EU international student markets  

---

## 11. Mentor network (supply snapshot)

| Metric | Approximate value |
|--------|-------------------|
| Mentors on platform | **260+** (262 EN profiles in export) |
| Active for matching | **214+** |
| Coverage | Multi-country — UK, Canada, Germany, US, and others |
| Profile depth | Education, work history, specialisations, booking links |

Mentors are **paid** for their time; Leapto provides discovery, matching, and commercial infrastructure.

---

## 12. Summary — is this the project scope?

**Yes.** At this stage Leapto is:

1. **A mentor marketplace** with real supply (260+ graduates)  
2. **An AI-assisted portfolio builder** for university/programme selection  
3. **A path to application support** — human-first now, automation as the long-term differentiator  

We are **not** claiming to be finished. We are building the hybrid platform described above, with Phase 1 live or in deployment and Phases 2–3 on a clear roadmap.

---

## 13. Discussion questions (for candidate conversations)

1. Which pillar excites you most — matching, mentors, or application automation?  
2. What would you ship in the first 90 days?  
3. How would you grow verified programme data for UK Master’s (partnerships vs. scraping vs. licensed feeds)?  
4. How do we price mentor micro-sessions vs. application packs without undercutting mentor earnings?  
5. What responsible-AI guardrails would you insist on before scaling LLM features?

---

## 14. Contact & materials

| Item | Location |
|------|----------|
| Public site | https://leapto.co.uk |
| Website repo | github.com/Ehsan92701528/horizon |
| AI/API repo | github.com/Ehsan92701528/leapto-ai |
| Technical architecture | `docs/LEAPTO-AI-SYSTEM-ARCHITECTURE.md` |

**[Insert your name, role, and email for candidate follow-up]**

---

*End of brief*
