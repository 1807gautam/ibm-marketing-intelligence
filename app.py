"""
IBM Consulting Marketing Intelligence Dashboard
Main Streamlit application entry point.
"""

import streamlit as st
import time
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.file_parser import parse_uploaded_file
from utils.ica_client import call_ica, build_document_context, build_pre_summarised_context
from utils.prompt_engine import TAB_REGISTRY

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="IBM Consulting · Marketing Intelligence",
    page_icon="assets/favicon.png" if __import__("os").path.exists("assets/favicon.png") else "💡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CUSTOM CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

  /* ── Global ── */
  html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', system-ui, sans-serif !important;
  }
  .main .block-container {
    padding: 2rem 2.5rem 3rem;
    max-width: 1280px;
  }
  .main { background: #f8f9fb; }

  /* ── Sidebar ── */
  section[data-testid="stSidebar"] {
    background: #ffffff !important;
    border-right: 1px solid #e4e7ec !important;
    padding-top: 0 !important;
  }
  section[data-testid="stSidebar"] > div:first-child {
    padding-top: 0 !important;
  }
  /* Sidebar branding strip */
  .sidebar-brand {
    background: #0f62fe;
    margin: -1rem -1rem 1.5rem -1rem;
    padding: 1.2rem 1.4rem;
  }
  .sidebar-brand h2 {
    color: #ffffff !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
    margin: 0 !important;
    letter-spacing: 0.01em;
  }
  .sidebar-brand p {
    color: rgba(255,255,255,0.75) !important;
    font-size: 0.75rem !important;
    margin: 0.2rem 0 0 !important;
  }

  /* Sidebar section labels */
  .sidebar-label {
    font-size: 0.7rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    color: #6b7280 !important;
    margin: 1.2rem 0 0.5rem !important;
  }

  /* File list items */
  .file-chip {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    background: #f0f4ff;
    border: 1px solid #c7d7fd;
    border-radius: 6px;
    padding: 0.35rem 0.6rem;
    margin-bottom: 0.35rem;
    font-size: 0.75rem;
    color: #1d4ed8;
    font-family: 'IBM Plex Mono', monospace;
    word-break: break-all;
  }
  .file-chip .wc {
    margin-left: auto;
    white-space: nowrap;
    color: #6b7280;
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 0.68rem;
  }

  /* Sidebar checkboxes */
  section[data-testid="stSidebar"] .stCheckbox label {
    font-size: 0.8rem !important;
    color: #374151 !important;
  }

  /* Run button */
  section[data-testid="stSidebar"] .stButton > button {
    width: 100% !important;
    background: #0f62fe !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 6px !important;
    font-size: 0.88rem !important;
    font-weight: 600 !important;
    padding: 0.65rem 1rem !important;
    margin-top: 0.5rem !important;
    letter-spacing: 0.01em !important;
    transition: background 0.15s !important;
  }
  section[data-testid="stSidebar"] .stButton > button:hover {
    background: #0043ce !important;
  }
  section[data-testid="stSidebar"] .stButton > button:disabled {
    background: #d1d5db !important;
    color: #9ca3af !important;
    cursor: not-allowed !important;
  }

  /* ── Hero header ── */
  .hero {
    background: #ffffff;
    border: 1px solid #e4e7ec;
    border-left: 5px solid #0f62fe;
    border-radius: 8px;
    padding: 1.6rem 2rem;
    margin-bottom: 1.8rem;
    display: flex;
    align-items: center;
    gap: 1.5rem;
  }
  .hero-icon {
    width: 48px;
    height: 48px;
    background: #0f62fe;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    font-size: 1.4rem;
  }
  .hero h1 {
    font-size: 1.45rem !important;
    font-weight: 700 !important;
    color: #111827 !important;
    margin: 0 0 0.25rem !important;
    line-height: 1.25 !important;
  }
  .hero p {
    font-size: 0.88rem !important;
    color: #6b7280 !important;
    margin: 0 !important;
  }
  .hero-badge {
    margin-left: auto;
    background: #f0f4ff;
    border: 1px solid #c7d7fd;
    color: #1d4ed8;
    font-size: 0.72rem;
    font-weight: 600;
    padding: 0.3rem 0.75rem;
    border-radius: 20px;
    white-space: nowrap;
    flex-shrink: 0;
  }

  /* ── Step cards ── */
  .step-grid { display: grid; grid-template-columns: repeat(3,1fr); gap: 1rem; margin-bottom: 2rem; }
  .step-card {
    background: #ffffff;
    border: 1px solid #e4e7ec;
    border-radius: 8px;
    padding: 1.25rem 1.4rem;
  }
  .step-card .step-num {
    display: inline-block;
    width: 28px; height: 28px;
    background: #0f62fe;
    color: white;
    border-radius: 50%;
    font-size: 0.8rem;
    font-weight: 700;
    text-align: center;
    line-height: 28px;
    margin-bottom: 0.75rem;
  }
  .step-card h4 { font-size: 0.9rem; font-weight: 600; color: #111827; margin: 0 0 0.3rem; }
  .step-card p  { font-size: 0.8rem; color: #6b7280; margin: 0; line-height: 1.5; }

  /* ── Tab capability grid ── */
  .cap-grid { display: grid; grid-template-columns: repeat(2,1fr); gap: 0.65rem; }
  .cap-card {
    background: #ffffff;
    border: 1px solid #e4e7ec;
    border-radius: 6px;
    padding: 0.85rem 1rem;
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
  }
  .cap-icon {
    width: 32px; height: 32px;
    background: #f0f4ff;
    border-radius: 6px;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.95rem; flex-shrink: 0;
  }
  .cap-card strong { font-size: 0.82rem; font-weight: 600; color: #111827; display: block; margin-bottom: 0.15rem; }
  .cap-card span   { font-size: 0.75rem; color: #6b7280; line-height: 1.4; }

  /* ── Results area ── */
  .results-bar {
    background: #ffffff;
    border: 1px solid #e4e7ec;
    border-radius: 8px;
    padding: 1rem 1.4rem;
    margin-bottom: 1.2rem;
    display: flex;
    align-items: center;
    gap: 1rem;
    flex-wrap: wrap;
  }
  .results-bar .stat { font-size: 0.82rem; color: #374151; }
  .results-bar .stat strong { color: #111827; }
  .pill-success { background:#d1fae5; color:#065f46; padding:3px 10px; border-radius:20px; font-size:0.72rem; font-weight:600; }
  .pill-error   { background:#fee2e2; color:#991b1b; padding:3px 10px; border-radius:20px; font-size:0.72rem; font-weight:600; }

  /* ── Output tabs ── */
  .stTabs [data-baseweb="tab-list"] {
    gap: 0 !important;
    background: #f8f9fb !important;
    border-bottom: 2px solid #e4e7ec !important;
    border-radius: 0 !important;
    padding: 0 !important;
  }
  .stTabs [data-baseweb="tab"] {
    padding: 0.6rem 1.1rem !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    color: #6b7280 !important;
    border-bottom: 2px solid transparent !important;
    margin-bottom: -2px !important;
    background: transparent !important;
    white-space: nowrap !important;
  }
  .stTabs [aria-selected="true"] {
    color: #0f62fe !important;
    border-bottom: 2px solid #0f62fe !important;
    font-weight: 600 !important;
  }
  .stTabs [data-baseweb="tab"]:hover { color: #0f62fe !important; background: #f0f4ff !important; }

  /* ── Tab content card ── */
  .output-card {
    background: #ffffff;
    border: 1px solid #e4e7ec;
    border-radius: 8px;
    padding: 2rem 2.2rem;
    margin-top: 1rem;
  }
  .output-card h2 { font-size: 1.15rem !important; font-weight: 700 !important; color: #111827 !important; }
  .output-card h3 { font-size: 0.98rem !important; font-weight: 600 !important; color: #1e3a5f !important; }
  .output-card h4 { font-size: 0.88rem !important; font-weight: 600 !important; color: #374151 !important; }
  .output-card p  { font-size: 0.87rem !important; color: #374151 !important; line-height: 1.65 !important; }
  .output-card li { font-size: 0.87rem !important; color: #374151 !important; line-height: 1.65 !important; }
  .output-card table { width: 100%; border-collapse: collapse; font-size: 0.82rem; }
  .output-card th {
    background: #f0f4ff;
    color: #1d4ed8;
    font-weight: 600;
    padding: 0.55rem 0.8rem;
    text-align: left;
    border: 1px solid #dbeafe;
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }
  .output-card td {
    padding: 0.5rem 0.8rem;
    border: 1px solid #e4e7ec;
    color: #374151;
    vertical-align: top;
  }
  .output-card tr:nth-child(even) td { background: #f8f9fb; }
  .output-card code {
    background: #f1f5f9;
    color: #0f172a;
    padding: 0.15rem 0.4rem;
    border-radius: 3px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.82em;
  }
  .output-card pre {
    background: #f1f5f9;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 1rem 1.2rem;
    overflow-x: auto;
  }
  .output-card blockquote {
    border-left: 3px solid #0f62fe;
    margin: 0.8rem 0;
    padding: 0.4rem 1rem;
    background: #f0f4ff;
    border-radius: 0 4px 4px 0;
    color: #1e3a5f;
    font-style: normal;
  }

  /* Download buttons */
  .stDownloadButton > button {
    background: #ffffff !important;
    border: 1.5px solid #0f62fe !important;
    color: #0f62fe !important;
    border-radius: 6px !important;
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    padding: 0.45rem 1rem !important;
    transition: all 0.15s !important;
  }
  .stDownloadButton > button:hover {
    background: #0f62fe !important;
    color: #ffffff !important;
  }

  /* Progress bar */
  .stProgress > div > div { background: #0f62fe !important; border-radius: 4px !important; }
  .stProgress > div { background: #e4e7ec !important; border-radius: 4px !important; }

  /* Footer */
  .footer {
    text-align: center;
    padding: 1.5rem 0 0.5rem;
    font-size: 0.72rem;
    color: #9ca3af;
    border-top: 1px solid #e4e7ec;
    margin-top: 2.5rem;
  }

  /* Dividers */
  hr { border: none; border-top: 1px solid #e4e7ec; margin: 1.5rem 0; }
</style>
""", unsafe_allow_html=True)


# ── SESSION STATE ─────────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "documents": {},
        "results": {},
        "tab_status": {},
        "analysis_run": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ── HTML EXPORT BUILDER ───────────────────────────────────────────────────────
def build_html_export(results: dict, tab_order: list) -> str:
    """Convert markdown results into a self-contained tabbed HTML report."""

    def md_to_html(text: str) -> str:
        """Minimal markdown → HTML converter."""
        # Code blocks
        text = re.sub(r'```[\w]*\n(.*?)```', lambda m: f'<pre><code>{m.group(1).strip()}</code></pre>', text, flags=re.DOTALL)
        # Tables
        def convert_table(m):
            rows = [r.strip() for r in m.group(0).strip().split('\n') if r.strip() and not re.match(r'^\|[-| :]+\|$', r.strip())]
            if not rows: return m.group(0)
            html = '<table>'
            for i, row in enumerate(rows):
                cells = [c.strip() for c in row.strip('|').split('|')]
                tag = 'th' if i == 0 else 'td'
                html += '<tr>' + ''.join(f'<{tag}>{c}</{tag}>' for c in cells) + '</tr>'
            return html + '</table>'
        text = re.sub(r'(\|.+\|\n?)+', convert_table, text)
        # Headings
        text = re.sub(r'^#### (.+)$', r'<h4>\1</h4>', text, flags=re.MULTILINE)
        text = re.sub(r'^### (.+)$',  r'<h3>\1</h3>', text, flags=re.MULTILINE)
        text = re.sub(r'^## (.+)$',   r'<h2>\1</h2>', text, flags=re.MULTILINE)
        text = re.sub(r'^# (.+)$',    r'<h1>\1</h1>', text, flags=re.MULTILINE)
        # Bold / italic
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'\*(.+?)\*',     r'<em>\1</em>', text)
        # Inline code
        text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
        # Blockquote
        text = re.sub(r'^> (.+)$', r'<blockquote>\1</blockquote>', text, flags=re.MULTILINE)
        # Horizontal rule
        text = re.sub(r'^---+$', '<hr>', text, flags=re.MULTILINE)
        # Unordered lists
        def ul_block(m):
            items = re.findall(r'^[-*] (.+)$', m.group(0), re.MULTILINE)
            return '<ul>' + ''.join(f'<li>{i}</li>' for i in items) + '</ul>'
        text = re.sub(r'(^[-*] .+\n?)+', ul_block, text, flags=re.MULTILINE)
        # Ordered lists
        def ol_block(m):
            items = re.findall(r'^\d+\. (.+)$', m.group(0), re.MULTILINE)
            return '<ol>' + ''.join(f'<li>{i}</li>' for i in items) + '</ol>'
        text = re.sub(r'(^\d+\. .+\n?)+', ol_block, text, flags=re.MULTILINE)
        # Paragraphs
        paras = []
        for block in re.split(r'\n{2,}', text):
            block = block.strip()
            if block and not re.match(r'^<(h[1-6]|ul|ol|table|pre|blockquote|hr)', block):
                paras.append(f'<p>{block}</p>')
            else:
                paras.append(block)
        return '\n'.join(paras)

    # Build tab buttons + panels
    tab_buttons = ""
    tab_panels  = ""
    for i, tab_name in enumerate(tab_order):
        tid    = f"tab{i}"
        active = "active" if i == 0 else ""
        short  = tab_name.replace("Tab ", "").replace(" –", ":")
        tab_buttons += f'<button class="tab-btn {active}" onclick="switchTab(\'{tid}\')" id="btn-{tid}">{short}</button>\n'
        content = md_to_html(results.get(tab_name, "No content generated."))
        tab_panels += f'<div class="tab-panel {active}" id="{tid}"><h2 class="panel-title">{tab_name}</h2>{content}</div>\n'

    from datetime import datetime
    generated = datetime.now().strftime("%d %B %Y, %H:%M")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>IBM Consulting Marketing Intelligence Report</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');
  *, *::before, *::after {{ box-sizing: border-box; }}
  body {{
    font-family: 'IBM Plex Sans', system-ui, sans-serif;
    background: #f8f9fb;
    color: #111827;
    margin: 0;
    padding: 0;
    font-size: 14px;
    line-height: 1.6;
  }}
  /* ── Header ── */
  .report-header {{
    background: #0f62fe;
    color: white;
    padding: 2rem 3rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
  }}
  .report-header h1 {{ margin: 0; font-size: 1.4rem; font-weight: 700; }}
  .report-header p  {{ margin: 0.3rem 0 0; font-size: 0.82rem; opacity: 0.8; }}
  .report-header .meta {{ text-align: right; font-size: 0.75rem; opacity: 0.75; }}

  /* ── Tab bar ── */
  .tab-bar {{
    background: #ffffff;
    border-bottom: 2px solid #e4e7ec;
    padding: 0 2rem;
    display: flex;
    flex-wrap: wrap;
    gap: 0;
    position: sticky;
    top: 0;
    z-index: 100;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  }}
  .tab-btn {{
    background: none;
    border: none;
    border-bottom: 2px solid transparent;
    padding: 0.75rem 1rem;
    font-family: inherit;
    font-size: 0.78rem;
    font-weight: 500;
    color: #6b7280;
    cursor: pointer;
    margin-bottom: -2px;
    transition: all 0.15s;
    white-space: nowrap;
  }}
  .tab-btn:hover  {{ color: #0f62fe; background: #f0f4ff; }}
  .tab-btn.active {{ color: #0f62fe; border-bottom-color: #0f62fe; font-weight: 600; }}

  /* ── Content ── */
  .content-wrap {{ max-width: 1100px; margin: 0 auto; padding: 2rem 2.5rem 4rem; }}
  .tab-panel {{ display: none; }}
  .tab-panel.active {{ display: block; }}
  .panel-title {{
    font-size: 1.3rem;
    font-weight: 700;
    color: #0f62fe;
    margin: 0 0 1.5rem;
    padding-bottom: 0.75rem;
    border-bottom: 2px solid #e4e7ec;
  }}

  /* ── Typography ── */
  h1 {{ font-size: 1.2rem; font-weight: 700; color: #111827; margin: 1.5rem 0 0.75rem; }}
  h2 {{ font-size: 1.05rem; font-weight: 700; color: #1e3a5f; margin: 1.4rem 0 0.6rem; }}
  h3 {{ font-size: 0.95rem; font-weight: 600; color: #1e3a5f; margin: 1.2rem 0 0.5rem; }}
  h4 {{ font-size: 0.88rem; font-weight: 600; color: #374151; margin: 1rem 0 0.4rem; }}
  p  {{ margin: 0.5rem 0 0.9rem; color: #374151; }}
  ul, ol {{ padding-left: 1.5rem; margin: 0.5rem 0 1rem; }}
  li {{ margin-bottom: 0.35rem; color: #374151; }}
  strong {{ color: #111827; }}
  blockquote {{
    border-left: 3px solid #0f62fe;
    margin: 1rem 0;
    padding: 0.5rem 1rem;
    background: #f0f4ff;
    border-radius: 0 4px 4px 0;
    color: #1e3a5f;
  }}
  hr {{ border: none; border-top: 1px solid #e4e7ec; margin: 1.5rem 0; }}
  code {{
    background: #f1f5f9;
    color: #0f172a;
    padding: 0.15rem 0.4rem;
    border-radius: 3px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.85em;
  }}
  pre {{
    background: #f1f5f9;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 1rem 1.2rem;
    overflow-x: auto;
    margin: 1rem 0;
  }}
  pre code {{ background: none; padding: 0; font-size: 0.82rem; }}

  /* ── Tables ── */
  table {{ width: 100%; border-collapse: collapse; margin: 1rem 0 1.5rem; font-size: 0.82rem; }}
  th {{
    background: #f0f4ff;
    color: #1d4ed8;
    font-weight: 600;
    padding: 0.55rem 0.8rem;
    text-align: left;
    border: 1px solid #dbeafe;
    font-size: 0.76rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }}
  td {{
    padding: 0.5rem 0.8rem;
    border: 1px solid #e4e7ec;
    color: #374151;
    vertical-align: top;
  }}
  tr:nth-child(even) td {{ background: #f8f9fb; }}

  /* ── Footer ── */
  .report-footer {{
    text-align: center;
    padding: 1.5rem;
    font-size: 0.72rem;
    color: #9ca3af;
    border-top: 1px solid #e4e7ec;
    background: #ffffff;
  }}
</style>
</head>
<body>

<div class="report-header">
  <div>
    <h1>IBM Consulting Marketing Intelligence Report</h1>
    <p>AI-generated analysis powered by ICA · claude-sonnet-4-5</p>
  </div>
  <div class="meta">Generated: {generated}<br>All outputs require human review before external use<br>IBM Consulting Confidential</div>
</div>

<div class="tab-bar">
{tab_buttons}
</div>

<div class="content-wrap">
{tab_panels}
</div>

<div class="report-footer">
  IBM Consulting Marketing Intelligence Agent &nbsp;·&nbsp; Powered by ICA (claude-sonnet-4-5) &nbsp;·&nbsp;
  All outputs require human review before external use &nbsp;·&nbsp; IBM Consulting Confidential
</div>

<script>
function switchTab(tid) {{
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.getElementById(tid).classList.add('active');
  document.getElementById('btn-' + tid).classList.add('active');
}}
</script>
</body>
</html>"""


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
      <h2>IBM Consulting</h2>
      <p>Marketing Intelligence Agent</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<p class="sidebar-label">Upload Documents</p>', unsafe_allow_html=True)
    uploaded_files = st.file_uploader(
        "upload",
        type=["pdf", "docx", "pptx", "txt", "md", "csv", "xlsx", "xls"],
        accept_multiple_files=True,
        help="PDF, DOCX, PPTX, TXT, MD, CSV, XLSX supported",
        label_visibility="collapsed",
    )

    if uploaded_files:
        new_docs = {}
        for f in uploaded_files:
            f.seek(0)
            new_docs[f.name] = parse_uploaded_file(f)
        st.session_state.documents = new_docs

        st.markdown(f'<p class="sidebar-label">{len(new_docs)} file(s) loaded</p>', unsafe_allow_html=True)
        for fname, txt in new_docs.items():
            wc = len(txt.split())
            short_name = fname if len(fname) <= 28 else fname[:25] + "…"
            st.markdown(
                f'<div class="file-chip">📄 {short_name}<span class="wc">{wc:,}w</span></div>',
                unsafe_allow_html=True,
            )

    st.markdown('<p class="sidebar-label">Output Tabs</p>', unsafe_allow_html=True)
    tab_names = list(TAB_REGISTRY.keys())
    select_all = st.checkbox("Select all", value=True)
    selected_tabs = []
    if select_all:
        selected_tabs = tab_names
    else:
        for t in tab_names:
            if st.checkbox(t, value=True, key=f"chk_{t}"):
                selected_tabs.append(t)

    st.markdown("")
    run_disabled = len(st.session_state.documents) == 0
    if st.button("Run Analysis", disabled=run_disabled, type="primary"):
        if not selected_tabs:
            st.error("Select at least one tab.")
        else:
            st.session_state.results    = {}
            st.session_state.tab_status = {t: "pending" for t in selected_tabs}
            st.session_state.analysis_run = True
            st.session_state.selected_tabs = selected_tabs
            st.session_state.pop("doc_digest", None)
            st.session_state.pop("doc_raw", None)
            st.rerun()

    if run_disabled:
        st.caption("Upload at least one document to begin.")

    st.markdown("")
    st.caption("v2.0 · ICA · claude-sonnet-4-5")


# ── HERO HEADER ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <div class="hero-icon">💡</div>
  <div>
    <h1>Marketing Intelligence Dashboard</h1>
    <p>Upload analyst reports, white papers, competitor documents, or any research — get a full 10-tab intelligence brief in minutes.</p>
  </div>
  <div class="hero-badge">IBM Consulting · Confidential</div>
</div>
""", unsafe_allow_html=True)


# ── WELCOME STATE ─────────────────────────────────────────────────────────────
if not st.session_state.documents and not st.session_state.analysis_run:

    st.markdown("""
    <div class="step-grid">
      <div class="step-card">
        <div class="step-num">1</div>
        <h4>Upload Documents</h4>
        <p>Add PDFs, Word docs, PowerPoints, CSVs or spreadsheets using the sidebar uploader.</p>
      </div>
      <div class="step-card">
        <div class="step-num">2</div>
        <h4>Select Output Tabs</h4>
        <p>Choose which of the 10 intelligence tabs to generate — or select all for the full brief.</p>
      </div>
      <div class="step-card">
        <div class="step-num">3</div>
        <h4>Run &amp; Export</h4>
        <p>Click <strong>Run Analysis</strong>. Download results as Markdown or a tabbed HTML report.</p>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### What this dashboard generates")
    cap_data = [
        ("📋", "Executive Summary",       "Top 10 findings, risks, opportunities & 90-day actions"),
        ("✍️", "Blog Content",            "3 ready-to-brief content ideas with stats & CTAs"),
        ("🔵", "IBM Priorities",          "Alignment to Cybersecurity & Autonomous Security priorities"),
        ("📅", "Focus Areas & Agendas",   "Strategic focus areas with structured meeting templates"),
        ("📣", "Social Media Hub",        "LinkedIn posts, carousels, polls & infographic concepts"),
        ("✉️", "Email Generator",         "IBM-compliant emails for clients, prospects & internal"),
        ("🔮", "Industry Outlook",        "12 / 24 / 36-month market outlook with APAC spotlight"),
        ("📈", "Technology Trends",       "Ranked trend analysis with IBM marketing implications"),
        ("🏆", "Competitive Intel",       "Competitor landscape vs IBM with white-space opportunities"),
        ("🎯", "Final Deliverable",       "Top 5 opportunities, threats, campaigns & talking points"),
    ]
    cols = st.columns(2)
    for i, (icon, title, desc) in enumerate(cap_data):
        with cols[i % 2]:
            st.markdown(f"""
            <div class="cap-card">
              <div class="cap-icon">{icon}</div>
              <div><strong>{title}</strong><span>{desc}</span></div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("")


# ── ANALYSIS ENGINE ───────────────────────────────────────────────────────────
if st.session_state.analysis_run and st.session_state.documents:
    selected_tabs = st.session_state.get("selected_tabs", list(TAB_REGISTRY.keys()))
    pending = [t for t in selected_tabs if st.session_state.tab_status.get(t) == "pending"]

    if pending:
        progress_bar = st.progress(0, text="Preparing…")
        status_text  = st.empty()

        if "doc_digest" not in st.session_state:
            status_text.info("Compressing documents into intelligence digest — this runs once and speeds up all tabs…")
            digest, raw = build_pre_summarised_context(st.session_state.documents)
            st.session_state.doc_digest = digest
            st.session_state.doc_raw    = raw
            ratio = int((1 - len(digest) / max(len(raw), 1)) * 100)
            status_text.success(f"Digest ready — {len(digest):,} chars ({ratio}% compressed from {len(raw):,} chars raw)")
            time.sleep(0.8)
        else:
            status_text.success("Using cached digest from previous run.")

        doc_context = st.session_state.doc_digest
        total       = len(selected_tabs)
        done_count  = sum(1 for t in selected_tabs if st.session_state.tab_status.get(t) == "done")
        progress_bar.progress(done_count / max(total, 1), text="Generating tabs in parallel…")

        def _run_tab(tab_name: str) -> tuple:
            fn = TAB_REGISTRY[tab_name]
            sys_p, usr_p = fn(doc_context)
            return tab_name, call_ica(sys_p, usr_p, max_tokens=4096)

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(_run_tab, t): t for t in pending}
            for future in as_completed(futures):
                tab_name, result = future.result()
                st.session_state.tab_status[tab_name] = (
                    "error" if result.startswith("[ERROR]") or result.startswith("[HTTP ERROR]") else "done"
                )
                st.session_state.results[tab_name] = result
                done_count += 1
                progress_bar.progress(done_count / max(total, 1), text=f"Done: {tab_name} ({done_count}/{total})")

        progress_bar.progress(1.0, text="All tabs generated!")
        status_text.empty()
        time.sleep(0.8)
        st.rerun()


# ── RESULTS DASHBOARD ─────────────────────────────────────────────────────────
if st.session_state.results:
    selected_tabs = st.session_state.get("selected_tabs", list(TAB_REGISTRY.keys()))
    completed     = [t for t in selected_tabs if st.session_state.tab_status.get(t) == "done"]
    errored       = [t for t in selected_tabs if st.session_state.tab_status.get(t) == "error"]

    # ── Results status bar ────────────────────────────────────────────────────
    st.markdown('<div class="results-bar">', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns([3, 1.2, 1.5, 1.5])
    with c1:
        st.markdown(
            f'<span class="stat"><strong>{len(completed)}</strong> of <strong>{len(selected_tabs)}</strong> tabs generated'
            + (f' &nbsp;<span class="pill-error">{len(errored)} failed</span>' if errored else ' &nbsp;<span class="pill-success">All successful</span>')
            + '</span>',
            unsafe_allow_html=True,
        )
    with c3:
        if completed:
            md_all = "\n\n".join(
                f"# {t}\n\n{st.session_state.results.get(t, '')}" for t in completed
            )
            st.download_button(
                "⬇ Download MD",
                data=md_all.encode("utf-8"),
                file_name="ibm_marketing_intelligence.md",
                mime="text/markdown",
            )
    with c4:
        if completed:
            html_report = build_html_export(st.session_state.results, completed)
            st.download_button(
                "⬇ Export HTML",
                data=html_report.encode("utf-8"),
                file_name="ibm_marketing_intelligence.html",
                mime="text/html",
            )
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Tab output ────────────────────────────────────────────────────────────
    if completed:
        tabs_ui = st.tabs(completed)
        for i, tab_name in enumerate(completed):
            with tabs_ui[i]:
                result_text = st.session_state.results.get(tab_name, "")
                col_left, col_right = st.columns([6, 1])
                with col_right:
                    st.download_button(
                        "⬇ MD",
                        data=result_text.encode("utf-8"),
                        file_name=f"{tab_name.replace(' ', '_').replace('–', '-')}.md",
                        mime="text/markdown",
                        key=f"dl_{tab_name}",
                    )
                st.markdown(f'<div class="output-card">{result_text}</div>', unsafe_allow_html=True)

    # ── Errors ────────────────────────────────────────────────────────────────
    if errored:
        st.markdown("---")
        for t in errored:
            with st.expander(f"Error — {t}"):
                st.error(st.session_state.results.get(t, "Unknown error"))


# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="footer">
  IBM Consulting Marketing Intelligence Agent &nbsp;·&nbsp; Powered by ICA (claude-sonnet-4-5)
  &nbsp;·&nbsp; All outputs require human review before external use &nbsp;·&nbsp; IBM Consulting Confidential
</div>
""", unsafe_allow_html=True)
