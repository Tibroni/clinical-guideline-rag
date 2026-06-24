import os
import streamlit as st
from dotenv import load_dotenv

# Load from .env file if it exists
load_dotenv()

# Set to False to restore the credential sidebar for local development.
DEFAULT_DEMO_MODE = True

class AppConfig:
    @staticmethod
    def _get_host_setting(key, default=""):
        """Read from Streamlit secrets or environment only (not sidebar session state)."""
        try:
            if hasattr(st, "secrets") and key in st.secrets:
                val = st.secrets[key]
                if val is not None and str(val).strip():
                    return str(val)
        except Exception:
            pass
        val = os.environ.get(key)
        if val is not None and str(val).strip():
            return val
        return default

    @staticmethod
    def get_setting(key, default=""):
        """Get setting from session state, Streamlit secrets, environment variables, then default."""
        if st.session_state is not None and key in st.session_state:
            val = st.session_state[key]
            if val:
                return val
        return AppConfig._get_host_setting(key, default)

    @classmethod
    def _has_host_credentials(cls):
        """True when LLM + Snowflake credentials are injected by the host."""
        provider = cls._get_host_setting("LLM_PROVIDER", "gemini").lower()
        if provider == "openai":
            llm_ok = bool(cls._get_host_setting("OPENAI_API_KEY"))
        else:
            llm_ok = bool(cls._get_host_setting("GEMINI_API_KEY"))

        snowflake_ok = (
            bool(cls._get_host_setting("SNOWFLAKE_ACCOUNT"))
            and bool(cls._get_host_setting("SNOWFLAKE_USER"))
            and bool(cls._get_host_setting("SNOWFLAKE_PASSWORD"))
        )
        return llm_ok and snowflake_ok

    @classmethod
    def is_demo_mode(cls):
        """Hide credential sidebar when host secrets/env are used instead of manual input."""
        demo_flag = cls._get_host_setting("DEMO_MODE", "")
        if demo_flag:
            return demo_flag.lower() in ("true", "1", "yes")
        if demo_flag.lower() in ("false", "0", "no"):
            return False
        if cls._has_host_credentials():
            return True
        return DEFAULT_DEMO_MODE

    @classmethod
    def get_llm_provider(cls):
        """Returns the active LLM provider: 'gemini' or 'openai'."""
        return cls.get_setting("LLM_PROVIDER", "gemini").lower()

    @classmethod
    def get_gemini_api_key(cls):
        return cls.get_setting("GEMINI_API_KEY")

    @classmethod
    def get_openai_api_key(cls):
        return cls.get_setting("OPENAI_API_KEY")

    @classmethod
    def get_snowflake_creds(cls):
        """Returns dict containing Snowflake connection credentials."""
        return {
            "user": cls.get_setting("SNOWFLAKE_USER"),
            "password": cls.get_setting("SNOWFLAKE_PASSWORD"),
            "account": cls.get_setting("SNOWFLAKE_ACCOUNT"),
            "warehouse": cls.get_setting("SNOWFLAKE_WAREHOUSE"),
            "database": cls.get_setting("SNOWFLAKE_DATABASE"),
            "schema": cls.get_setting("SNOWFLAKE_SCHEMA")
        }

    @classmethod
    def is_llm_configured(cls):
        provider = cls.get_llm_provider()
        if provider == "openai":
            return bool(cls.get_openai_api_key())
        return bool(cls.get_gemini_api_key())

    @classmethod
    def get_gemini_client(cls):
        """Initializes and returns the Google GenAI Client."""
        api_key = cls.get_gemini_api_key()
        if not api_key:
            raise ValueError("Gemini API key is not configured.")
        from google import genai
        return genai.Client(api_key=api_key)

    @classmethod
    def get_openai_client(cls):
        """Initializes and returns the OpenAI Client."""
        api_key = cls.get_openai_api_key()
        if not api_key:
            raise ValueError("OpenAI API key is not configured.")
        from openai import OpenAI
        return OpenAI(api_key=api_key)

    @classmethod
    def get_embeddings_batch(cls, texts: list[str]) -> list[list[float]]:
        """Generates 768-dimensional embedding vectors for a list of texts in a single batch call with retries."""
        if not texts:
            return []
            
        provider = cls.get_llm_provider()
        import time
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                if provider == "openai":
                    client = cls.get_openai_client()
                    response = client.embeddings.create(
                        model="text-embedding-3-small",
                        input=texts,
                        dimensions=768
                    )
                    return [item.embedding for item in response.data]
                else:
                    client = cls.get_gemini_client()
                    response = client.models.embed_content(
                        model="text-embedding-004",
                        contents=texts,
                    )
                    
                    # Handle batch list structure dynamically
                    embeddings = response.embeddings
                    if isinstance(embeddings, list):
                        return [emb.values if hasattr(emb, 'values') else emb for emb in embeddings]
                    elif hasattr(embeddings, 'values'):
                        return [embeddings.values]
                    else:
                        # Fallback for list-like custom wrapper structures
                        try:
                            return [emb.values for emb in embeddings]
                        except Exception:
                            return [embeddings]
            except Exception as e:
                print(f"Embedding attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    raise e
                time.sleep(2 ** attempt)
        raise ValueError("Could not retrieve batch embeddings.")

    @classmethod
    def get_embedding(cls, text: str) -> list[float]:
        """Generates a 768-dimensional embedding vector for the text using the active provider."""
        res = cls.get_embeddings_batch([text])
        if not res:
            raise ValueError("Failed to generate embedding.")
        return res[0]

    @classmethod
    def generate_completion(cls, system_prompt: str, user_prompt: str) -> str:
        """Generates a text completion using the active provider."""
        provider = cls.get_llm_provider()
        if provider == "openai":
            client = cls.get_openai_client()
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2
            )
            return response.choices[0].message.content
        else:
            client = cls.get_gemini_client()
            from google.genai import types
            config = types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.2
            )
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=user_prompt,
                config=config
            )
            return response.text
