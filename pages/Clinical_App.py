import html
import re
import streamlit as st
import pandas as pd
from config import AppConfig
from vector_store import SnowflakeVectorStore
from guidelines_catalog import GUIDELINES_CATALOG, GUIDELINES_PAGE_SIZE
from ui_styles import inject_styles
from app_bootstrap import (
    init_session_config,
    check_requirements,
    get_snowflake_status_cached,
    ensure_snowflake_connected,
    get_indexed_documents_cached,
    refresh_snowflake_data,
    get_app_resources,
    start_background_warmup,
)

st.set_page_config(
    page_title="Clinical Guideline RAG Assistant",
    page_icon="⚕️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": None,
    },
)

inject_styles()
init_session_config()
start_background_warmup()

# Reuse resources pre-warmed on the landing page
ingest_pipeline, rag_pipeline, store = get_app_resources()


@st.dialog("Indexing guideline", width="medium", dismissible=False)
def ingest_guideline_dialog(title: str) -> None:
    st.caption("Embedding document chunks into the Snowflake vector index.")
    st.markdown(f"**{html.escape(title)}**", unsafe_allow_html=True)
    progress_bar = st.progress(0.0)
    status_text = st.empty()
    try:

        def ingest_progress(current, total, msg):
            progress_bar.progress(current / total if total else 0.0)
            status_text.text(msg)

        chunk_count = ingest_pipeline.ingest_default_guideline(
            title,
            progress_callback=ingest_progress,
        )
        progress_bar.progress(1.0)
        status_text.success(f"Indexed — {chunk_count} chunks loaded.")
        refresh_snowflake_data()
        st.rerun()
    except Exception as e:
        status_text.error(f"Ingestion failed: {e}")
        if st.button("Close", key="ingest_dialog_close"):
            st.rerun()


@st.dialog("Indexing guidelines", width="medium", dismissible=False)
def ingest_page_dialog(guideline_titles: list[str]) -> None:
    st.caption("Batch embedding all guidelines on this page.")
    progress_bar = st.progress(0.0)
    status_text = st.empty()
    total_chunks = 0
    try:
        for idx, title in enumerate(guideline_titles):
            status_text.text(f"Processing {idx + 1}/{len(guideline_titles)}...")

            def page_progress(current, total, msg, base=idx, count=len(guideline_titles)):
                doc_ratio = (base + (current / total if total else 0)) / count
                progress_bar.progress(min(0.99, doc_ratio))
                status_text.text(f"[{base + 1}/{count}] {msg}")

            total_chunks += ingest_pipeline.ingest_default_guideline(
                title,
                progress_callback=page_progress,
            )

        progress_bar.progress(1.0)
        status_text.success(
            f"Ingested {len(guideline_titles)} guidelines — {total_chunks} total chunks."
        )
        refresh_snowflake_data()
        st.rerun()
    except Exception as e:
        status_text.error(f"Batch ingestion failed: {e}")
        if st.button("Close", key="batch_ingest_dialog_close"):
            st.rerun()


def format_answer_citations(text: str) -> str:
    """Convert [Source N] / [Source N, p. X] markers into clickable citation pills."""
    return re.sub(
        r'\[Source\s*\[?(\d+)\]?(?:,\s*p\.\s*(\d+))?\]',
        lambda m: (
            f'<a class="citation-link" href="#source-{m.group(1)}">S{m.group(1)}'
            + (f', p. {m.group(2)}' if m.group(2) else '')
            + '</a>'
        ),
        text,
    )

# Title Area for App
st.markdown('<p class="app-eyebrow">Clinical Decision Support Engine</p>', unsafe_allow_html=True)
st.markdown('<div class="main-title">Clinical Guideline RAG</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Search, query, and compare evidence-based clinical guidelines using native Snowflake Vector Search and LLMs</div>', unsafe_allow_html=True)

# ================= MAIN AREA: TABS (rendered before sidebar so UI appears instantly) =================
tab_qa, tab_docs, tab_compare = st.tabs([
    "CLINICAL INQUIRY",
    "GUIDELINES HUB",
    "COMPARATIVE ANALYSIS",
])

# ----------------- TAB 1: Q&A ASSISTANT -----------------
with tab_qa:
    st.markdown("""
    <div class="tab-section">
        <div class="section-header">
            <p class="section-subheader">Evidence retrieval</p>
            <h3>Clinical Guideline Q&amp;A</h3>
            <p class="section-lead">Submit a query to retrieve evidence-based recommendations with page-level citations.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Preset queries to guide user
    presets = [
        "What are the dosage guidelines for initiating opioid therapy in patients with chronic pain?",
        "What are the preferred short-course treatment regimens for latent tuberculosis infection?",
        "When is it recommended to prescribe naloxone to outpatients receiving opioid therapy?",
        "What is the recommended dosage and duration for the isoniazid and rifapentine regimen?"
    ]
    
    use_preset = st.toggle("Use Sample Question", value=True)
    
    if use_preset:
        query_text = st.selectbox("Sample Clinical Inquiries", presets)
    else:
        query_text = st.text_input("Clinical Query Input", 
                                  value="",
                                  placeholder="e.g., How often should pain and function be assessed after starting opioids?")
    
    search_col, doc_filter_col = st.columns([3, 1], gap="medium", vertical_alignment="bottom")
    cached_doc_names = [d["document_name"] for d in get_indexed_documents_cached()]
    with doc_filter_col:
        active_filter = st.selectbox("Source Guideline Filter", ["All Documents"] + cached_doc_names)
        doc_filter = None if active_filter == "All Documents" else active_filter
        
    with search_col:
        run_query = st.button("Generate Answer", type="primary", width="stretch")
        
    if run_query and query_text.strip():
        if check_requirements():
            try:
                with st.spinner("Retrieving evidence from guidelines..."):
                    prepared = rag_pipeline.prepare_query(
                        user_query=query_text,
                        limit=6,
                        doc_filter=doc_filter,
                    )

                if prepared["empty_message"]:
                    st.warning(prepared["empty_message"])
                else:
                    st.markdown('<p class="section-subheader" style="margin-top:1.5rem;">Guidance summary</p>', unsafe_allow_html=True)

                    answer_ph = st.empty()
                    full_answer = ""
                    for chunk in AppConfig.generate_completion_stream(
                        prepared["system_prompt"],
                        prepared["user_prompt"],
                    ):
                        full_answer += chunk
                        answer_ph.markdown(
                            f'<div class="glow-card answer-streaming">{full_answer}</div>',
                            unsafe_allow_html=True,
                        )

                    ans_formatted = format_answer_citations(full_answer)
                    answer_ph.markdown(
                        f'<div class="glow-card">{ans_formatted}</div>',
                        unsafe_allow_html=True,
                    )

                    score = prepared["confidence_score"]
                    level = prepared["confidence_level"]

                    color = "hsl(0, 85%, 60%)"
                    if level == "High":
                        color = "var(--success)"
                    elif level == "Medium":
                        color = "var(--warning)"

                    st.markdown('<div class="confidence-panel">', unsafe_allow_html=True)
                    st.markdown('<p class="section-subheader">Retrieval confidence</p>', unsafe_allow_html=True)
                    metric_cols = st.columns([1, 4], gap="large")
                    with metric_cols[0]:
                        st.markdown(
                            f'<p class="confidence-score" style="color:{color};">{score*100:.1f}%</p>',
                            unsafe_allow_html=True,
                        )
                        st.markdown(
                            f'<p class="confidence-label">Confidence level: <strong style="color:{color};">{level}</strong></p>',
                            unsafe_allow_html=True,
                        )
                    with metric_cols[1]:
                        st.progress(score)
                        st.caption(
                            "Derived from the mean cosine similarity of the top retrieved context chunks."
                        )
                    st.markdown("</div>", unsafe_allow_html=True)

                    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
                    with st.expander("Supporting context & citation sources", expanded=False):
                        for s in prepared["sources"]:
                            idx_match = re.search(r'\d+', s['source_tag'])
                            idx_str = idx_match.group(0) if idx_match else "1"
                            st.markdown(f"""
                            <div class="glass-card source-card" id="source-{idx_str}">
                                <div class="source-card-header">
                                    <p class="source-card-title">{html.escape(s['document_name'])} · Page {s['page_number']}</p>
                                    <span class="status-badge status-success">Match {s['similarity']*100:.1f}%</span>
                                </div>
                                <p class="source-card-quote">"{html.escape(s['chunk_text'])}"</p>
                            </div>
                            """, unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Error executing RAG Pipeline: {e}")
 
# ----------------- TAB 2: GUIDELINES HUB -----------------
with tab_docs:
    st.markdown("""
    <div class="tab-section">
        <div class="section-header">
            <p class="section-subheader">Repository</p>
            <h3>Guidelines Hub</h3>
            <p class="section-lead">Browse, ingest, and manage CDC MMWR clinical guidelines in your Snowflake vector index.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    upload_custom = st.toggle("Upload custom guidelines", value=False)

    if not upload_custom:
        st.markdown(
            f'<p class="section-lead" style="margin-bottom:1rem;">'
            f'<strong>{len(GUIDELINES_CATALOG)}</strong> verified CDC guidelines available for ingestion.</p>',
            unsafe_allow_html=True,
        )

        if "guidelines_page" not in st.session_state:
            st.session_state.guidelines_page = 0

        total_guidelines = len(GUIDELINES_CATALOG)
        total_pages = max(1, (total_guidelines + GUIDELINES_PAGE_SIZE - 1) // GUIDELINES_PAGE_SIZE)
        current_page = max(0, min(st.session_state.guidelines_page, total_pages - 1))
        st.session_state.guidelines_page = current_page

        page_start = current_page * GUIDELINES_PAGE_SIZE
        page_items = GUIDELINES_CATALOG[page_start:page_start + GUIDELINES_PAGE_SIZE]
        indexed_names = {d["document_name"] for d in get_indexed_documents_cached()}

        nav_prev, nav_info, nav_next = st.columns([1, 2, 1], gap="medium", vertical_alignment="center")
        with nav_prev:
            if st.button("← Previous", disabled=current_page == 0, key="guidelines_prev"):
                st.session_state.guidelines_page = current_page - 1
                st.rerun()
        with nav_info:
            st.markdown(
                f"""
                <div class="guidelines-toolbar-meta">
                    Page <strong>{current_page + 1}</strong> of <strong>{total_pages}</strong>
                    &nbsp;·&nbsp; Showing <strong>{len(page_items)}</strong> of <strong>{total_guidelines}</strong>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with nav_next:
            if st.button("Next →", disabled=current_page >= total_pages - 1, key="guidelines_next"):
                st.session_state.guidelines_page = current_page + 1
                st.rerun()

        st.markdown('<div class="guidelines-grid-row">', unsafe_allow_html=True)
        for row_start in range(0, len(page_items), 2):
            card_cols = st.columns(2, gap="medium")
            for col_idx, guideline in enumerate(page_items[row_start:row_start + 2]):
                is_indexed = guideline["title"] in indexed_names
                status_badge = (
                    "<span class='status-badge status-success'>Indexed</span>"
                    if is_indexed
                    else "<span class='status-badge status-warning'>Not indexed</span>"
                )
                safe_title = html.escape(guideline["title"])
                safe_desc = html.escape(guideline["description"])
                safe_url = html.escape(guideline["url"])
                with card_cols[col_idx]:
                    st.markdown(
                        f"""
                        <div class="guideline-entry-shell">
                            <div class="guideline-card-header">{status_badge}</div>
                            <h5 class="guideline-title">{safe_title}</h5>
                            <p class="guideline-desc">{safe_desc}</p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    action_pdf, action_ingest = st.columns(2, gap="small", vertical_alignment="center")
                    with action_pdf:
                        st.markdown(
                            f"""
                            <a class="guideline-action-btn guideline-action-pdf"
                               href="{safe_url}" target="_blank" rel="noopener noreferrer">
                                <svg class="guideline-action-icon" width="13" height="13" viewBox="0 0 24 24"
                                     fill="none" stroke="currentColor" stroke-width="2"
                                     stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                                    <polyline points="14 2 14 8 20 8"/>
                                    <line x1="16" y1="13" x2="8" y2="13"/>
                                    <line x1="16" y1="17" x2="8" y2="17"/>
                                </svg>
                                <span>View PDF</span>
                            </a>
                            """,
                            unsafe_allow_html=True,
                        )
                    with action_ingest:
                        if st.button(
                            "Ingest",
                            key=f"ingest_{guideline['code']}",
                            type="secondary",
                            width="stretch",
                        ):
                            if check_requirements():
                                ingest_guideline_dialog(guideline["title"])
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="batch-ingest-row">', unsafe_allow_html=True)
        _batch_left, batch_btn_col, _batch_right = st.columns([1, 2, 1])
        with batch_btn_col:
            if st.button(
                "Ingest all on this page",
                type="secondary",
                key="batch_ingest_page",
            ):
                if check_requirements():
                    ingest_page_dialog([g["title"] for g in page_items])
        st.markdown("</div>", unsafe_allow_html=True)

    else:
        st.markdown("""
        <div class="section-header">
            <p class="section-subheader">Custom upload</p>
            <h4>Ingest policy document</h4>
            <p class="section-lead">Upload institutional policies or local clinical guidelines in PDF format.</p>
        </div>
        """, unsafe_allow_html=True)

        uploaded_file = st.file_uploader("Select PDF Document", type="pdf")
        if uploaded_file is not None:
            upload_btn = st.button("Ingest Custom Guideline")
            if upload_btn:
                if check_requirements():
                    prog_bar = st.progress(0.0)
                    status_lbl = st.empty()

                    try:
                        def upload_progress(current, total, msg):
                            prog_bar.progress(current / total)
                            status_lbl.text(msg)

                        file_bytes = uploaded_file.read()
                        chunk_count = ingest_pipeline.ingest_uploaded_pdf(
                            file_bytes=file_bytes,
                            filename=uploaded_file.name,
                            progress_callback=upload_progress,
                        )
                        prog_bar.progress(1.0)
                        status_lbl.success(
                            f"Successfully ingested custom guideline '{uploaded_file.name}'! "
                            f"Generated {chunk_count} vector chunks."
                        )
                        refresh_snowflake_data()
                        st.rerun()
                    except Exception as e:
                        status_lbl.error(f"Error during upload: {e}")

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    st.markdown("""
    <div class="section-header">
        <p class="section-subheader">Index management</p>
        <h4>Guidelines index status</h4>
        <p class="section-lead">View indexed documents and remove entries from the vector schema.</p>
    </div>
    """, unsafe_allow_html=True)

    indexed_docs = get_indexed_documents_cached()
    db_status, _, db_ok = get_snowflake_status_cached()
    if db_ok:
        try:
            if not indexed_docs:
                st.info("No documents are currently indexed in the Snowflake vector database.")
            else:
                df_docs = pd.DataFrame(indexed_docs)
                df_docs.columns = ["Document Name", "Chunk Count", "First Page", "Last Page"]

                st.dataframe(df_docs, width="stretch")

                doc_to_delete = st.selectbox("Select Document to Delete", [d["document_name"] for d in indexed_docs])
                delete_btn = st.button("Drop Document Index", type="secondary")

                if delete_btn:
                    if check_requirements():
                        with st.spinner(f"Removing {doc_to_delete} from Snowflake..."):
                            store.delete_document(doc_to_delete)
                            refresh_snowflake_data()
                            st.success(f"Removed '{doc_to_delete}' successfully!")
                            st.rerun()
        except Exception as e:
            st.error(f"Error loading index: {e}")
    else:
        if db_status == "connecting":
            st.info("Connecting to Snowflake...")
        else:
            st.info("Snowflake is unconfigured or offline. Connect to view indexed files.")

# ----------------- TAB 3: COMPARATIVE ANALYSIS -----------------
with tab_compare:
    st.markdown("""
    <div class="tab-section">
        <div class="section-header">
            <p class="section-subheader">Side-by-side review</p>
            <h3>Cross-guideline comparison</h3>
            <p class="section-lead">Analyze alignments, discrepancies, and consensus across two indexed guidelines.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    available_docs = [d["document_name"] for d in get_indexed_documents_cached()]
        
    if len(available_docs) < 2:
        st.warning("⚠️ Guideline comparison requires at least 2 documents indexed in the Snowflake database. Currently indexed: " + str(available_docs))
    else:
        col_a, col_b = st.columns(2, gap="medium")
        with col_a:
            doc_a = st.selectbox("Guideline A (Baseline)", available_docs, index=0)
        with col_b:
            doc_b = st.selectbox("Guideline B (Comparator)", available_docs, index=1 if len(available_docs) > 1 else 0)
            
        compare_topic = st.text_input("Comparative Inquiry Topic", 
                                      value="What is the initiation threshold and recommended first-line pharmacological agent?",
                                      placeholder="e.g. Follow-up and reassessment intervals after commencing treatment")
        
        run_compare = st.button("Compare Guidelines", type="primary")
        
        if run_compare and compare_topic.strip():
            if check_requirements():
                if doc_a == doc_b:
                    st.warning("Please select two different documents to perform a comparison.")
                else:
                    with st.spinner(f"Comparing {doc_a} and {doc_b}..."):
                        try:
                            result = rag_pipeline.compare_guidelines(
                                clinical_topic=compare_topic,
                                doc_a=doc_a,
                                doc_b=doc_b
                            )
                            
                            st.markdown('<p class="section-subheader" style="margin-top:1.5rem;">Comparative synthesis</p>', unsafe_allow_html=True)
                            
                            comp_formatted = result["comparison_text"]
                            comp_formatted = re.sub(
                                r'\[Source\s*\[?(\d+)\]?(?:,\s*p\.\s*(\d+))?\]',
                                lambda m: f'<a class="citation-link" href="#source-{m.group(1)}">S{m.group(1)}' + (f', p. {m.group(2)}' if m.group(2) else '') + '</a>',
                                comp_formatted
                            )
                            
                            st.markdown('<div class="glow-card">', unsafe_allow_html=True)
                            st.markdown(comp_formatted, unsafe_allow_html=True)
                            st.markdown('</div>', unsafe_allow_html=True)
                            
                            col_ref_a, col_ref_b = st.columns(2, gap="medium")
                            with col_ref_a:
                                with st.expander(f"Supporting context · {doc_a[:48]}{'…' if len(doc_a) > 48 else ''}"):
                                    for c in result["sources_a"]:
                                        st.markdown(f"""
                                        <div class="glass-card source-card">
                                            <div class="source-card-header">
                                                <p class="source-card-title">Page {c['page_number']}</p>
                                                <span class="status-badge status-success">Match {c['similarity']*100:.1f}%</span>
                                            </div>
                                            <p class="source-card-quote">"{html.escape(c['chunk_text'])}"</p>
                                        </div>
                                        """, unsafe_allow_html=True)
                            with col_ref_b:
                                with st.expander(f"Supporting context · {doc_b[:48]}{'…' if len(doc_b) > 48 else ''}"):
                                    for c in result["sources_b"]:
                                        st.markdown(f"""
                                        <div class="glass-card source-card">
                                            <div class="source-card-header">
                                                <p class="source-card-title">Page {c['page_number']}</p>
                                                <span class="status-badge status-success">Match {c['similarity']*100:.1f}%</span>
                                            </div>
                                            <p class="source-card-quote">"{html.escape(c['chunk_text'])}"</p>
                                        </div>
                                        """, unsafe_allow_html=True)
                        except Exception as e:
                            st.error(f"Error performing comparison: {e}")

# ================= SIDEBAR (after main content — does not block tab UI from streaming in) =================
with st.sidebar:
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 20px; padding: 5px 0;">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2ZM17 13H13V17H11V13H7V11H11V7H13V11H17V13Z" fill="var(--brand)"/>
        </svg>
        <span style="font-family: var(--font-mono); font-weight: 700; font-size: 0.85rem; letter-spacing: 0.1em; color: var(--text-primary);">CDSE CORE</span>
    </div>
    """, unsafe_allow_html=True)

    if st.button("← Back to Landing Page", width="stretch"):
        st.switch_page("app.py")

    st.markdown("---")

    if AppConfig.is_demo_mode():
        st.markdown("""
        <div style="background: var(--brand-softer); border: 1px solid var(--border-brand-subtle);
                    border-radius: 8px; padding: 14px 16px; margin-bottom: 8px;">
            <div style="font-family: var(--font-mono); font-size: 0.7rem; font-weight: 700;
                        letter-spacing: 0.12em; color: var(--brand); margin-bottom: 6px;">DEMO MODE</div>
            <div style="font-size: 0.82rem; color: var(--text-secondary); line-height: 1.5;">
                Credentials are pre-configured by the host. Use the <strong>Guidelines Hub</strong> to ingest documents, then explore clinical queries.
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("### Engine Configuration")
        st.session_state["LLM_PROVIDER"] = st.selectbox(
            "LLM API Provider",
            options=["gemini", "openai"],
            index=0 if st.session_state["LLM_PROVIDER"] == "gemini" else 1,
            help="Select the model provider for generating text embeddings and clinical completions."
        )
        if st.session_state["LLM_PROVIDER"] == "gemini":
            st.session_state["GEMINI_API_KEY"] = st.text_input(
                "Gemini API Key", value=st.session_state["GEMINI_API_KEY"], type="password", placeholder="AIzaSy..."
            )
        else:
            st.session_state["OPENAI_API_KEY"] = st.text_input(
                "OpenAI API Key", value=st.session_state["OPENAI_API_KEY"], type="password", placeholder="sk-proj-..."
            )
        st.markdown("---")
        st.markdown("### Snowflake Connection")
        st.session_state["SNOWFLAKE_ACCOUNT"] = st.text_input("Account Identifier", value=st.session_state["SNOWFLAKE_ACCOUNT"], placeholder="xy12345.us-east-1")
        st.session_state["SNOWFLAKE_USER"] = st.text_input("Username", value=st.session_state["SNOWFLAKE_USER"])
        st.session_state["SNOWFLAKE_PASSWORD"] = st.text_input("Password", value=st.session_state["SNOWFLAKE_PASSWORD"], type="password")
        st.session_state["SNOWFLAKE_DATABASE"] = st.text_input("Database Name", value=st.session_state["SNOWFLAKE_DATABASE"], placeholder="CLINICAL_DB")
        st.session_state["SNOWFLAKE_SCHEMA"] = st.text_input("Schema Name", value=st.session_state["SNOWFLAKE_SCHEMA"], placeholder="PUBLIC")
        st.session_state["SNOWFLAKE_WAREHOUSE"] = st.text_input("Warehouse Name", value=st.session_state["SNOWFLAKE_WAREHOUSE"])
        st.markdown("---")
        test_conn = st.button("Test Connection", width="stretch")
        init_db = st.button("Init Schema", width="stretch")
        if test_conn:
            try:
                if SnowflakeVectorStore().test_connection():
                    st.sidebar.success("Successfully connected to Snowflake!")
                else:
                    st.sidebar.error("Failed connection test.")
            except Exception as e:
                st.sidebar.error(f"Connection Error: {e}")
        if init_db:
            try:
                SnowflakeVectorStore().create_schema_and_table()
                refresh_snowflake_data()
                st.sidebar.success("Table schema checked/created successfully!")
                st.rerun()
            except Exception as e:
                st.sidebar.error(f"Initialization Error: {e}")

    st.markdown("### SYSTEM CONNECTIVITY")
    llm_badge = (
        f"<span class='status-badge status-success'>Configured ({st.session_state['LLM_PROVIDER'].upper()})</span>"
        if AppConfig.is_llm_configured()
        else "<span class='status-badge status-error'>API Key Missing</span>"
    )
    st.markdown(f"<div class='status-row'><strong>LLM ENGINE</strong>{llm_badge}</div>", unsafe_allow_html=True)

    needed_sync = get_snowflake_status_cached()[0] == "connecting"
    db_status, guidelines_count, _ = ensure_snowflake_connected()
    if needed_sync and db_status != "connecting":
        st.rerun()
    if db_status == "connected":
        db_badge = "<span class='status-badge status-success'>Connected</span>"
    elif db_status == "connecting":
        db_badge = "<span class='status-badge status-warning'>Connecting...</span>"
    elif db_status == "unconfigured":
        db_badge = "<span class='status-badge status-warning'>Unconfigured</span>"
    else:
        db_badge = "<span class='status-badge status-error'>Offline</span>"

    st.markdown(f"""
    <div class='status-row'><strong>SNOWFLAKE</strong>{db_badge}</div>
    <div class='status-row'>
        <strong>INDEXED GUIDELINES</strong>
        <span class='status-badge' style='background: var(--brand-softer); color: var(--fg-brand-strong); border: 1px solid var(--border-brand-subtle);'>{guidelines_count}</span>
    </div>
    """, unsafe_allow_html=True)
