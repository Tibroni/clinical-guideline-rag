import os
import requests
import io
from pypdf import PdfReader
from config import AppConfig
from vector_store import SnowflakeVectorStore

# Default guideline URLs
DEFAULT_GUIDELINES = {
    "CDC Opioid Prescribing Guideline (2022)": {
        "url": "https://www.cdc.gov/mmwr/volumes/71/rr/pdfs/rr7103a1-H.pdf",
        "filename": "cdc_opioids_2022.pdf"
    },
    "CDC Latent Tuberculosis Treatment Guideline (2020)": {
        "url": "https://www.cdc.gov/mmwr/volumes/69/rr/pdfs/rr6901a1-H.pdf",
        "filename": "cdc_tb_2020.pdf"
    }
}

class IngestionPipeline:
    def __init__(self):
        self.vector_store = SnowflakeVectorStore()
        # Local cache directory for downloaded PDFs
        self.data_dir = "data"
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def download_default_pdf(self, doc_name: str) -> str:
        """Downloads a default clinical guideline PDF and returns its local filepath."""
        if doc_name not in DEFAULT_GUIDELINES:
            raise ValueError(f"Unknown default guideline: {doc_name}")
        
        info = DEFAULT_GUIDELINES[doc_name]
        dest_path = os.path.join(self.data_dir, info["filename"])
        
        # Don't re-download if it already exists
        if os.path.exists(dest_path) and os.path.getsize(dest_path) > 10000:
            return dest_path
            
        print(f"Downloading {doc_name} from {info['url']}...")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(info["url"], headers=headers, timeout=30)
        response.raise_for_status()
        
        with open(dest_path, "wb") as f:
            f.write(response.content)
            
        return dest_path

    @staticmethod
    def chunk_page_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> list[str]:
        """
        Splits text into chunks of roughly chunk_size characters,
        with chunk_overlap characters of overlap. Backtracks to spaces to avoid cutting words.
        """
        # Normalize whitespace (but preserve basic punctuation/characters)
        text = " ".join(text.split())
        
        chunks = []
        if not text.strip():
            return chunks
            
        start = 0
        text_len = len(text)
        
        while start < text_len:
            # Settle on a tentative end index
            end = min(start + chunk_size, text_len)
            
            # If we're not at the very end, backtrack to find a word boundary (space)
            if end < text_len:
                last_space = text.rfind(' ', start, end)
                if last_space != -1 and last_space > start:
                    end = last_space
                    
            chunk_content = text[start:end].strip()
            if chunk_content:
                chunks.append(chunk_content)
                
            # If we've reached the end of the text, we're done
            if end >= text_len:
                break
                
            # Set the next start index (taking overlap into account)
            start = end - chunk_overlap
            
            # Avoid infinite loops or empty progression
            if start >= end:
                start = end + 1
                
        return chunks

    def process_and_index_pdf(self, pdf_file_path: str, doc_display_name: str, progress_callback=None):
        """
        Parses a PDF file, chunks the text page-by-page, generates embeddings in batches,
        and saves them to the Snowflake Vector Store.
        """
        reader = PdfReader(pdf_file_path)
        total_pages = len(reader.pages)
        chunks_to_insert = []
        
        # 1. Parse all pages and extract chunks
        for page_idx, page in enumerate(reader.pages):
            page_num = page_idx + 1
            page_text = page.extract_text() or ""
            
            if not page_text.strip():
                continue
                
            page_chunks = self.chunk_page_text(page_text)
            for chunk_idx, chunk_text in enumerate(page_chunks):
                chunks_to_insert.append({
                    "document_name": doc_display_name,
                    "page_number": page_num,
                    "chunk_text": chunk_text
                })
                
        total_chunks = len(chunks_to_insert)
        if total_chunks == 0:
            return 0
            
        # Delete existing entries for this guideline first to prevent duplicates
        self.vector_store.delete_document(doc_display_name)
        
        # 2. Batch generate embeddings and insert into Snowflake
        batch_size = 50  # Moderate batch size to prevent payload timeouts
        
        for i in range(0, total_chunks, batch_size):
            batch = chunks_to_insert[i:i + batch_size]
            batch_texts = [c["chunk_text"] for c in batch]
            
            if progress_callback:
                progress_callback(i, total_chunks, f"Embedding chunks {i + 1} to {min(i + batch_size, total_chunks)} of {total_chunks}...")
                
            # Generate embeddings for the batch
            embeddings = AppConfig.get_embeddings_batch(batch_texts)
            
            # Map embeddings back to chunks
            for idx, embedding in enumerate(embeddings):
                batch[idx]["embedding"] = embedding
                
            # Insert this batch into Snowflake
            if progress_callback:
                progress_callback(i, total_chunks, f"Uploading chunks {i + 1} to {min(i + batch_size, total_chunks)} to Snowflake...")
            self.vector_store.insert_chunks(batch)
            
        if progress_callback:
            progress_callback(total_chunks, total_chunks, f"Ingestion complete! Loaded {total_chunks} chunks.")
            
        return total_chunks

    def ingest_uploaded_pdf(self, file_bytes: bytes, filename: str, progress_callback=None) -> int:
        """Processes and indexes raw bytes from an uploaded PDF file."""
        temp_path = os.path.join(self.data_dir, f"temp_{filename}")
        
        with open(temp_path, "wb") as f:
            f.write(file_bytes)
            
        try:
            chunk_count = self.process_and_index_pdf(temp_path, filename, progress_callback)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
        return chunk_count
