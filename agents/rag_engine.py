import os
import re
import math
from collections import Counter
from typing import List, Dict, Any, Optional

class LightweightRAG:
    """
    Lightweight local Retrieval-Augmented Generation (RAG) engine.
    Indexes text and markdown files in a target directory and retrieves relevant context
    using an Okapi BM25 lexical ranking pipeline without requiring an external vector database.
    """

    def __init__(self, kb_dir: str = "knowledge_base", k1: float = 1.5, b: float = 0.75):
        self.kb_dir = kb_dir
        self.k1 = k1
        self.b = b
        self.documents: List[Dict[str, Any]] = []
        self.doc_freqs: Dict[str, int] = {}
        self.avg_doc_len: float = 0.0
        self.load_and_index()

    def _tokenize(self, text: str) -> List[str]:
        """Normalizes and tokenizes text into lowercase alphanumeric words."""
        return re.findall(r'\b[a-zA-Z0-9_-]+\b', text.lower())

    def load_and_index(self):
        """Loads, chunks, and indexes all markdown and text files from the knowledge base directory."""
        self.documents = []
        self.doc_freqs = {}
        if not os.path.exists(self.kb_dir):
            return

        for root, _, files in os.walk(self.kb_dir):
            for file in files:
                if file.endswith((".md", ".txt")):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()

                        chunks = self._chunk_text(content)
                        for idx, chunk in enumerate(chunks):
                            if chunk.strip():
                                tokens = self._tokenize(chunk)
                                self.documents.append({
                                    "filename": file,
                                    "path": file_path,
                                    "chunk_id": idx,
                                    "content": chunk.strip(),
                                    "tokens": tokens,
                                    "term_counts": Counter(tokens),
                                    "length": len(tokens)
                                })
                    except Exception as e:
                        print(f"Warning: Failed to read RAG document {file_path}: {e}")

        # Compute document frequencies and average document length for BM25
        total_chunks = len(self.documents)
        if total_chunks > 0:
            total_len = 0
            df_counter = Counter()
            for doc in self.documents:
                total_len += doc["length"]
                unique_terms = set(doc["tokens"])
                for term in unique_terms:
                    df_counter[term] += 1
            self.avg_doc_len = total_len / total_chunks
            self.doc_freqs = dict(df_counter)
        else:
            self.avg_doc_len = 0.0
            self.doc_freqs = {}

    def _chunk_text(self, text: str, max_chunk_words: int = 250) -> List[str]:
        """Splits text into paragraph-level or block chunks."""
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = []
        current_word_count = 0

        for para in paragraphs:
            words = para.split()
            if not words:
                continue
            if current_word_count + len(words) > max_chunk_words and current_chunk:
                chunks.append("\n\n".join(current_chunk))
                current_chunk = [para]
                current_word_count = len(words)
            else:
                current_chunk.append(para)
                current_word_count += len(words)

        if current_chunk:
            chunks.append("\n\n".join(current_chunk))

        return chunks

    def _compute_idf(self, term: str) -> float:
        """Calculates smoothed inverse document frequency (IDF) for a term."""
        n_docs = len(self.documents)
        df = self.doc_freqs.get(term, 0)
        # Standard Okapi BM25 smoothed IDF
        return math.log(1.0 + (n_docs - df + 0.5) / (df + 0.5))

    def _score_chunk(self, query_tokens: List[str], doc: Dict[str, Any]) -> float:
        """Calculates Okapi BM25 relevance score between query tokens and document chunk."""
        if not query_tokens or doc["length"] == 0:
            return 0.0

        score = 0.0
        doc_len = doc["length"]
        term_counts = doc["term_counts"]
        avg_len = self.avg_doc_len or 1.0

        # Term match evaluation
        for q_term in set(query_tokens):
            if q_term in term_counts:
                tf = term_counts[q_term]
                idf = self._compute_idf(q_term)
                # BM25 term weighting formula
                numerator = tf * (self.k1 + 1.0)
                denominator = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / avg_len))
                score += idf * (numerator / denominator)

        # Bonus for filename / title match
        filename_lower = doc["filename"].lower()
        for q_term in set(query_tokens):
            if len(q_term) > 2 and q_term in filename_lower:
                score += 1.5

        return score

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Returns top_k most relevant chunks for a given query, ordered by BM25 relevance score.
        Each returned dictionary includes the score and document metadata.
        """
        if not self.documents:
            self.load_and_index()

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        scored_results = []
        for doc in self.documents:
            score = self._score_chunk(query_tokens, doc)
            if score > 0:
                result_item = {
                    "filename": doc["filename"],
                    "path": doc["path"],
                    "chunk_id": doc["chunk_id"],
                    "content": doc["content"],
                    "score": round(score, 4)
                }
                scored_results.append((score, result_item))

        scored_results.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored_results[:top_k]]

    def retrieve_with_metadata(self, query: str, top_k: int = 3) -> Dict[str, Any]:
        """
        Retrieves top_k chunks along with rich retrieval metadata:
        - retrieved_documents: unique list of source documents matched
        - top_score: highest BM25 score achieved
        - chunks: list of scored chunk items
        - context: formatted text context ready for agent prompt ingestion
        """
        chunks = self.search(query, top_k=top_k)
        if not chunks:
            return {
                "context": "No relevant local knowledge base documents found.",
                "chunks": [],
                "retrieved_documents": [],
                "top_score": 0.0,
                "query_tokens": self._tokenize(query)
            }

        retrieved_docs = list(dict.fromkeys(c["filename"] for c in chunks))
        top_score = chunks[0]["score"] if chunks else 0.0

        context_parts = []
        for res in chunks:
            context_parts.append(
                f"--- Document: {res['filename']} (Relevance: {res['score']}) --- \n{res['content']}"
            )
        formatted_context = "\n\n".join(context_parts)

        return {
            "context": formatted_context,
            "chunks": chunks,
            "retrieved_documents": retrieved_docs,
            "top_score": top_score,
            "query_tokens": self._tokenize(query)
        }

    def retrieve_context(self, query: str, top_k: int = 3) -> str:
        """Retrieves and formats matching context into a clean context string."""
        meta = self.retrieve_with_metadata(query, top_k=top_k)
        return meta["context"]

