import streamlit as st
from ui_styles import inject_styles
from app_bootstrap import init_session_config, start_background_warmup

st.set_page_config(
    page_title="Clinical Guideline RAG Assistant",
    page_icon="⚕️",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": None,
    },
)

inject_styles(hide_sidebar=True)
init_session_config()
start_background_warmup()

st.markdown('<div class="landing-page-root" hidden aria-hidden="true"></div>', unsafe_allow_html=True)

st.markdown("""
<style>
    /* Landing page interactions — scoped via .landing-page-root */
    .stApp:has(.landing-page-root) .landing-hero .app-eyebrow {
        transition: letter-spacing 0.35s ease, color 0.35s ease;
    }
    .stApp:has(.landing-page-root) .landing-hero:hover .app-eyebrow {
        letter-spacing: 0.28em;
        color: #F44174 !important;
    }
    .stApp:has(.landing-page-root) .landing-hero .main-title {
        transition: text-shadow 0.35s ease, transform 0.35s ease;
    }
    .stApp:has(.landing-page-root) .landing-hero:hover .main-title {
        text-shadow: 0 0 28px rgba(244, 65, 116, 0.22);
        transform: translateY(-1px);
    }
    .stApp:has(.landing-page-root) .landing-section-title {
        transition: color 0.3s ease, letter-spacing 0.3s ease;
    }
    .stApp:has(.landing-page-root) .landing-section-title:hover {
        color: #F44174 !important;
        letter-spacing: 0.01em;
    }
    .stApp:has(.landing-page-root) .landing-feature-card {
        transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1),
                    border-color 0.25s ease,
                    box-shadow 0.25s ease,
                    background-color 0.25s ease !important;
        cursor: default;
    }
    .stApp:has(.landing-page-root) .landing-feature-card:hover {
        transform: translateY(-5px);
        border-color: rgba(244, 65, 116, 0.42) !important;
        background: #111111 !important;
        box-shadow: 0 10px 28px rgba(0, 0, 0, 0.28), 0 0 22px rgba(244, 65, 116, 0.14) !important;
    }
    .stApp:has(.landing-page-root) .landing-feature-card:hover h5 {
        color: #FFFFFF !important;
    }
    .stApp:has(.landing-page-root) .landing-feature-card strong {
        transition: color 0.25s ease;
    }
    .stApp:has(.landing-page-root) .landing-feature-card:hover strong {
        color: #FF5A89 !important;
    }
    .stApp:has(.landing-page-root) .landing-detail-heading {
        transition: color 0.25s ease;
    }
    .stApp:has(.landing-page-root) .landing-detail-col:hover .landing-detail-heading {
        color: #F44174 !important;
    }
    .stApp:has(.landing-page-root) .landing-detail-card .tech-table tr {
        transition: background-color 0.2s ease;
    }
    .stApp:has(.landing-page-root) .landing-detail-card .tech-table tr:hover td {
        background-color: rgba(244, 65, 116, 0.05) !important;
    }
    .stApp:has(.landing-page-root) .landing-detail-card .tech-table tr:hover td.tech-key,
    .stApp:has(.landing-page-root) .landing-detail-card .tech-table tr:hover .workflow-key-label {
        color: #FF5A89 !important;
    }
    .stApp:has(.landing-page-root) .tech-table.workflow-table code {
        transition: background-color 0.2s ease, border-color 0.2s ease;
    }
    .stApp:has(.landing-page-root) .tech-table.workflow-table code:hover {
        background-color: rgba(244, 65, 116, 0.2) !important;
        border-color: rgba(244, 65, 116, 0.45) !important;
    }
    .stApp:has(.landing-page-root) div[data-testid="stButton"] button {
        transition: transform 0.2s ease, box-shadow 0.2s ease, background-color 0.2s ease, border-color 0.2s ease !important;
    }
    .stApp:has(.landing-page-root) div[data-testid="stButton"] button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(244, 65, 116, 0.28) !important;
    }
    .stApp:has(.landing-page-root) hr {
        transition: border-color 0.3s ease, opacity 0.3s ease;
    }
    .stApp:has(.landing-page-root) hr:hover {
        border-color: rgba(244, 65, 116, 0.35) !important;
        opacity: 0.9;
    }
    @media (prefers-reduced-motion: reduce) {
        .stApp:has(.landing-page-root) * {
            transition: none !important;
            transform: none !important;
        }
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="landing-hero" style="text-align: center; padding-top: 5vh; padding-bottom: 2vh;">
    <p class="app-eyebrow" style="text-align: center;">Clinical Decision Support Engine</p>
    <div class="main-title" style="text-align: center; font-size: clamp(2.5rem, 7vw, 4.5rem); letter-spacing: -0.04em; margin-bottom: 0.5rem; color: #ffffff;">Clinical Guideline RAG</div>
    <div class="subtitle" style="text-align: center; margin: 0 auto 2.5rem auto; font-size: 1.15rem; color: var(--text-secondary); line-height: 1.6; max-width: 720px;">
        A Retrieval-Augmented Generation (RAG) system for querying, verifying, and comparing evidence-based clinical guidelines using native Snowflake Vector Search.
    </div>
</div>
""", unsafe_allow_html=True)

col_btn_l, col_btn_c, col_btn_r = st.columns([1.5, 1, 1.5])
with col_btn_c:
    if st.button("Open App", type="primary", width="stretch"):
        st.switch_page("pages/Clinical_App.py")

st.markdown("---")

st.markdown('<h3 class="landing-section-title" style="text-align: center; margin-top: 2.5rem !important; margin-bottom: 1.5rem !important; font-size: 1.75rem;">Core Platform Capabilities</h3>', unsafe_allow_html=True)
col_feat1, col_feat2, col_feat3 = st.columns(3)
with col_feat1:
    st.markdown("""
    <div class="glass-card landing-feature-card" style="min-height: 220px; display: flex; flex-direction: column; justify-content: flex-start;">
        <strong style="font-family: var(--font-mono); font-size: 0.7rem; color: var(--brand); letter-spacing: 0.1em; text-transform: uppercase; display: block; margin-bottom: 8px;">01 / SEMANTIC INQUIRY</strong>
        <h5 style="margin: 4px 0 10px 0;">Evidence-Based Q&A</h5>
        <p style="font-size: 0.85rem; color: var(--text-secondary); line-height: 1.5; margin: 0;">Query clinical guidelines using natural language. The system retrieves relevant policy chunks and synthesizes verified summaries bounded strictly by matched context.</p>
    </div>
    """, unsafe_allow_html=True)
with col_feat2:
    st.markdown("""
    <div class="glass-card landing-feature-card" style="min-height: 220px; display: flex; flex-direction: column; justify-content: flex-start;">
        <strong style="font-family: var(--font-mono); font-size: 0.7rem; color: var(--brand); letter-spacing: 0.1em; text-transform: uppercase; display: block; margin-bottom: 8px;">02 / ANCHORED CITATIONS</strong>
        <h5 style="margin: 4px 0 10px 0;">Page-Level Verification</h5>
        <p style="font-size: 0.85rem; color: var(--text-secondary); line-height: 1.5; margin: 0;">Every clinical claim is compiled with inline citation badges. Clicking a citation badge scrolls directly to the verified original context block inside the audit logs.</p>
    </div>
    """, unsafe_allow_html=True)
with col_feat3:
    st.markdown("""
    <div class="glass-card landing-feature-card" style="min-height: 220px; display: flex; flex-direction: column; justify-content: flex-start;">
        <strong style="font-family: var(--font-mono); font-size: 0.7rem; color: var(--brand); letter-spacing: 0.1em; text-transform: uppercase; display: block; margin-bottom: 8px;">03 / COMPARISON SYNTHESIS</strong>
        <h5 style="margin: 4px 0 10px 0;">Guideline Synthesis</h5>
        <p style="font-size: 0.85rem; color: var(--text-secondary); line-height: 1.5; margin: 0;">Perform side-by-side comparative analysis of different guideline sources on any topic to identify clinical alignments, discrepancies, and consensus recommendations.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

st.markdown("""
<style>
    .workflow-key-label,
    .tech-table.workflow-table td.workflow-key {
        color: #F44174 !important;
        font-family: var(--font-mono) !important;
        font-size: 0.7rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.08em !important;
    }
    .tech-table.workflow-table td.workflow-key {
        width: 35% !important;
        vertical-align: top !important;
    }
    .tech-table.workflow-table code {
        color: #F44174 !important;
        background-color: rgba(244, 65, 116, 0.12) !important;
        border: 1px solid rgba(244, 65, 116, 0.25) !important;
        border-radius: 4px !important;
        padding: 0.1em 0.35em !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="landing-detail-grid">
    <div class="landing-detail-col">
        <div class="landing-detail-heading">System Workflow</div>
        <div class="glass-card landing-detail-card">
            <table class="tech-table workflow-table">
                <tr>
                    <td class="workflow-key"><span class="workflow-key-label" style="color: #F44174 !important;">INGESTION &amp; PARSING</span></td>
                    <td>Raw PDF guidelines are processed page-by-page. Text is segmented into chunks using custom boundary-aware overlaps to prevent word splitting.</td>
                </tr>
                <tr>
                    <td class="workflow-key"><span class="workflow-key-label" style="color: #F44174 !important;">VECTOR GENERATION</span></td>
                    <td>Chunks are submitted to either the Gemini (<code>text-embedding-004</code>) or OpenAI (<code>text-embedding-3-small</code>) embeddings engine, outputting 768-dimensional float vectors.</td>
                </tr>
                <tr>
                    <td class="workflow-key"><span class="workflow-key-label" style="color: #F44174 !important;">SNOWFLAKE INDEXING</span></td>
                    <td>Vectors and metadata are batch-inserted into Snowflake using native <code>VECTOR(FLOAT, 768)</code> columns.</td>
                </tr>
                <tr>
                    <td class="workflow-key"><span class="workflow-key-label" style="color: #F44174 !important;">SIMILARITY SEARCH</span></td>
                    <td>Clinical queries are vectorized and compared against the guidelines index using Snowflake's native <code>VECTOR_COSINE_SIMILARITY</code> function.</td>
                </tr>
                <tr>
                    <td class="workflow-key"><span class="workflow-key-label" style="color: #F44174 !important;">CITED SUMMARY</span></td>
                    <td>The top matched chunks are compiled into a system prompt. The LLM generates structured summaries constrained exclusively by the retrieved context.</td>
                </tr>
            </table>
        </div>
    </div>
    <div class="landing-detail-col">
        <div class="landing-detail-heading">Technical Stack Specifications</div>
        <div class="glass-card landing-detail-card">
            <table class="tech-table">
                <tr>
                    <td class="tech-key">DATABASE</td>
                    <td>Snowflake (Native Vector Data Type)</td>
                </tr>
                <tr>
                    <td class="tech-key">LLM CLIENTS</td>
                    <td>Google GenAI (Gemini) / OpenAI API</td>
                </tr>
                <tr>
                    <td class="tech-key">EMBEDDINGS</td>
                    <td>Gemini 004 / OpenAI 3-Small (Normalized to 768-dim)</td>
                </tr>
                <tr>
                    <td class="tech-key">PARSING LAYER</td>
                    <td>PyPDF (Page-level boundary-aware parser)</td>
                </tr>
                <tr>
                    <td class="tech-key">FRONTEND</td>
                    <td>Streamlit (Custom CSS adaptation of Deep Research Design System)</td>
                </tr>
                <tr>
                    <td class="tech-key">TEST SUITE</td>
                    <td>Pytest (12 integration and vector mocks)</td>
                </tr>
            </table>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)
