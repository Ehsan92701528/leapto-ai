# Leapto AI — Program Charter

**Version:** 0.1 · **Owner:** Product (Leapto) · **Last updated:** 2026-05-28

## Engagement summary

| Field | Value |
|-------|--------|
| **Product** | Leapto — peer mentoring & international education mobility |
| **Business problem** | Students struggle to find relevant mentors and programmes; static filters and long forms cause drop-off and low trust |
| **Primary users** | Persian/English-speaking students exploring study, work, or both abroad |
| **Secondary users** | Mentors (supply), operations (quality & support) |
| **Constraints** | Advice-adjacent domain; multilingual; limited ML budget; must work without LLM in v1 |

## Product vision

**Help every student reach the right human path and the right programme — through a governed conversational experience that is grounded in verified data, not guesses.**

## Success metrics (12-month)

| Metric | Target | Notes |
|--------|--------|-------|
| Intake completion rate | ≥ 65% | From first message to match request |
| Median time-to-match | ≤ 90s | Including conversational steps |
| Match relevance (human sample) | ≥ 4.0 / 5 | Quarterly sample of 30 sessions |
| Unsafe / ungrounded AI responses | 0 in prod | Blocked or escalated |
| Programme answer citation accuracy | ≥ 95% | RAG eval gold set |

## Stakeholders

| Stakeholder | Interest |
|-------------|----------|
| **Students** | Fast, trustworthy guidance in FA/EN |
| **Mentors** | Qualified leads, not spam |
| **Operations** | Explainability, escalation paths |
| **Data** | Fresh mentor + programme corpus |
| **Risk / RAI** | No harmful advice; audit trail |

## Decision principles

1. **Rules before models** — ship deterministic MVP; add LLM only with eval gates.
2. **Ground or block** — programme facts from DB rows only; no invented requirements.
3. **Human path always available** — book session / mentor escalation.
4. **Same schema everywhere** — `StudentIntake` is the contract between UI, AI, and matchers.

## Out of scope (v1)

- Visa/legal advice via generative AI
- Autonomous booking or payments
- Training on live user chats without consent
- Medical or financial product recommendations
