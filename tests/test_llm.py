import pytest
from unittest.mock import MagicMock, patch
from config import AppConfig

def test_config_getters(monkeypatch):
    # Test setting values and getting them back
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    
    assert AppConfig.get_llm_provider() == "openai"
    assert AppConfig.get_openai_api_key() == "test-openai-key"

@patch("openai.OpenAI")
def test_openai_embedding(mock_openai_class, monkeypatch):
    # Setup mock
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client
    
    # Mock embedding response
    mock_response = MagicMock()
    mock_data = MagicMock()
    mock_data.embedding = [0.1] * 768
    mock_response.data = [mock_data]
    mock_client.embeddings.create.return_value = mock_response
    
    # Set environment variables
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "mock-key")
    
    # Generate embedding
    emb = AppConfig.get_embedding("test query text")
    
    # Assertions
    assert len(emb) == 768
    mock_client.embeddings.create.assert_called_once_with(
        model="text-embedding-3-small",
        input=["test query text"],
        dimensions=768
    )

@patch("openai.OpenAI")
def test_openai_completion(mock_openai_class, monkeypatch):
    # Setup mock
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client
    
    # Mock completion response
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_message.content = "This is a mock clinical response."
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response
    
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "mock-key")
    
    ans = AppConfig.generate_completion("system prompt", "user query")
    
    assert ans == "This is a mock clinical response."
    mock_client.chat.completions.create.assert_called_once_with(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "system prompt"},
            {"role": "user", "content": "user query"}
        ],
        temperature=0.2
    )

@patch("google.genai.Client")
def test_gemini_embedding(mock_gemini_client_class, monkeypatch):
    # Setup mock
    mock_client = MagicMock()
    mock_gemini_client_class.return_value = mock_client
    
    # Mock embedding response
    mock_response = MagicMock()
    # Handle the structure returned by Gemini API (response.embeddings.values or response.embeddings[0].values)
    mock_embeddings = MagicMock()
    mock_embeddings.values = [0.2] * 768
    mock_response.embeddings = mock_embeddings
    
    mock_client.models.embed_content.return_value = mock_response
    
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "mock-gemini-key")
    
    emb = AppConfig.get_embedding("test query text")
    
    assert len(emb) == 768
    mock_client.models.embed_content.assert_called_once_with(
        model="text-embedding-004",
        contents=["test query text"]
    )
