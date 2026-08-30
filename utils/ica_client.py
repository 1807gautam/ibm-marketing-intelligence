"""
ICA API client.
Wraps IBM Consulting Accelerator (ICA) OpenAI-compatible chat completions endpoint.

Credential resolution order:
  1. Streamlit secrets (st.secrets) — used when deployed on Streamlit Cloud
  2. Environment variables / .env file — used for local development
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def _secret(key: str, default: str = "") -> str:
    """Read from st.secrets first, fall back to env vars."""
    try:
        import streamlit as st
        return st.secrets.get(key, os.getenv(key, default))
    except Exception:
        return os.getenv(key, default)

ICA_API_KEY  = _secret("ICA_API_KEY")
ICA_BASE_URL = _secret("ICA_BASE_URL", "https://api.nextgen-beta.ica.ibm.com/ica/v1")
ICA_MODEL    = _secret("ICA_MODEL", "claude-sonnet-4-5")

# Hard cap for the raw combined document context sent to the pre-summariser.
# The pre-summariser output (~6 000–10 000 chars) is what every tab actually uses.
MAX_CONTEXT_CHARS = 120_000

# Per-document cap: keep the first 60% and last 40% of large docs so we retain
# both the executive summary/intro AND the conclusions/recommendations.
PER_DOC_MAX_CHARS = 40_000

# Timeout for all ICA calls (seconds).  300 s covers even large-document runs.
REQUEST_TIMEOUT = 300


def call_ica(system_prompt: str, user_prompt: str, max_tokens: int = 8192) -> str:
    """
    Send a chat completion request to the ICA endpoint.
    Returns the assistant's reply text, or an error string.
    """
    if not ICA_API_KEY:
        return "[ERROR] ICA_API_KEY is not set. Check your .env file."

    url = f"{ICA_BASE_URL.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {ICA_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": ICA_MODEL,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }

    try:
        response = requests.post(
            url, headers=headers, json=payload, timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except requests.exceptions.HTTPError:
        return f"[HTTP ERROR {response.status_code}] {response.text}"
    except requests.exceptions.Timeout:
        return (
            "[ERROR] Request timed out after 300 s. "
            "This usually means the pre-summarised context is still too large. "
            "Try uploading fewer documents, or use the 'Summarise first' option."
        )
    except Exception as e:
        return f"[ERROR] {str(e)}"


# ── Context helpers ───────────────────────────────────────────────────────────

def _smart_truncate_doc(text: str, max_chars: int = PER_DOC_MAX_CHARS) -> str:
    """
    Keep the first 60 % and last 40 % of a document so that the executive
    summary/intro AND the conclusions/appendix are both preserved.
    """
    if len(text) <= max_chars:
        return text
    head = int(max_chars * 0.60)
    tail = int(max_chars * 0.40)
    return (
        text[:head]
        + f"\n\n[... {len(text) - head - tail:,} chars omitted for context efficiency ...]\n\n"
        + text[-tail:]
    )


def truncate_context(text: str, max_chars: int = MAX_CONTEXT_CHARS) -> str:
    """Final safety truncation on the combined context block."""
    if len(text) <= max_chars:
        return text
    head = int(max_chars * 0.70)
    tail = int(max_chars * 0.30)
    return (
        text[:head]
        + f"\n\n[... combined context truncated to {max_chars:,} chars for model efficiency ...]\n\n"
        + text[-tail:]
    )


def build_document_context(documents: dict) -> str:
    """
    Build a formatted context block from parsed document texts.
    Each document is smart-truncated individually before combining,
    so large uploads don't explode the context window.
    documents: {filename: extracted_text}
    """
    parts = []
    for filename, content in documents.items():
        truncated = _smart_truncate_doc(content)
        parts.append(
            f"{'='*60}\nDOCUMENT: {filename}\n"
            f"(original length: {len(content):,} chars)\n"
            f"{'='*60}\n{truncated}"
        )
    combined = "\n\n".join(parts)
    return truncate_context(combined)


# ── Pre-summarisation ─────────────────────────────────────────────────────────

PRE_SUMMARISE_SYSTEM = """You are a senior intelligence analyst. Your job is to compress one or more uploaded documents into a dense, structured intelligence digest. Preserve ALL statistics, named entities, quotes, company names, product names, market figures, regulatory references, geographic mentions (especially APAC), and competitive intelligence. Do not editorialize. Do not add information not present in the source. Output only the digest."""

PRE_SUMMARISE_INSTRUCTION = """Compress the following documents into a dense intelligence digest of 4 000–6 000 words.

Structure the digest as:
1. KEY STATISTICS & DATA POINTS (every number, percentage, market figure)
2. NAMED ENTITIES (companies, products, people, regulators, standards bodies)
3. CORE THEMES & FINDINGS (grouped by topic)
4. QUOTES (verbatim, with attribution)
5. GEOGRAPHIC INTELLIGENCE (especially APAC, country-level where available)
6. COMPETITIVE MENTIONS (any competitor names, strategies, announcements)
7. REGULATORY & COMPLIANCE REFERENCES
8. TECHNOLOGY TRENDS MENTIONED
9. RISKS & CHALLENGES IDENTIFIED
10. OPPORTUNITIES & RECOMMENDATIONS MENTIONED

Preserve source document names for attribution. Be exhaustive on facts and figures."""


def build_pre_summarised_context(documents: dict) -> tuple[str, str]:
    """
    Two-phase context builder for large document sets.

    Phase 1: Smart-truncate each doc and build the raw combined context.
    Phase 2: Call ICA to compress the combined context into a dense digest.

    Returns (digest_text, raw_context_text).
    The digest is used for all tab generation calls (small, fast).
    The raw context is stored for reference/download.
    """
    raw_context = build_document_context(documents)

    # If the raw context is small enough, skip summarisation entirely
    if len(raw_context) <= 30_000:
        return raw_context, raw_context

    user_prompt = (
        f"{PRE_SUMMARISE_INSTRUCTION}\n\n"
        f"DOCUMENTS TO COMPRESS:\n{raw_context}"
    )

    digest = call_ica(
        PRE_SUMMARISE_SYSTEM,
        user_prompt,
        max_tokens=8000,
    )

    if digest.startswith("[ERROR]") or digest.startswith("[HTTP ERROR]"):
        # Fall back to raw context on summarisation failure
        return raw_context, raw_context

    return digest, raw_context
