import os
import threading
import streamlit as st
from config import AppConfig
from vector_store import SnowflakeVectorStore
from ingestion import IngestionPipeline
from rag_pipeline import RAGPipeline

DEFAULTS = {
    "LLM_PROVIDER": "gemini",
    "SNOWFLAKE_DATABASE": "CLINICAL_DB",
    "SNOWFLAKE_SCHEMA": "PUBLIC",
    "SNOWFLAKE_WAREHOUSE": "COMPUTE_WH",
}

CONFIG_KEYS = [
    "LLM_PROVIDER", "GEMINI_API_KEY", "OPENAI_API_KEY",
    "SNOWFLAKE_USER", "SNOWFLAKE_PASSWORD", "SNOWFLAKE_ACCOUNT",
    "SNOWFLAKE_WAREHOUSE", "SNOWFLAKE_DATABASE", "SNOWFLAKE_SCHEMA",
]

_lock = threading.Lock()
_resources = None
_sf_status = None
_indexed_docs = None
_warmup_started = False


def _get_initial_config_value(key):
    return AppConfig._get_host_setting(key, DEFAULTS.get(key, ""))


def init_session_config():
    """Load config from Streamlit secrets / env. Re-fills empty session values on each run."""
    for key in CONFIG_KEYS:
        host_val = _get_initial_config_value(key)
        if key not in st.session_state or not str(st.session_state.get(key, "")).strip():
            st.session_state[key] = host_val
    if not st.session_state.get("LLM_PROVIDER"):
        st.session_state["LLM_PROVIDER"] = "gemini"


def check_requirements():
    if not AppConfig.is_llm_configured():
        if AppConfig.is_demo_mode():
            st.warning("⚠️ Demo mode is active but the LLM API key is not configured. Add it to Streamlit secrets.")
        else:
            st.warning("⚠️ Please provide your Gemini or OpenAI API Key in the sidebar.")
        return False
    if not (st.session_state["SNOWFLAKE_ACCOUNT"] and st.session_state["SNOWFLAKE_USER"]):
        if AppConfig.is_demo_mode():
            st.warning("⚠️ Demo mode is active but Snowflake credentials are missing. Add them to Streamlit secrets.")
        else:
            st.warning("⚠️ Please configure your Snowflake database connection details in the sidebar.")
        return False
    return True


def _rows_to_indexed_docs(rows):
    return [
        {
            "document_name": row[0],
            "chunk_count": int(row[1]),
            "start_page": int(row[2]),
            "end_page": int(row[3]),
        }
        for row in rows
    ]


def _fetch_snowflake_data_sync():
    """Blocking Snowflake fetch — only for background warm-up or post-ingest refresh."""
    global _sf_status, _indexed_docs
    account = AppConfig.get_setting("SNOWFLAKE_ACCOUNT")
    user = AppConfig.get_setting("SNOWFLAKE_USER")
    if not account or not user:
        status = ("unconfigured", 0, False)
        docs = []
    else:
        try:
            store = SnowflakeVectorStore()
            docs = store.get_indexed_documents()
            status = ("connected", len(docs), True)
        except Exception:
            status = ("offline", 0, False)
            docs = []
    with _lock:
        _sf_status = status
        _indexed_docs = docs
    return status, docs


def _fetch_snowflake_data_from_creds(creds: dict):
    """Snowflake fetch for background thread (no Streamlit session)."""
    account = creds.get("SNOWFLAKE_ACCOUNT", "")
    user = creds.get("SNOWFLAKE_USER", "")
    if not account or not user:
        return ("unconfigured", 0, False), []

    try:
        import snowflake.connector

        conn_args = {"user": user, "password": creds.get("SNOWFLAKE_PASSWORD", ""), "account": account}
        if creds.get("SNOWFLAKE_WAREHOUSE"):
            conn_args["warehouse"] = creds["SNOWFLAKE_WAREHOUSE"]
        database = creds.get("SNOWFLAKE_DATABASE", "")
        schema = creds.get("SNOWFLAKE_SCHEMA", "")

        with snowflake.connector.connect(**conn_args) as conn:
            with conn.cursor() as cur:
                if database:
                    cur.execute(f"CREATE DATABASE IF NOT EXISTS {database}")
                    cur.execute(f"USE DATABASE {database}")
                if schema:
                    cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
                    cur.execute(f"USE SCHEMA {schema}")
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS CLINICAL_GUIDELINE_CHUNKS (
                        ID VARCHAR(36) PRIMARY KEY,
                        DOCUMENT_NAME VARCHAR(255),
                        PAGE_NUMBER INT,
                        CHUNK_TEXT STRING,
                        EMBEDDING VECTOR(FLOAT, 768)
                    )
                """)
                cur.execute("""
                    SELECT DOCUMENT_NAME, COUNT(*), MIN(PAGE_NUMBER), MAX(PAGE_NUMBER)
                    FROM CLINICAL_GUIDELINE_CHUNKS
                    GROUP BY DOCUMENT_NAME
                    ORDER BY DOCUMENT_NAME ASC
                """)
                rows = cur.fetchall()
        docs = _rows_to_indexed_docs(rows)
        return ("connected", len(docs), True), docs
    except Exception:
        return ("offline", 0, False), []


def _warmup_worker(creds: dict):
    global _resources, _sf_status, _indexed_docs
    try:
        resources = IngestionPipeline(), RAGPipeline(), SnowflakeVectorStore()
        status, docs = _fetch_snowflake_data_from_creds(creds)
        with _lock:
            _resources = resources
            _sf_status = status
            _indexed_docs = docs
    except Exception:
        with _lock:
            if _resources is None:
                _resources = (IngestionPipeline(), RAGPipeline(), SnowflakeVectorStore())
            if _sf_status is None:
                _sf_status = ("offline", 0, False)
            if _indexed_docs is None:
                _indexed_docs = []


def start_background_warmup():
    """Non-blocking: warm pipelines + Snowflake on landing page."""
    global _warmup_started
    with _lock:
        if _warmup_started:
            return
        _warmup_started = True
        creds = {k: st.session_state.get(k, "") for k in CONFIG_KEYS}

    threading.Thread(target=_warmup_worker, args=(creds,), daemon=True).start()


def get_app_resources():
    global _resources
    with _lock:
        if _resources is not None:
            return _resources
    resources = IngestionPipeline(), RAGPipeline(), SnowflakeVectorStore()
    with _lock:
        if _resources is None:
            _resources = resources
        return _resources


def get_snowflake_status_cached():
    """Instant read — does not block. May return 'connecting' if cache is empty."""
    with _lock:
        if _sf_status is not None:
            return _sf_status
    return "connecting", 0, False


def ensure_snowflake_connected():
    """Load Snowflake status into cache. Call from sidebar after main UI renders."""
    with _lock:
        if _sf_status is not None:
            return _sf_status
    status, _ = _fetch_snowflake_data_sync()
    return status


def get_snowflake_status(account, user, _password, warehouse, database, schema):
    """Alias for cached read — keeps call sites working."""
    return get_snowflake_status_cached()


def get_indexed_documents_cached():
    """Instant — returns cached doc list; never blocks the UI."""
    with _lock:
        if _indexed_docs is not None:
            return list(_indexed_docs)
    return []


def refresh_snowflake_data():
    """Blocking refresh after ingest/delete — call only inside spinners."""
    return _fetch_snowflake_data_sync()


def clear_snowflake_status_cache():
    global _sf_status, _indexed_docs
    with _lock:
        _sf_status = None
        _indexed_docs = None
