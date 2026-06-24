from config import AppConfig
from vector_store import SnowflakeVectorStore

class RAGPipeline:
    def __init__(self):
        self.vector_store = SnowflakeVectorStore()

    def query(self, user_query: str, limit: int = 6, doc_filter: str = None) -> dict:
        """
        Executes the main RAG flow:
        1. Embeds the user query.
        2. Retrieves the top relevant chunks from Snowflake.
        3. Constructs a context-aware system prompt.
        4. Invokes the LLM to generate the answer with citations.
        5. Calculates confidence scores.
        """
        # Step 1: Embed Query
        query_vector = AppConfig.get_embedding(user_query)
        
        # Step 2: Retrieve Relevant Chunks
        retrieved_chunks = self.vector_store.similarity_search(
            query_vector=query_vector,
            limit=limit,
            doc_filter=doc_filter
        )
        
        if not retrieved_chunks:
            return {
                "answer": "No relevant clinical guideline documents have been ingested or matched your query. Please index documents first.",
                "sources": [],
                "confidence_score": 0.0,
                "confidence_level": "None"
            }
            
        # Step 3: Format Context & Track Citations
        context_str = ""
        sources_list = []
        for idx, chunk in enumerate(retrieved_chunks):
            doc_name = chunk["document_name"]
            page_num = chunk["page_number"]
            source_tag = f"Source [{idx + 1}]"
            
            # Format text block for the LLM
            context_str += f"--- {source_tag} ---\n"
            context_str += f"Document: {doc_name}\n"
            context_str += f"Page: {page_num}\n"
            context_str += f"Text:\n{chunk['chunk_text']}\n\n"
            
            # Store metadata for citation panel
            sources_list.append({
                "source_tag": source_tag,
                "document_name": doc_name,
                "page_number": page_num,
                "chunk_text": chunk["chunk_text"],
                "similarity": chunk["similarity"]
            })
            
        # Step 4: System Prompt and LLM Completion
        system_prompt = """You are an advanced Clinical Guideline Assistant. Your purpose is to provide clinicians with accurate, evidence-based answers to medical policy and clinical guidelines questions.

Follow these strict rules:
1. Base your answer **only** on the clinical guideline passages provided in the context below. Do not assume, extrapolate, or use outside clinical knowledge.
2. If the answer cannot be found in the provided context, state clearly: "I cannot find the answer in the ingested guidelines."
3. Synthesize your answer concisely and structure it with clear headings or bullet points where appropriate for busy clinicians.
4. Cite the sources of your statements inline using the index of the source, e.g., "Initiate pharmacological treatment when systolic blood pressure is ≥ 140 mmHg [Source 1]."
5. Refer to specific pages if provided, e.g., "for patients with cardiovascular disease, initiate at ≥ 130 mmHg [Source 2, p. 12]."
6. Include a brief concluding summary table of the key recommendations if applicable.
"""
        
        user_prompt = f"""Clinical Question: {user_query}

Context from Clinical Guidelines:
{context_str}

Please generate a clinical response following the rules above.
"""
        
        answer = AppConfig.generate_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )
        
        # Step 5: Calculate Confidence Score
        # We calculate the average similarity of the top 3 matches (or all if fewer than 3)
        top_similarities = [c["similarity"] for c in retrieved_chunks[:3]]
        avg_similarity = sum(top_similarities) / len(top_similarities) if top_similarities else 0.0
        
        # Determine confidence level
        if avg_similarity >= 0.80:
            confidence_level = "High"
        elif avg_similarity >= 0.60:
            confidence_level = "Medium"
        else:
            confidence_level = "Low"
            
        return {
            "answer": answer,
            "sources": sources_list,
            "confidence_score": avg_similarity,
            "confidence_level": confidence_level
        }

    def compare_guidelines(self, clinical_topic: str, doc_a: str, doc_b: str) -> dict:
        """
        Retrieves relevant guidelines on a specific topic for two different documents,
        and requests the LLM to generate a structured side-by-side comparative table.
        """
        query_vector = AppConfig.get_embedding(clinical_topic)
        
        # Retrieve chunks for Document A
        chunks_a = self.vector_store.similarity_search(query_vector=query_vector, limit=4, doc_filter=doc_a)
        # Retrieve chunks for Document B
        chunks_b = self.vector_store.similarity_search(query_vector=query_vector, limit=4, doc_filter=doc_b)
        
        if not chunks_a and not chunks_b:
            return {
                "comparison_text": "No matching guideline documents found to compare. Please check document names in your index.",
                "sources_a": [],
                "sources_b": []
            }
            
        # Format context for both documents
        context_a = "\n".join([f"- Page {c['page_number']}: {c['chunk_text']}" for c in chunks_a])
        context_b = "\n".join([f"- Page {c['page_number']}: {c['chunk_text']}" for c in chunks_b])
        
        system_prompt = """You are a senior clinical consultant assisting hospital leadership. Your task is to perform a comparative analysis between two clinical guidelines on a specific clinical topic.
        
Structure your response as follows:
1. **Executive Summary**: A brief paragraph summarizing the key difference or alignment between the two guidelines on the topic.
2. **Comparison Matrix**: Build a Markdown table with columns: 'Feature / Parameter', 'Guideline A', 'Guideline B', and 'Key Difference'.
3. **Clinical Recommendation**: A brief recommendation on how a hospital might reconcile these guidelines (e.g. which standard is more stringent or universally applicable).
4. Cite sources inline using page numbers (e.g., "[A, p. 5]" or "[B, p. 12]").
"""
        
        user_prompt = f"""Clinical Topic to Compare: {clinical_topic}

=== Guideline A: {doc_a} ===
Context:
{context_a if context_a else "No relevant information found in this guideline."}

=== Guideline B: {doc_b} ===
Context:
{context_b if context_b else "No relevant information found in this guideline."}

Generate the comparative analysis. Refer to Guideline A as '{doc_a}' and Guideline B as '{doc_b}' in the table.
"""
        
        comparison_text = AppConfig.generate_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )
        
        return {
            "comparison_text": comparison_text,
            "sources_a": chunks_a,
            "sources_b": chunks_b
        }
