import streamlit as st
from ui_styles import inject_styles
from app_bootstrap import init_session_config, start_background_warmup

st.set_page_config(
    page_title="Clinical Guideline RAG Assistant",
    page_icon="⚕️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_styles(hide_sidebar=True)
init_session_config()
start_background_warmup()

st.markdown("""
<div style="text-align: center; padding-top: 5vh; padding-bottom: 2vh;">
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

st.markdown('<h3 style="text-align: center; margin-top: 2.5rem !important; margin-bottom: 1.5rem !important; font-size: 1.75rem;">Core Platform Capabilities</h3>', unsafe_allow_html=True)
col_feat1, col_feat2, col_feat3 = st.columns(3)
with col_feat1:
    st.markdown("""
    <div class="glass-card" style="min-height: 220px; display: flex; flex-direction: column; justify-content: flex-start;">
        <strong style="font-family: var(--font-mono); font-size: 0.7rem; color: var(--brand); letter-spacing: 0.1em; text-transform: uppercase; display: block; margin-bottom: 8px;">01 / SEMANTIC INQUIRY</strong>
        <h5 style="margin: 4px 0 10px 0;">Evidence-Based Q&A</h5>
        <p style="font-size: 0.85rem; color: var(--text-secondary); line-height: 1.5; margin: 0;">Query clinical guidelines using natural language. The system retrieves relevant policy chunks and synthesizes verified summaries bounded strictly by matched context.</p>
    </div>
    """, unsafe_allow_html=True)
with col_feat2:
    st.markdown("""
    <div class="glass-card" style="min-height: 220px; display: flex; flex-direction: column; justify-content: flex-start;">
        <strong style="font-family: var(--font-mono); font-size: 0.7rem; color: var(--brand); letter-spacing: 0.1em; text-transform: uppercase; display: block; margin-bottom: 8px;">02 / ANCHORED CITATIONS</strong>
        <h5 style="margin: 4px 0 10px 0;">Page-Level Verification</h5>
        <p style="font-size: 0.85rem; color: var(--text-secondary); line-height: 1.5; margin: 0;">Every clinical claim is compiled with inline citation badges. Clicking a citation badge scrolls directly to the verified original context block inside the audit logs.</p>
    </div>
    """, unsafe_allow_html=True)
with col_feat3:
    st.markdown("""
    <div class="glass-card" style="min-height: 220px; display: flex; flex-direction: column; justify-content: flex-start;">
        <strong style="font-family: var(--font-mono); font-size: 0.7rem; color: var(--brand); letter-spacing: 0.1em; text-transform: uppercase; display: block; margin-bottom: 8px;">03 / COMPARISON SYNTHESIS</strong>
        <h5 style="margin: 4px 0 10px 0;">Guideline Synthesis</h5>
        <p style="font-size: 0.85rem; color: var(--text-secondary); line-height: 1.5; margin: 0;">Perform side-by-side comparative analysis of different guideline sources on any topic to identify clinical alignments, discrepancies, and consensus recommendations.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

col_left, col_right = st.columns(2)
with col_left:
    st.markdown('<h4 style="margin-top: 1.5rem !important; margin-bottom: 1rem !important; font-size: 1.25rem;">System Workflow</h4>', unsafe_allow_html=True)
    st.markdown("""
    <div class="glass-card" style="padding: 24px; min-height: 380px;">
        <ol style="font-size: 0.85rem; color: var(--text-secondary); line-height: 1.7; margin-left: 0; padding-left: 20px; margin-bottom: 0;">
            <li style="margin-bottom: 12px;"><strong>Ingestion & Parsing</strong>: Raw PDF guidelines are processed page-by-page. Text is segmented into chunks using custom boundary-aware overlaps to prevent word splitting.</li>
            <li style="margin-bottom: 12px;"><strong>Vector Generation</strong>: Chunks are submitted to either the Gemini (<code>text-embedding-004</code>) or OpenAI (<code>text-embedding-3-small</code>) embeddings engine, outputting 768-dimensional float vectors.</li>
            <li style="margin-bottom: 12px;"><strong>Snowflake Indexing</strong>: Vectors and metadata are batch-inserted into Snowflake using native <code>VECTOR(FLOAT, 768)</code> columns.</li>
            <li style="margin-bottom: 12px;"><strong>Similarity Search</strong>: Clinical queries are vectorized and compared against the guidelines index using Snowflake's native <code>VECTOR_COSINE_SIMILARITY</code> function.</li>
            <li style="margin-bottom: 0;"><strong>Cited Summary Generation</strong>: The top matched chunks are compiled into a system prompt. The LLM generates structured summaries constrained exclusively by the retrieved context.</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)

with col_right:
    st.markdown('<h4 style="margin-top: 1.5rem !important; margin-bottom: 1rem !important; font-size: 1.25rem;">Technical Stack Specifications</h4>', unsafe_allow_html=True)
    st.markdown("""
    <div class="glass-card" style="padding: 24px; min-height: 380px;">
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
    """, unsafe_allow_html=True)
