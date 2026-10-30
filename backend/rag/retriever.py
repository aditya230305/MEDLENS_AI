"""
Medical RAG Retriever Module
Fetches grounding reference chunks for report entities and patient Q&A queries.
"""
from typing import List, Dict, Any
from backend.rag.vector_store import get_vector_store
from backend.nlp_extraction.entity_models import StructuredMedicalRecord


def retrieve_context_for_report(record: StructuredMedicalRecord) -> List[Dict[str, Any]]:
    """
    Retrieves grounding medical literature chunks for all identified abnormal lab tests
    and primary routine parameters in the patient's record.
    """
    vs = get_vector_store()
    retrieved_chunks: List[Dict[str, Any]] = []
    seen_chunk_ids = set()

    # Prioritize abnormal tests
    target_tests = record.abnormal_tests if record.abnormal_tests else record.tests

    for test in target_tests:
        query = f"{test.test_name} {test.category.value} normal range causes of {test.status.value}"
        results = vs.search(query, top_k=2)
        for r in results:
            if r["chunk_id"] not in seen_chunk_ids:
                seen_chunk_ids.add(r["chunk_id"])
                retrieved_chunks.append(r)

    # If few abnormal tests found, search for the remaining tests
    if len(retrieved_chunks) < 3 and record.tests:
        for test in record.tests[:3]:
            query = f"{test.test_name} {test.category.value}"
            results = vs.search(query, top_k=1)
            for r in results:
                if r["chunk_id"] not in seen_chunk_ids:
                    seen_chunk_ids.add(r["chunk_id"])
                    retrieved_chunks.append(r)

    return retrieved_chunks


def retrieve_context_for_query(
    query: str,
    record: StructuredMedicalRecord,
    top_k: int = 3
) -> List[Dict[str, Any]]:
    """
    Retrieves the most semantically relevant medical knowledge chunks
    specifically addressing a patient's question.
    """
    vs = get_vector_store()

    # Enrich query with abnormal test context from patient's record if relevant
    abnormal_names = " ".join([t.test_name for t in record.abnormal_tests])
    augmented_query = f"{query} {abnormal_names}".strip()

    results = vs.search(augmented_query, top_k=top_k)
    return results


def format_chunks_for_prompt(chunks: List[Dict[str, Any]]) -> str:
    """Formats retrieved chunks into clean markdown reference citations for LLM prompt."""
    if not chunks:
        return "No specific medical reference text retrieved."

    formatted = []
    for idx, c in enumerate(chunks, 1):
        formatted.append(
            f"--- Reference Citation [{idx}]: {c['title']} ---\n"
            f"{c['content']}\n"
        )
    return "\n".join(formatted)
