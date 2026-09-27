import os
import re
from typing import List, Dict, Any

class LightweightRAG:
    """
    Lightweight local Retrieval-Augmented Generation (RAG) engine.
    Indexes text files in a target directory and retrieves relevant context using TF-IDF / keyword similarity.
    """

    def __init__(self, kb_dir: str = "knowledge_base"):
        self.kb_dir = kb_dir
        self.documents: List[Dict[str, Any]] = []
        self.load_and_index()

    def load_and_index(self):
        """Loads and chunks all markdown and text files from the knowledge base directory."""
        self.documents = []
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
                                self.documents.append({
                                    "filename": file,
                                    "path": file_path,
                                    "chunk_id": idx,
                                    "content": chunk.strip()
                                })
                    except Exception as e:
                        print(f"Warning: Failed to read RAG document {file_path}: {e}")

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

    def _score_chunk(self, query: str, chunk_text: str) -> float:
        """Calculates keyword overlap and relevance score between query and chunk."""
        query_words = set(re.findall(r'\w+', query.lower()))
        chunk_words = re.findall(r'\w+', chunk_text.lower())

        if not query_words or not chunk_words:
            return 0.0

        matches = sum(1 for w in chunk_words if w in query_words)
        unique_matches = len(query_words.intersection(set(chunk_words)))

        # Higher weight for unique query keyword matches
        score = (matches * 0.4) + (unique_matches * 1.5)
        return score

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Returns top_k most relevant chunks for a given query."""
        if not self.documents:
            self.load_and_index()

        scored_results = []
        for doc in self.documents:
            score = self._score_chunk(query, doc["content"])
            if score > 0:
                scored_results.append((score, doc))

        scored_results.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored_results[:top_k]]

    def retrieve_context(self, query: str, top_k: int = 3) -> str:
        """Retrieves and formats matching context into a clean context string."""
        results = self.search(query, top_k=top_k)
        if not results:
            return "No relevant local knowledge base documents found."

        context_parts = []
        for res in results:
            context_parts.append(f"--- Document: {res['filename']} --- \n{res['content']}")

        return "\n\n".join(context_parts)
