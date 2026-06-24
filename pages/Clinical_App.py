import re
import streamlit as st
import pandas as pd
from config import AppConfig
from vector_store import SnowflakeVectorStore
from ingestion import DEFAULT_GUIDELINES
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
)

inject_styles()
init_session_config()
start_background_warmup()

# Reuse resources pre-warmed on the landing page
ingest_pipeline, rag_pipeline, store = get_app_resources()

# Title Area for App
st.markdown('<p class="app-eyebrow">Clinical Decision Support Engine</p>', unsafe_allow_html=True)
st.markdown('<div class="main-title">Clinical Guideline RAG</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Search, query, and compare evidence-based clinical guidelines using native Snowflake Vector Search and LLMs</div>', unsafe_allow_html=True)

# ================= MAIN AREA: TABS (rendered before sidebar so UI appears instantly) =================
tab_qa, tab_compare, tab_docs = st.tabs([
    "CLINICAL INQUIRY", 
    "COMPARATIVE ANALYSIS", 
    "GUIDELINES HUB"
])

# ----------------- TAB 1: Q&A ASSISTANT -----------------
with tab_qa:
    st.markdown("### Clinical Guideline Q&A")
    st.write("Submit a query to retrieve evidence-based recommendations complete with page-level citations.")
    
    # Preset queries to guide user
    presets = [
        "What are the dosage guidelines for initiating opioid therapy in patients with chronic pain?",
        "What are the preferred short-course treatment regimens for latent tuberculosis infection?",
        "When is it recommended to prescribe naloxone to outpatients receiving opioid therapy?",
        "What is the recommended dosage and duration for the isoniazid and rifapentine regimen?"
    ]
    
    use_preset = st.toggle("Use Sample Question", value=False)
    
    if use_preset:
        query_text = st.selectbox("Sample Clinical Inquiries", presets)
    else:
        query_text = st.text_input("Clinical Query Input", 
                                  value="",
                                  placeholder="e.g., How often should pain and function be assessed after starting opioids?")
    
    search_col, doc_filter_col = st.columns([3, 1], vertical_alignment="bottom")
    cached_doc_names = [d["document_name"] for d in get_indexed_documents_cached()]
    with doc_filter_col:
        active_filter = st.selectbox("Source Guideline Filter", ["All Documents"] + cached_doc_names)
        doc_filter = None if active_filter == "All Documents" else active_filter
        
    with search_col:
        run_query = st.button("Generate Answer", type="primary", width="stretch")
        
    if run_query and query_text.strip():
        if check_requirements():
            with st.spinner("Retrieving evidence and generating answer..."):
                try:
                    result = rag_pipeline.query(
                        user_query=query_text,
                        limit=6,
                        doc_filter=doc_filter
                    )
                    
                    # Display Answer
                    st.markdown("---")
                    st.markdown("#### Guidance Summary")
                    
                    # Regex replacement to format inline citations [Source X, p. Y] or [Source X] as pills
                    import re
                    ans_formatted = result["answer"]
                    # Replace e.g., [Source X, p. Y] or [Source X] with a styled link
                    ans_formatted = re.sub(
                        r'\[Source\s*\[?(\d+)\]?(?:,\s*p\.\s*(\d+))?\]',
                        lambda m: f'<a class="citation-link" href="#source-{m.group(1)}">S{m.group(1)}' + (f', p. {m.group(2)}' if m.group(2) else '') + '</a>',
                        ans_formatted
                    )
                    
                    st.markdown('<div class="glow-card">', unsafe_allow_html=True)
                    st.markdown(ans_formatted, unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Display Confidence Meter
                    score = result["confidence_score"]
                    level = result["confidence_level"]
                    
                    # Color coding logic using design system variables
                    color = "hsl(0, 85%, 60%)"  # Red
                    if level == "High":
                        color = "var(--success)"
                    elif level == "Medium":
                        color = "var(--warning)"
                        
                    st.markdown("#### Retrieval Confidence & Alignment")
                    metric_cols = st.columns([1, 4])
                    with metric_cols[0]:
                        st.markdown(f"<h3 style='color:{color}; margin:0; font-family:var(--font-mono); font-size:1.8rem;'>{score*100:.1f}%</h3>", unsafe_allow_html=True)
                        st.markdown(f"**Confidence Level:** <span style='color:{color}; font-weight:600;'>{level}</span>", unsafe_allow_html=True)
                    with metric_cols[1]:
                        st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
                        st.progress(score)
                        st.caption("Confidence percentage is derived from the mean cosine similarity of the top retrieved context chunks.")
                    
                    # Display Supporting Passages
                    st.markdown("---")
                    with st.expander("Supporting Context & Citation Source Logs", expanded=False):
                        for s in result["sources"]:
                            # Extract the index digit from tag, e.g. "Source [1]" -> "1"
                            idx_match = re.search(r'\d+', s['source_tag'])
                            idx_str = idx_match.group(0) if idx_match else "1"
                            st.markdown(f"""
                            <div class="glass-card" id="source-{idx_str}">
                                <strong style="font-family: var(--font-mono); font-size: 0.85rem; color: var(--ds-white);">📄 {s['document_name']} (Page {s['page_number']})</strong> 
                                <span class="status-badge status-success" style="float:right;">Match score: {s['similarity']*100:.1f}%</span>
                                <hr style="margin: 12px 0; border: none; border-top: 1px solid var(--border-color);"/>
                                <p style="font-size:0.95rem; line-height:1.6; color:var(--text-secondary); font-style:italic;">"{s['chunk_text']}"</p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                except Exception as e:
                    st.error(f"Error executing RAG Pipeline: {e}")
 
# ----------------- TAB 2: COMPARATIVE ANALYSIS -----------------
with tab_compare:
    st.markdown("### Cross-Guideline Comparison")
    st.write("Evaluate multiple clinical guidelines side-by-side to analyze alignments, discrepancies, and consensus recommendations.")
    
    available_docs = [d["document_name"] for d in get_indexed_documents_cached()]
        
    if len(available_docs) < 2:
        st.warning("⚠️ Guideline comparison requires at least 2 documents indexed in the Snowflake database. Currently indexed: " + str(available_docs))
    else:
        col_a, col_b = st.columns(2)
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
                            
                            st.markdown("---")
                            st.markdown("#### 📈 Comparative Synthesis")
                            
                            # Run citation formatting on comparison text in case any citations exist
                            import re
                            comp_formatted = result["comparison_text"]
                            comp_formatted = re.sub(
                                r'\[Source\s*\[?(\d+)\]?(?:,\s*p\.\s*(\d+))?\]',
                                lambda m: f'<a class="citation-link" href="#source-{m.group(1)}">S{m.group(1)}' + (f', p. {m.group(2)}' if m.group(2) else '') + '</a>',
                                comp_formatted
                            )
                            
                            st.markdown('<div class="glow-card">', unsafe_allow_html=True)
                            st.markdown(comp_formatted, unsafe_allow_html=True)
                            st.markdown('</div>', unsafe_allow_html=True)
                            
                            # Display references inside expandable tabs
                            col_ref_a, col_ref_b = st.columns(2)
                            with col_ref_a:
                                with st.expander(f"Supporting Context: {doc_a}"):
                                    for c in result["sources_a"]:
                                        st.markdown(f"""
                                        <div class="glass-card" style="padding: 16px !important; margin-bottom: 12px !important;">
                                            <strong style="font-family: var(--font-mono); font-size: 0.8rem; color: var(--ds-white);">Page {c['page_number']}</strong>
                                            <span class="status-badge status-success" style="float:right;">Match: {c['similarity']*100:.1f}%</span>
                                            <hr style="margin: 8px 0; border: none; border-top: 1px solid var(--border-color);"/>
                                            <p style="font-size:0.9rem; line-height:1.5; color:var(--text-secondary); margin: 0; font-style:italic;">"{c['chunk_text']}"</p>
                                        </div>
                                        """, unsafe_allow_html=True)
                            with col_ref_b:
                                with st.expander(f"Supporting Context: {doc_b}"):
                                    for c in result["sources_b"]:
                                        st.markdown(f"""
                                        <div class="glass-card" style="padding: 16px !important; margin-bottom: 12px !important;">
                                            <strong style="font-family: var(--font-mono); font-size: 0.8rem; color: var(--ds-white);">Page {c['page_number']}</strong>
                                            <span class="status-badge status-success" style="float:right;">Match: {c['similarity']*100:.1f}%</span>
                                            <hr style="margin: 8px 0; border: none; border-top: 1px solid var(--border-color);"/>
                                            <p style="font-size:0.9rem; line-height:1.5; color:var(--text-secondary); margin: 0; font-style:italic;">"{c['chunk_text']}"</p>
                                        </div>
                                        """, unsafe_allow_html=True)
                        except Exception as e:
                            st.error(f"Error performing comparison: {e}")

# ----------------- TAB 3: GUIDELINES HUB -----------------
with tab_docs:
    st.markdown("### Guidelines Repository & Ingestion")
    
    upload_custom = st.toggle("Upload Custom Guidelines", value=False)
    
    if not upload_custom:
        # Section 1: Ingest Default Public Guidelines (Example Documents)
        st.markdown("#### Ingest Standard Reference Guidelines")
        st.write("Fetch, segment, and vector-embed standard reference guidelines directly into the Snowflake database schema.")
        
        col_dl_1, col_dl_2 = st.columns(2)
        with col_dl_1:
            st.markdown(f"""
            <div class="glass-card">
                <h5>CDC Opioid Prescribing Practice Guideline (2022)</h5>
                <p style="font-size:0.85rem; color: var(--text-secondary); line-height: 1.5; margin-bottom: 12px;">Replaces the 2016 guideline. Outlines 12 practice recommendations for chronic and acute pain management.</p>
                <a href="{DEFAULT_GUIDELINES["CDC Opioid Prescribing Guideline (2022)"]["url"]}" target="_blank" style="font-size:0.8rem; color: var(--primary-accent); text-decoration:none; font-family: var(--font-mono); font-weight: 600;">🔗 ORIGINAL PDF LINK</a>
            </div>
            """, unsafe_allow_html=True)
            
        with col_dl_2:
            st.markdown(f"""
            <div class="glass-card">
                <h5>CDC Latent Tuberculosis Treatment Guideline (2020)</h5>
                <p style="font-size:0.85rem; color: var(--text-secondary); line-height: 1.5; margin-bottom: 12px;">Outlines guidelines for treatment of latent tuberculosis infection in the US, detailing preferred short-course regimens.</p>
                <a href="{DEFAULT_GUIDELINES["CDC Latent Tuberculosis Treatment Guideline (2020)"]["url"]}" target="_blank" style="font-size:0.8rem; color: var(--primary-accent); text-decoration:none; font-family: var(--font-mono); font-weight: 600;">🔗 ORIGINAL PDF LINK</a>
            </div>
            """, unsafe_allow_html=True)
            
        ingest_defaults = st.button("Ingest Reference Guidelines", type="primary", width="stretch")
        
        # Progress UI for default ingestion
        if ingest_defaults:
            if check_requirements():
                progress_bar = st.progress(0.0)
                status_text = st.empty()
                
                try:
                    # 1. Download
                    status_text.text("Downloading default guidelines PDFs...")
                    progress_bar.progress(0.1)
                    
                    cdc_path = ingest_pipeline.download_default_pdf("CDC Opioid Prescribing Guideline (2022)")
                    tb_path = ingest_pipeline.download_default_pdf("CDC Latent Tuberculosis Treatment Guideline (2020)")
                    
                    progress_bar.progress(0.2)
                    
                    # 2. Ingest CDC
                    status_text.text("Ingesting CDC Opioids Guideline (estimating ~60-80 pages)...")
                    def cdc_progress(current, total, msg):
                        ratio = 0.2 + (current / total) * 0.4
                        progress_bar.progress(min(0.6, ratio))
                        status_text.text(f"CDC Opioids: {msg}")
                        
                    cdc_chunks = ingest_pipeline.process_and_index_pdf(cdc_path, "CDC Opioid Prescribing Guideline (2022)", cdc_progress)
                    
                    # 3. Ingest TB
                    status_text.text("Ingesting CDC Tuberculosis Guideline (estimating ~20-30 pages)...")
                    def tb_progress(current, total, msg):
                        ratio = 0.6 + (current / total) * 0.35
                        progress_bar.progress(min(0.95, ratio))
                        status_text.text(f"CDC TB: {msg}")
                        
                    tb_chunks = ingest_pipeline.process_and_index_pdf(tb_path, "CDC Latent Tuberculosis Treatment Guideline (2020)", tb_progress)
                    
                    progress_bar.progress(1.0)
                    status_text.success(f"Successfully loaded Guidelines into Snowflake! Indexed {cdc_chunks} CDC Opioid chunks and {tb_chunks} CDC TB chunks.")
                    refresh_snowflake_data()
                    st.rerun()
                    
                except Exception as e:
                    status_text.error(f"Ingestion failed: {e}")
                    
    else:
        # Section 2: Upload Custom Guidelines
        st.markdown("#### Ingest Custom Policy Document")
        st.write("Upload institutional policies or local clinical guidelines (PDF format) to segment, vector-embed, and index.")
        
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
                            progress_callback=upload_progress
                        )
                        prog_bar.progress(1.0)
                        status_lbl.success(f"Successfully ingested custom guideline '{uploaded_file.name}'! Generated {chunk_count} vector chunks.")
                        refresh_snowflake_data()
                        st.rerun()
                    except Exception as e:
                        status_lbl.error(f"Error during upload: {e}")
                        
    st.markdown("---")
    
    # Section 3: Manage Index
    st.markdown("#### Guidelines Index Status")
    st.write("Manage active guideline documents inside the vector schema. Rebuild or drop indices as required.")
    
    indexed_docs = get_indexed_documents_cached()
    db_status, _, db_ok = get_snowflake_status_cached()
    if db_ok:
        try:
            if not indexed_docs:
                st.info("No documents are currently indexed in the Snowflake vector database.")
            else:
                # Convert list of dicts to DataFrame for neat visualization
                df_docs = pd.DataFrame(indexed_docs)
                df_docs.columns = ["Document Name", "Chunk Count", "First Page", "Last Page"]
                
                st.dataframe(df_docs, width="stretch")
                
                # Delete control
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
