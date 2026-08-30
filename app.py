"""
IBM Consulting Marketing Intelligence Dashboard
Main Streamlit application entry point.
"""

import streamlit as st
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.file_parser import parse_uploaded_file
from utils.ica_client import call_ica, build_document_context, build_pre_summarised_context
from utils.prompt_engine import TAB_REGISTRY

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="IBM Consulting Marketing Intelligence",
    page_icon="🔷",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CUSTOM CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* IBM-inspired palette */
    :root {
        --ibm-blue: #0f62fe;
        --ibm-dark: #161616;
        --ibm-gray: #393939;
        --ibm-light: #f4f4f4;
        --ibm-white: #ffffff;
        --ibm-cool-gray: #697077;
    }

    .main { background-color: var(--ibm-light); }

    /* Header bar */
    .ibm-header {
        background: linear-gradient(135deg, #0f62fe 0%, #0043ce 100%);
        color: white;
        padding: 1.5rem 2rem;
        border-radius: 4px;
        margin-bottom: 1.5rem;
    }
    .ibm-header h1 { margin: 0; font-size: 1.6rem; font-weight: 600; color: white; }
    .ibm-header p  { margin: 0.3rem 0 0; font-size: 0.9rem; opacity: 0.85; color: white; }

    /* Tab content card */
    .tab-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 4px;
        padding: 1.5rem;
        margin-top: 0.5rem;
    }

    /* Status badges */
    .badge-success { background:#24a148; color:white; padding:2px 10px; border-radius:12px; font-size:0.75rem; }
    .badge-pending { background:#f1c21b; color:#161616; padding:2px 10px; border-radius:12px; font-size:0.75rem; }
    .badge-running { background:#0f62fe; color:white; padding:2px 10px; border-radius:12px; font-size:0.75rem; }
    .badge-error   { background:#da1e28; color:white; padding:2px 10px; border-radius:12px; font-size:0.75rem; }

    /* Sidebar */
    section[data-testid="stSidebar"] { background-color: #161616 !important; }
    section[data-testid="stSidebar"] * { color: #f4f4f4 !important; }
    section[data-testid="stSidebar"] .stButton>button {
        background-color: #0f62fe !important;
        color: white !important;
        border: none !important;
        width: 100%;
    }
    section[data-testid="stSidebar"] .stButton>button:hover {
        background-color: #0043ce !important;
    }

    /* Primary button */
    .stButton>button[kind="primary"] {
        background-color: #0f62fe;
        color: white;
        border: none;
        font-weight: 600;
    }
    .stButton>button[kind="primary"]:hover { background-color: #0043ce; }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] { gap: 0; border-bottom: 2px solid #e0e0e0; }
    .stTabs [data-baseweb="tab"] {
        padding: 0.6rem 1rem;
        font-size: 0.82rem;
        font-weight: 500;
        border-bottom: 2px solid transparent;
        margin-bottom: -2px;
    }
    .stTabs [aria-selected="true"] { border-bottom: 2px solid #0f62fe !important; color: #0f62fe !important; }

    /* Divider */
    hr { border-top: 1px solid #e0e0e0; margin: 1rem 0; }
</style>
""", unsafe_allow_html=True)


# ── SESSION STATE INIT ────────────────────────────────────────────────────────
def init_state():
    if "documents" not in st.session_state:
        st.session_state.documents = {}          # {filename: extracted_text}
    if "results" not in st.session_state:
        st.session_state.results = {}            # {tab_name: output_text}
    if "tab_status" not in st.session_state:
        st.session_state.tab_status = {}         # {tab_name: "pending"|"running"|"done"|"error"}
    if "analysis_run" not in st.session_state:
        st.session_state.analysis_run = False

init_state()


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔷 IBM Consulting MI")
    st.markdown("**Marketing Intelligence Agent**")
    st.markdown("---")

    # File uploader
    st.markdown("#### 📁 Upload Documents")
    uploaded_files = st.file_uploader(
        "Drag & drop or browse",
        type=["pdf", "docx", "pptx", "txt", "md", "csv", "xlsx", "xls"],
        accept_multiple_files=True,
        help="Supported: PDF, DOCX, PPTX, TXT, MD, CSV, XLSX",
        label_visibility="collapsed",
    )

    if uploaded_files:
        # Parse files
        new_docs = {}
        for f in uploaded_files:
            f.seek(0)
            text = parse_uploaded_file(f)
            new_docs[f.name] = text
        st.session_state.documents = new_docs

        st.markdown(f"**{len(new_docs)} file(s) loaded:**")
        for fname in new_docs:
            word_count = len(new_docs[fname].split())
            st.markdown(f"- 📄 `{fname}` ({word_count:,} words)")

    st.markdown("---")

    # Tab selection
    st.markdown("#### ⚙️ Select Tabs to Generate")
    tab_names = list(TAB_REGISTRY.keys())
    select_all = st.checkbox("Select All Tabs", value=True)
    selected_tabs = []
    if select_all:
        selected_tabs = tab_names
        for t in tab_names:
            st.markdown(f"☑ {t}")
    else:
        for t in tab_names:
            if st.checkbox(t, value=True, key=f"chk_{t}"):
                selected_tabs.append(t)

    st.markdown("---")

    # Run button
    run_disabled = len(st.session_state.documents) == 0
    if st.button("🚀 Run Analysis", disabled=run_disabled, type="primary"):
        if not selected_tabs:
            st.error("Select at least one tab.")
        else:
            st.session_state.results = {}
            st.session_state.tab_status = {t: "pending" for t in selected_tabs}
            st.session_state.analysis_run = True
            st.session_state.selected_tabs = selected_tabs
            # Clear cached digest so new files get a fresh compression pass
            st.session_state.pop("doc_digest", None)
            st.session_state.pop("doc_raw", None)
            st.rerun()

    if run_disabled:
        st.caption("⬆ Upload at least one document to enable analysis.")

    st.markdown("---")
    st.caption("IBM Consulting Marketing Intelligence Agent v2.0\nPowered by ICA · claude-sonnet-4-5")


# ── MAIN HEADER ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="ibm-header">
  <h1>🔷 IBM Consulting Marketing Intelligence Dashboard</h1>
  <p>Upload analyst reports, white papers, IBM publications, and competitive documents. Get a full 9-tab marketing intelligence brief in minutes.</p>
</div>
""", unsafe_allow_html=True)


# ── WELCOME STATE ─────────────────────────────────────────────────────────────
if not st.session_state.documents and not st.session_state.analysis_run:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("**Step 1** 📁\n\nUpload your documents in the sidebar. Supports PDF, DOCX, PPTX, TXT, CSV, XLSX.")
    with col2:
        st.info("**Step 2** ⚙️\n\nChoose which tabs to generate — or select all 10 for a full dashboard.")
    with col3:
        st.info("**Step 3** 🚀\n\nClick **Run Analysis** and the agent analyses all documents and generates your dashboard.")

    st.markdown("---")
    st.markdown("### 📊 Dashboard Tabs")
    tab_descriptions = {
        "Tab 1 – Executive Summary": "Top 10 findings, strategic implications, risks, and recommended actions.",
        "Tab 2 – Blog Content Opportunities": "Ready-to-brief blog content ideas with talking points, stats, and CTAs.",
        "Tab 3 – IBM Consulting Priorities": "Alignment to IBM's Cybersecurity and Autonomous Security priorities.",
        "Tab 4 – Focus Areas & Meeting Agendas": "Strategic focus areas with structured meeting agenda templates.",
        "Tab 5 – Social Media Content Hub": "LinkedIn posts (3 types), carousels, polls, and infographic concepts.",
        "Tab 6 – Email Generator": "IBM-compliant emails for clients, prospects, and internal stakeholders.",
        "Tab 7 – Industry Direction & Outlook": "12/24/36-month market outlook with APAC-specific analysis.",
        "Tab 8 – Industry & Technology Trends": "Ranked technology trends with business opportunities and marketing implications.",
        "Tab 9 – Competitive Intelligence": "Competitor assessment vs IBM with positioning recommendations.",
        "Final Deliverable": "Top 5 opportunities, threats, actions, campaigns, and executive talking points.",
    }
    for tab, desc in tab_descriptions.items():
        st.markdown(f"**{tab}** — {desc}")


# ── ANALYSIS ENGINE ───────────────────────────────────────────────────────────
if st.session_state.analysis_run and st.session_state.documents:
    selected_tabs = st.session_state.get("selected_tabs", list(TAB_REGISTRY.keys()))
    pending = [t for t in selected_tabs if st.session_state.tab_status.get(t) == "pending"]

    if pending:
        progress_bar = st.progress(0, text="⏳ Compressing documents...")
        status_text = st.empty()

        # ── Phase 1: pre-summarise all documents into a compact digest ────────
        # Only runs once; result is cached in session state
        if "doc_digest" not in st.session_state:
            status_text.info("📄 Compressing documents into intelligence digest… (runs once, speeds up all tabs)")
            digest, raw = build_pre_summarised_context(st.session_state.documents)
            st.session_state.doc_digest = digest
            st.session_state.doc_raw = raw
            digest_size = len(digest)
            raw_size = len(raw)
            compression = int((1 - digest_size / max(raw_size, 1)) * 100)
            status_text.success(
                f"✅ Digest ready — {digest_size:,} chars "
                f"(compressed {compression}% from {raw_size:,} chars raw)"
            )
            time.sleep(1)
        else:
            status_text.success("✅ Using cached digest from previous run")

        doc_context = st.session_state.doc_digest

        # ── Phase 2: generate tabs in parallel (up to 3 at a time) ───────────
        total = len(selected_tabs)
        done_count = sum(1 for t in selected_tabs if st.session_state.tab_status.get(t) == "done")
        progress_bar.progress(done_count / max(total, 1), text="⏳ Generating tabs in parallel…")

        def _run_tab(tab_name: str) -> tuple[str, str]:
            """Run a single tab and return (tab_name, result)."""
            prompt_fn = TAB_REGISTRY[tab_name]
            system_prompt, user_prompt = prompt_fn(doc_context)
            result = call_ica(system_prompt, user_prompt, max_tokens=4096)
            return tab_name, result

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(_run_tab, t): t for t in pending}
            for future in as_completed(futures):
                tab_name, result = future.result()
                if result.startswith("[ERROR]") or result.startswith("[HTTP ERROR]"):
                    st.session_state.tab_status[tab_name] = "error"
                else:
                    st.session_state.tab_status[tab_name] = "done"
                st.session_state.results[tab_name] = result
                done_count += 1
                progress_bar.progress(
                    done_count / max(total, 1),
                    text=f"✅ Done: {tab_name} ({done_count}/{total})"
                )

        progress_bar.progress(1.0, text="✅ All tabs generated!")
        status_text.empty()
        time.sleep(1)
        st.rerun()


# ── RESULTS DASHBOARD ─────────────────────────────────────────────────────────
if st.session_state.results:
    selected_tabs = st.session_state.get("selected_tabs", list(TAB_REGISTRY.keys()))
    completed = [t for t in selected_tabs if st.session_state.tab_status.get(t) == "done"]
    errored = [t for t in selected_tabs if st.session_state.tab_status.get(t) == "error"]

    # Status bar
    col_a, col_b, col_c = st.columns([2, 1, 1])
    with col_a:
        st.success(f"✅ Analysis complete — {len(completed)}/{len(selected_tabs)} tabs generated")
    with col_b:
        if errored:
            st.error(f"❌ {len(errored)} tab(s) failed")
    with col_c:
        # Download all results as markdown
        if completed:
            all_output = ""
            for t in completed:
                all_output += f"\n\n{'#'*60}\n# {t}\n{'#'*60}\n\n"
                all_output += st.session_state.results.get(t, "")
            st.download_button(
                label="⬇ Download All (MD)",
                data=all_output.encode("utf-8"),
                file_name="ibm_marketing_intelligence_report.md",
                mime="text/markdown",
            )

    st.markdown("---")

    # Render tabs
    if completed:
        tabs_ui = st.tabs(completed)
        for i, tab_name in enumerate(completed):
            with tabs_ui[i]:
                result_text = st.session_state.results.get(tab_name, "")

                # Per-tab download
                col_left, col_right = st.columns([5, 1])
                with col_right:
                    st.download_button(
                        label="⬇ Download",
                        data=result_text.encode("utf-8"),
                        file_name=f"{tab_name.replace(' ', '_').replace('–', '-')}.md",
                        mime="text/markdown",
                        key=f"dl_{tab_name}",
                    )
                with col_left:
                    st.markdown(f"### {tab_name}")

                st.markdown('<div class="tab-card">', unsafe_allow_html=True)
                st.markdown(result_text)
                st.markdown('</div>', unsafe_allow_html=True)

    # Show errors
    if errored:
        st.markdown("---")
        st.markdown("### ❌ Failed Tabs")
        for t in errored:
            with st.expander(f"Error details: {t}"):
                st.error(st.session_state.results.get(t, "Unknown error"))


# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    "IBM Consulting Marketing Intelligence Agent · Powered by ICA (claude-sonnet-4-5) · "
    "All outputs require human review before external use · IBM Consulting Confidential"
)
