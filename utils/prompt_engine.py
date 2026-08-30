"""
Prompt engine — generates per-tab system/user prompts for call_ica().
All tabs are tuned for CONCISE, scannable output — no filler, no padding.
"""

SYSTEM_PROMPT = """You are the IBM Consulting Marketing Intelligence Agent — a senior analyst and content strategist for IBM Consulting's Global Marketing team.

Domains: Cybersecurity | Autonomous Security | Financial Services | Public Sector | APAC

STRICT OUTPUT RULES — apply without exception:
- Be CONCISE. No padding, no filler sentences, no re-stating the question.
- Use tables and bullet points. Avoid long paragraphs.
- Every factual claim: cite [Doc Name] or [Doc Name, p.X].
- Label: [FACT], [INFERENCE], or [ASSUMPTION] on any claim that needs it.
- If APAC data is absent, write one line: "No APAC-specific data in sources."
- Never invent statistics. If data is missing, write [DATA GAP].
- IBM voice: authoritative, evidence-based, no unsupported superlatives."""


def _base_user_prompt(doc_context: str, tab_instruction: str) -> str:
    return (
        f"INTELLIGENCE DIGEST:\n{doc_context}\n\n"
        f"---\n\n{tab_instruction}\n\n"
        "Be concise. Use tables and bullets. No filler. Grounded in digest only."
    )


# ── TAB 1: EXECUTIVE SUMMARY ─────────────────────────────────────────────────

def tab1_executive_summary(doc_context: str) -> tuple:
    instruction = """Generate TAB 1 — EXECUTIVE SUMMARY. Target length: 600–900 words.

## Top 10 Key Findings
Numbered table: | # | Finding (1 sentence) | Source | Confidence |

## Strategic Implications
5 bullets max. IBM Consulting lens only.

## Market Opportunities
Ranked bullet list. One line each: opportunity + why it matters.

## Business Risks
Table: | Risk | Probability | Impact | Mitigation |

## Recommended Actions
Two columns — **0–90 days** and **90–180 days**. 3 actions each max.

## Source Summary
One-line description per uploaded document."""
    return SYSTEM_PROMPT, _base_user_prompt(doc_context, instruction)


# ── TAB 2: BLOG CONTENT OPPORTUNITIES ───────────────────────────────────────

def tab2_blog_content(doc_context: str) -> tuple:
    instruction = """Generate TAB 2 — BLOG CONTENT OPPORTUNITIES. 3 blog briefs max.
Priority order: Cybersecurity → Financial Services → Public Sector → APAC.

For each brief, use this compact table:

| Field | Content |
|---|---|
| Title | |
| Audience | Persona + level (e.g. CISO, mid-senior) |
| IBM Angle | One sentence |
| Key Stat | One cited data point |
| Quote | One verbatim quote from source |
| CTA | One sentence |

**Talking Points** (3 bullets max per brief)"""
    return SYSTEM_PROMPT, _base_user_prompt(doc_context, instruction)


# ── TAB 3: IBM CONSULTING PRIORITIES ────────────────────────────────────────

def tab3_ibm_priorities(doc_context: str) -> tuple:
    instruction = """Generate TAB 3 — IBM CONSULTING PRIORITIES ALIGNMENT. Target: 500–700 words.

Cover only priorities with evidence in the digest. Skip any with no source data.

Use this table for EACH priority:

| Field | Content |
|---|---|
| Priority | [Name] |
| Evidence | [Cited finding] |
| Business Impact | [1 line, quantified if possible] |
| IBM Message | [1–2 sentences, IBM voice] |
| Differentiation | [1 line] |

Priorities to cover:
- Security Transformation
- Managed Security Services
- AI-driven Security Operations
- Autonomous Remediation
- AI Governance"""
    return SYSTEM_PROMPT, _base_user_prompt(doc_context, instruction)


# ── TAB 4: FOCUS AREAS & MEETING AGENDAS ────────────────────────────────────

def tab4_focus_areas(doc_context: str) -> tuple:
    instruction = """Generate TAB 4 — FOCUS AREAS & MEETING AGENDAS. Target: 400–600 words.

## Strategic Focus Areas
Bullet list of 3 areas max. Each: name + one-line rationale.

## Meeting Agenda (one agenda per focus area)

Use compact format:
**Meeting: [Title]** | Duration: X min | Stakeholders: [Roles]

| # | Topic | Time | Owner |
|---|---|---|---|

**Decisions needed:** (2 bullets)
**Follow-ups:** (2 bullets)"""
    return SYSTEM_PROMPT, _base_user_prompt(doc_context, instruction)


# ── TAB 5: SOCIAL MEDIA CONTENT HUB ─────────────────────────────────────────

def tab5_social_media(doc_context: str) -> tuple:
    instruction = """Generate TAB 5 — SOCIAL MEDIA CONTENT HUB.

## LinkedIn Posts — 1 post per type (3 total)

**Type A — Executive Thought Leadership** (120–150 words, first-person, ends with question)
**Type B — Corporate Marketing** (80–100 words, stat-led, clear CTA)
**Type C — Industry Commentary** (80–100 words, references a specific finding)

For each post:
```
POST: [text]
HASHTAGS: #tag1 #tag2 #tag3 #tag4 #tag5
IMAGE: [one-line visual concept]
```

## Quick-Hit Ideas
- 2 × Carousel concepts (topic + 5-slide outline, one line each slide)
- 2 × Poll ideas (question + 4 options)
- 1 × Infographic concept (headline + 3 key stats)"""
    return SYSTEM_PROMPT, _base_user_prompt(doc_context, instruction)


# ── TAB 6: IBM-COMPLIANT EMAIL GENERATOR ────────────────────────────────────

def tab6_email_generator(doc_context: str) -> tuple:
    instruction = """Generate TAB 6 — EMAIL GENERATOR. One email per audience (3 total).
Audiences: Client | Prospect | Internal Stakeholder.

For each email use this compact format:

---
**[Audience]**
**Subject:** [<60 chars]
**Pre-header:** [<90 chars]

[Opening — 1 sentence personalised hook]

[Body — 2 short paragraphs, evidence-based, benefit-led]

**3 Supporting Insights:**
- [Stat/finding — source]
- [Stat/finding — source]
- [Stat/finding — source]

**CTA:** [One clear next step]

*[IBM Consulting standard disclaimer]*

---"""
    return SYSTEM_PROMPT, _base_user_prompt(doc_context, instruction)


# ── TAB 7: INDUSTRY DIRECTION & OUTLOOK ─────────────────────────────────────

def tab7_industry_outlook(doc_context: str) -> tuple:
    instruction = """Generate TAB 7 — INDUSTRY DIRECTION & OUTLOOK. Target: 500–700 words.

## Current State
Table: | Dimension | Assessment |
Rows: Market Maturity | Top 3 Drivers | Top 3 Buyer Pressures | Key Regulation

## Outlook Table
| Timeframe | Key Shifts | IBM Opportunity | Disruptors |
|---|---|---|---|
| 12 months | | | |
| 24 months | | | |
| 36 months | | | |

## APAC Spotlight
3–5 bullets. Country-level where data exists. Flag gaps explicitly."""
    return SYSTEM_PROMPT, _base_user_prompt(doc_context, instruction)


# ── TAB 8: INDUSTRY & TECHNOLOGY TRENDS ─────────────────────────────────────

def tab8_tech_trends(doc_context: str) -> tuple:
    instruction = """Generate TAB 8 — TECHNOLOGY TRENDS. Cover only trends with evidence in the digest.

For each trend use one compact block:

**[Trend Name]** — Impact: 🔴 High / 🟡 Medium / 🟢 Emerging

| Field | Content |
|---|---|
| Stage | Awareness / Early / Growth / Mainstream |
| Evidence | [Cited stat or finding] |
| APAC | [Specific data or DATA GAP] |
| IBM Opportunity | [Top 2, one line each] |
| Marketing Angle | [One sentence] |

End with a **Trend Rankings Table**: | Trend | Impact | Stage | IBM Priority |"""
    return SYSTEM_PROMPT, _base_user_prompt(doc_context, instruction)


# ── TAB 9: COMPETITIVE INTELLIGENCE ─────────────────────────────────────────

def tab9_competitive_intel(doc_context: str) -> tuple:
    instruction = """Generate TAB 9 — COMPETITIVE INTELLIGENCE.
Only cover competitors explicitly mentioned in the digest. Skip any not referenced.

For each competitor use this compact table:

**[Competitor]** — Threat: 🔴 High / 🟡 Medium / 🟢 Low

| Field | Content |
|---|---|
| Strategy | [1 line] |
| Cyber Capabilities | [1 line] |
| APAC Position | [1 line or DATA GAP] |
| Strength vs IBM | [1 line] |
| Weakness vs IBM | [1 line] |

## IBM Positioning
- **Top 3 Differentiators** (one line each, cited)
- **Top 3 White-Space Opportunities** (one line each)
- **Competitive Response** (one bullet per high-threat competitor)"""
    return SYSTEM_PROMPT, _base_user_prompt(doc_context, instruction)


# ── FINAL DELIVERABLE ────────────────────────────────────────────────────────

def tab_final_deliverable(doc_context: str) -> tuple:
    instruction = """Generate the FINAL DELIVERABLE. Target: 400–600 words. No padding.

Use numbered lists of exactly 5 items each. One sentence per item max (plus source).

## 🏆 Top 5 Strategic Opportunities
## ⚠️ Top 5 Competitive Threats
## 📣 Top 5 Marketing Actions (90-day executable)
## 💡 Top 5 Campaign Ideas (name + audience + core message)
## 🎙️ Top 5 Executive Talking Points (2 sentences each, fact-anchored)

---
*IBM Consulting Marketing Intelligence Agent · Human review required before external use · IBM Consulting Confidential*"""
    return SYSTEM_PROMPT, _base_user_prompt(doc_context, instruction)


# ── TAB REGISTRY ─────────────────────────────────────────────────────────────

TAB_REGISTRY = {
    "Tab 1 – Executive Summary": tab1_executive_summary,
    "Tab 2 – Blog Content Opportunities": tab2_blog_content,
    "Tab 3 – IBM Consulting Priorities": tab3_ibm_priorities,
    "Tab 4 – Focus Areas & Meeting Agendas": tab4_focus_areas,
    "Tab 5 – Social Media Content Hub": tab5_social_media,
    "Tab 6 – Email Generator": tab6_email_generator,
    "Tab 7 – Industry Direction & Outlook": tab7_industry_outlook,
    "Tab 8 – Industry & Technology Trends": tab8_tech_trends,
    "Tab 9 – Competitive Intelligence": tab9_competitive_intel,
    "Final Deliverable": tab_final_deliverable,
}
