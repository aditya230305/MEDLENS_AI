"""
Local Medical Vector Store & Similarity Search
Indexes medical knowledge corpus into searchable semantic chunks with cosine similarity.
Runs entirely locally with zero external API calls and instant retrieval.
"""
import re
import math
from typing import List, Dict, Any, Tuple
from collections import Counter
from backend.rag.knowledge_base import load_knowledge_base


def tokenize(text: str) -> List[str]:
    """Tokenizes and normalizes text into lowercase alphanumeric stems."""
    return [w for w in re.findall(r"\b[a-zA-Z0-9]{2,}\b", text.lower()) if len(w) > 1]


class DocumentChunk:
    def __init__(self, chunk_id: str, title: str, category: str, content: str, keywords: List[str]):
        self.chunk_id = chunk_id
        self.title = title
        self.category = category
        self.content = content
        self.keywords = [k.lower() for k in keywords]
        self.tokens = tokenize(content + " " + title + " " + " ".join(keywords))
        self.vector = self._compute_tf_vector(self.tokens)

    def _compute_tf_vector(self, tokens: List[str]) -> Dict[str, float]:
        counts = Counter(tokens)
        total = max(len(tokens), 1)
        # Normalized term frequency
        tf = {word: count / total for word, count in counts.items()}
        return tf


class LocalMedicalVectorStore:
    def __init__(self):
        self.chunks: List[DocumentChunk] = []
        self._build_index()

    def _build_index(self):
        """Loads curated medical knowledge and creates structured search chunks."""
        docs = load_knowledge_base()
        self.chunks = []

        for doc in docs:
            # Chunk 1: Clinical Definition & Standard Reference Range
            content_1 = (
                f"Topic: {doc['title']} ({doc['category']})\n"
                f"Normal Reference Range: {doc['normal_range']}\n"
                f"Clinical Definition: {doc['clinical_definition']}"
            )
            self.chunks.append(
                DocumentChunk(
                    chunk_id=f"{doc['id']}_def",
                    title=f"{doc['title']} - Definition & Normal Range",
                    category=doc['category'],
                    content=content_1,
                    keywords=doc['keywords']
                )
            )

            # Chunk 2: Causes of High and Low Values
            content_2 = (
                f"Topic: {doc['title']} Clinical Significance\n"
                f"Causes of High / Elevated Levels: {doc['causes_of_high']}\n"
                f"Causes of Low / Decreased Levels: {doc['causes_of_low']}"
            )
            self.chunks.append(
                DocumentChunk(
                    chunk_id=f"{doc['id']}_significance",
                    title=f"{doc['title']} - High / Low Causes",
                    category=doc['category'],
                    content=content_2,
                    keywords=doc['keywords']
                )
            )

            # Chunk 3: Patient-Friendly Explanation & Doctor Questions
            content_3 = (
                f"Topic: {doc['title']} Patient Understanding\n"
                f"Patient Explanation: {doc['patient_friendly_summary']}\n"
                f"Questions to ask Doctor: {' | '.join(doc.get('recommended_questions', []))}"
            )
            self.chunks.append(
                DocumentChunk(
                    chunk_id=f"{doc['id']}_patient",
                    title=f"{doc['title']} - Plain-Language Explanation",
                    category=doc['category'],
                    content=content_3,
                    keywords=doc['keywords']
                )
            )

    def search(self, query: str, top_k: int = 3, filter_category: str = None) -> List[Dict[str, Any]]:
        """
        Executes semantic cosine similarity search with keyword relevance boosting.
        """
        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        query_counts = Counter(query_tokens)
        query_total = len(query_tokens)
        query_vec = {w: c / query_total for w, c in query_counts.items()}

        scored_results: List[Tuple[float, DocumentChunk]] = []

        for chunk in self.chunks:
            if filter_category and chunk.category.lower() != filter_category.lower():
                continue

            # Calculate cosine similarity of TF vectors
            dot_product = 0.0
            for word, weight in query_vec.items():
                if word in chunk.vector:
                    dot_product += weight * chunk.vector[word]

            # Magnitude of query vector
            q_norm = math.sqrt(sum(v * v for v in query_vec.values()))
            c_norm = math.sqrt(sum(v * v for v in chunk.vector.values()))
            base_score = dot_product / (q_norm * c_norm) if (q_norm * c_norm) > 0 else 0.0

            # Boost if specific medical keyword in chunk's explicit keywords
            boost = 0.0
            query_str = query.lower()
            for kw in chunk.keywords:
                if kw in query_str:
                    boost += 0.35

            final_score = base_score + boost
            if final_score > 0.01:
                scored_results.append((final_score, chunk))

        # Sort by final score descending
        scored_results.sort(key=lambda x: x[0], reverse=True)

        output: List[Dict[str, Any]] = []
        for score, chunk in scored_results[:top_k]:
            output.append({
                "chunk_id": chunk.chunk_id,
                "title": chunk.title,
                "category": chunk.category,
                "content": chunk.content,
                "relevance_score": round(float(score), 3)
            })

        return output


# Singleton instance
_vector_store_instance = None


def get_vector_store() -> LocalMedicalVectorStore:
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = LocalMedicalVectorStore()
    return _vector_store_instance
