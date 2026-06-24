import pytest
import json
from unittest.mock import MagicMock, patch
from vector_store import SnowflakeVectorStore

@patch("snowflake.connector.connect")
def test_snowflake_test_connection(mock_connect, monkeypatch):
    # Mocking standard connection and cursor behavior
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    
    mock_cur.fetchone.return_value = (1,)
    
    # Set mock credentials
    monkeypatch.setenv("SNOWFLAKE_ACCOUNT", "test-acc")
    monkeypatch.setenv("SNOWFLAKE_USER", "test-user")
    monkeypatch.setenv("SNOWFLAKE_PASSWORD", "test-pass")
    
    store = SnowflakeVectorStore()
    assert store.test_connection() is True
    mock_cur.execute.assert_called_once_with("SELECT 1")

@patch("snowflake.connector.connect")
def test_snowflake_create_schema_and_table(mock_connect, monkeypatch):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    
    monkeypatch.setenv("SNOWFLAKE_ACCOUNT", "test-acc")
    monkeypatch.setenv("SNOWFLAKE_USER", "test-user")
    monkeypatch.setenv("SNOWFLAKE_PASSWORD", "test-pass")
    monkeypatch.setenv("SNOWFLAKE_DATABASE", "DB")
    monkeypatch.setenv("SNOWFLAKE_SCHEMA", "SCH")
    
    store = SnowflakeVectorStore()
    store.create_schema_and_table()
    
    # Assert database, schema, and table creation commands were executed
    mock_cur.execute.assert_any_call("CREATE DATABASE IF NOT EXISTS DB")
    mock_cur.execute.assert_any_call("CREATE SCHEMA IF NOT EXISTS SCH")
    
    # Verify CREATE TABLE query was run
    called_queries = [args[0] for args, _ in mock_cur.execute.call_args_list]
    assert any("CREATE TABLE IF NOT EXISTS CLINICAL_GUIDELINE_CHUNKS" in q for q in called_queries)

@patch("snowflake.connector.connect")
def test_snowflake_insert_chunks(mock_connect, monkeypatch):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    
    monkeypatch.setenv("SNOWFLAKE_ACCOUNT", "test-acc")
    monkeypatch.setenv("SNOWFLAKE_USER", "test-user")
    monkeypatch.setenv("SNOWFLAKE_PASSWORD", "test-pass")
    monkeypatch.setenv("SNOWFLAKE_DATABASE", "DB")
    monkeypatch.setenv("SNOWFLAKE_SCHEMA", "SCH")
    
    store = SnowflakeVectorStore()
    
    chunks = [
        {
            "id": "chunk-1",
            "document_name": "CDC Opioids",
            "page_number": 5,
            "chunk_text": "sample text",
            "embedding": [0.1] * 768
        }
    ]
    
    store.insert_chunks(chunks)
    
    # Verify execute was called for batched insertion
    mock_cur.execute.assert_called()
    insert_call = [call for call in mock_cur.execute.call_args_list if len(call[0]) > 1 and "INSERT INTO CLINICAL_GUIDELINE_CHUNKS" in call[0][0]][0]
    sql_arg = insert_call[0][0]
    data_arg = insert_call[0][1]
    
    assert "INSERT INTO CLINICAL_GUIDELINE_CHUNKS" in sql_arg
    assert "PARSE_JSON(%s)::VECTOR(FLOAT, 768)" in sql_arg
    assert data_arg[0] == "chunk-1"
    assert data_arg[1] == "CDC Opioids"
    assert data_arg[2] == 5
    assert data_arg[3] == "sample text"
    assert data_arg[4] == json.dumps([0.1] * 768)

@patch("snowflake.connector.connect")
def test_snowflake_similarity_search(mock_connect, monkeypatch):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    
    # Mock data returned by cursor fetchall: id, document_name, page_number, chunk_text, similarity
    mock_cur.fetchall.return_value = [
        ("id-1", "WHO Hypertension", 10, "hypertension recommendation text", 0.85)
    ]
    
    monkeypatch.setenv("SNOWFLAKE_ACCOUNT", "test-acc")
    monkeypatch.setenv("SNOWFLAKE_USER", "test-user")
    monkeypatch.setenv("SNOWFLAKE_PASSWORD", "test-pass")
    monkeypatch.setenv("SNOWFLAKE_DATABASE", "DB")
    monkeypatch.setenv("SNOWFLAKE_SCHEMA", "SCH")
    
    store = SnowflakeVectorStore()
    results = store.similarity_search(query_vector=[0.1]*768, limit=5)
    
    assert len(results) == 1
    assert results[0]["id"] == "id-1"
    assert results[0]["document_name"] == "WHO Hypertension"
    assert results[0]["page_number"] == 10
    assert results[0]["similarity"] == 0.85
    
    # Check that search query uses VECTOR_COSINE_SIMILARITY
    sql_arg = mock_cur.execute.call_args[0][0]
    assert "VECTOR_COSINE_SIMILARITY(EMBEDDING, PARSE_JSON(%s)::VECTOR(FLOAT, 768))" in sql_arg
