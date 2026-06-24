import json
import uuid
import snowflake.connector
from config import AppConfig

class SnowflakeVectorStore:
    @property
    def creds(self):
        """Dynamically gets the latest Snowflake credentials from session state or env."""
        return AppConfig.get_snowflake_creds()

    def get_connection(self):
        """Creates and returns a new Snowflake connection."""
        if not self.creds["account"] or not self.creds["user"]:
            raise ValueError("Snowflake credentials are not fully configured in settings.")
        
        # Build connection args, filtering out None values
        conn_args = {
            "user": self.creds["user"],
            "password": self.creds["password"],
            "account": self.creds["account"],
        }
        if self.creds["warehouse"]:
            conn_args["warehouse"] = self.creds["warehouse"]
        if self.creds["database"]:
            conn_args["database"] = self.creds["database"]
        if self.creds["schema"]:
            conn_args["schema"] = self.creds["schema"]

        return snowflake.connector.connect(**conn_args)

    def test_connection(self) -> bool:
        """Tests the Snowflake connection and returns True if successful."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    result = cur.fetchone()
                    return result is not None and result[0] == 1
        except Exception as e:
            print(f"Snowflake connection test failed: {e}")
            raise e

    def create_schema_and_table(self):
        """Initializes the database schema and guidelines table if they do not exist."""
        if not self.creds["database"]:
            raise ValueError("Database Name is empty. Please enter a database name (e.g. CLINICAL_DB) in the sidebar.")
        if not self.creds["schema"]:
            raise ValueError("Schema Name is empty. Please enter a schema name (e.g. PUBLIC) in the sidebar.")
            
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Create and set database
                cur.execute(f"CREATE DATABASE IF NOT EXISTS {self.creds['database']}")
                cur.execute(f"USE DATABASE {self.creds['database']}")
                
                # Create and set schema
                cur.execute(f"CREATE SCHEMA IF NOT EXISTS {self.creds['schema']}")
                cur.execute(f"USE SCHEMA {self.creds['schema']}")
                
                # Create the guidelines vector chunks table
                create_table_sql = """
                CREATE TABLE IF NOT EXISTS CLINICAL_GUIDELINE_CHUNKS (
                    ID VARCHAR(36) PRIMARY KEY,
                    DOCUMENT_NAME VARCHAR(255),
                    PAGE_NUMBER INT,
                    CHUNK_TEXT STRING,
                    EMBEDDING VECTOR(FLOAT, 768)
                );
                """
                cur.execute(create_table_sql)

    def insert_chunks(self, chunks_data: list[dict]):
        """
        Inserts a list of guideline chunks into Snowflake.
        Each chunk dict should contain:
        - document_name (str)
        - page_number (int)
        - chunk_text (str)
        - embedding (list of 768 floats)
        """
        if not chunks_data:
            return

        self.create_schema_and_table()

        # Build dynamic INSERT query using SELECT + UNION ALL
        select_parts = []
        params = []
        
        for chunk in chunks_data:
            chunk_id = chunk.get("id") or str(uuid.uuid4())
            doc_name = chunk["document_name"]
            page_num = int(chunk["page_number"])
            text = chunk["chunk_text"]
            vector_str = json.dumps(chunk["embedding"])
            
            select_parts.append("SELECT %s, %s, %s, %s, PARSE_JSON(%s)::VECTOR(FLOAT, 768)")
            params.extend([chunk_id, doc_name, page_num, text, vector_str])
            
        union_sql = " UNION ALL ".join(select_parts)
        insert_sql = f"""
        INSERT INTO CLINICAL_GUIDELINE_CHUNKS (ID, DOCUMENT_NAME, PAGE_NUMBER, CHUNK_TEXT, EMBEDDING)
        {union_sql}
        """
        
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(insert_sql, tuple(params))

    def similarity_search(self, query_vector: list[float], limit: int = 5, doc_filter: str = None) -> list[dict]:
        """
        Performs vector similarity search in Snowflake using VECTOR_COSINE_DISTANCE.
        Returns a list of dicts with the closest matches.
        """
        self.create_schema_and_table()
        
        vector_str = json.dumps(query_vector)
        
        # Build dynamic query based on filters
        params = [vector_str]
        where_clause = ""
        if doc_filter:
            where_clause = "WHERE DOCUMENT_NAME = %s"
            params.append(doc_filter)
            
        params.append(limit)
        
        query_sql = f"""
        SELECT 
            ID, 
            DOCUMENT_NAME, 
            PAGE_NUMBER, 
            CHUNK_TEXT, 
            VECTOR_COSINE_SIMILARITY(EMBEDDING, PARSE_JSON(%s)::VECTOR(FLOAT, 768)) AS SIMILARITY
        FROM CLINICAL_GUIDELINE_CHUNKS
        {where_clause}
        ORDER BY SIMILARITY DESC
        LIMIT %s
        """
        
        results = []
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query_sql, tuple(params))
                rows = cur.fetchall()
                for row in rows:
                    sim_val = float(row[4])
                    # Cosine similarity ranges from -1 to 1. Clamp to [0, 1] for our score
                    similarity = max(0.0, min(1.0, sim_val))
                    results.append({
                        "id": row[0],
                        "document_name": row[1],
                        "page_number": int(row[2]),
                        "chunk_text": row[3],
                        "similarity": similarity
                    })
        return results

    def delete_document(self, document_name: str):
        """Deletes all vector chunks associated with a specific document name."""
        self.create_schema_and_table()
        delete_sql = "DELETE FROM CLINICAL_GUIDELINE_CHUNKS WHERE DOCUMENT_NAME = %s"
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(delete_sql, (document_name,))

    def get_indexed_documents(self) -> list[dict]:
        """Returns a list of indexed guidelines and their metadata statistics."""
        self.create_schema_and_table()
        query_sql = """
        SELECT DOCUMENT_NAME, COUNT(*), MIN(PAGE_NUMBER), MAX(PAGE_NUMBER)
        FROM CLINICAL_GUIDELINE_CHUNKS
        GROUP BY DOCUMENT_NAME
        ORDER BY DOCUMENT_NAME ASC
        """
        results = []
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query_sql)
                    rows = cur.fetchall()
                    for row in rows:
                        results.append({
                            "document_name": row[0],
                            "chunk_count": int(row[1]),
                            "start_page": int(row[2]),
                            "end_page": int(row[3])
                        })
        except Exception as e:
            print(f"Error fetching indexed documents: {e}")
        return results
