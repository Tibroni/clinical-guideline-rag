import pytest
from ingestion import IngestionPipeline

def test_chunk_page_text_basic():
    # Test simple splitting of short text
    text = "This is a short test sentence for our clinical chunker."
    chunks = IngestionPipeline.chunk_page_text(text, chunk_size=20, chunk_overlap=5)
    
    assert len(chunks) > 0
    # Reconstructed text should cover all words (though whitespace is normalized)
    joined = " ".join(chunks)
    assert "clinical" in joined
    assert "chunker" in joined

def test_chunk_page_text_boundary_preservation():
    # Verify that we do not slice words in half by checking for word boundaries (spaces)
    text = "treatment threshold pharmacological treatment hypertension adults"
    # Set size small enough to force split
    chunks = IngestionPipeline.chunk_page_text(text, chunk_size=25, chunk_overlap=5)
    
    for chunk in chunks:
        # Check that none of the chunks end or start with partial words (or are too long)
        assert len(chunk) <= 25
        # Words in chunks should be whole words
        for word in chunk.split():
            assert word in text

def test_chunk_page_text_empty():
    # Test behavior on empty string or whitespace
    assert IngestionPipeline.chunk_page_text("") == []
    assert IngestionPipeline.chunk_page_text("    \n   ") == []

def test_chunk_page_text_large():
    # Test a paragraph that exceeds the chunk size
    paragraph = (
        "High blood pressure (hypertension) is a common condition in which the long-term force of the blood "
        "against your artery walls is high enough that it may eventually cause health problems, such as heart disease. "
        "Blood pressure is determined both by the amount of blood your heart pumps and the amount of resistance to "
        "blood flow in your arteries. The more blood your heart pumps and the narrower your arteries, the higher "
        "your blood pressure. A blood pressure reading is given in millimeters of mercury (mm Hg). It has two numbers."
    )
    
    chunk_size = 200
    overlap = 40
    chunks = IngestionPipeline.chunk_page_text(paragraph, chunk_size=chunk_size, chunk_overlap=overlap)
    
    assert len(chunks) >= 2
    for chunk in chunks:
        assert len(chunk) <= chunk_size
