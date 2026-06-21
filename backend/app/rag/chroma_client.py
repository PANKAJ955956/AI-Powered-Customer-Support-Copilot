import os
import logging
from backend.app.config import settings

logger = logging.getLogger(__name__)

# Try to import chromadb. If it's not installed or throws import errors on Windows,
# we'll build a Mock/InMemory Vector DB to prevent application crashes.
CHROMA_AVAILABLE = False
try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    CHROMA_AVAILABLE = True
except Exception as e:
    logger.warning(f"ChromaDB not available or failed to import: {e}. Falling back to in-memory store.")

class SimpleVectorStore:
    """Fallback in-memory vector store when ChromaDB package fails to compile/run on Windows."""
    def __init__(self):
        self.documents = []
        self.metadatas = []
        self.ids = []
        
    def add_texts(self, texts, metadatas=None, ids=None):
        for i, text in enumerate(texts):
            self.documents.append(text)
            self.metadatas.append(metadatas[i] if metadatas else {})
            self.ids.append(ids[i] if ids else f"id_{len(self.documents)}")
            
    def similarity_search_with_score(self, query, k=3):
        # Fallback to simple sub-string matching and basic Jaccard similarity score
        results = []
        query_words = set(query.lower().split())
        for doc, meta, doc_id in zip(self.documents, self.metadatas, self.ids):
            doc_words = set(doc.lower().split())
            intersection = query_words.intersection(doc_words)
            union = query_words.union(doc_words)
            jaccard = len(intersection) / len(union) if union else 0.0
            
            # Boost if exact query is in text
            if query.lower() in doc.lower():
                jaccard += 0.5
                
            results.append((doc, meta, doc_id, jaccard))
            
        results.sort(key=lambda x: x[3], reverse=True)
        return [{"document": r[0], "metadata": r[1], "id": r[2], "score": r[3]} for r in results[:k]]

class ChromaManager:
    def __init__(self):
        self.client = None
        self.collection = None
        self.fallback_store = SimpleVectorStore()
        self.use_fallback = not CHROMA_AVAILABLE
        
        if not self.use_fallback:
            try:
                os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
                self.client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
                self.collection = self.client.get_or_create_collection(
                    name="support_kb",
                    metadata={"hnsw:space": "cosine"}
                )
                logger.info("ChromaDB Client initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize ChromaDB Client: {e}. Switching to in-memory store.")
                self.use_fallback = True

    def add_documents(self, chunks: list[str], metadatas: list[dict], ids: list[str]):
        if self.use_fallback:
            self.fallback_store.add_texts(chunks, metadatas, ids)
            return
            
        # If OpenAI Key is available, use embeddings. Otherwise, use Chroma's default sentence-transformer.
        try:
            self.collection.add(
                documents=chunks,
                metadatas=metadatas,
                ids=ids
            )
        except Exception as e:
            logger.error(f"Error adding documents to ChromaDB: {e}. Adding to fallback in-memory store.")
            self.fallback_store.add_texts(chunks, metadatas, ids)

    def similarity_search(self, query: str, k: int = 3) -> list[dict]:
        if self.use_fallback:
            return self.fallback_store.similarity_search_with_score(query, k)
            
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=k
            )
            
            output = []
            if results and results['documents'] and len(results['documents']) > 0:
                docs = results['documents'][0]
                metas = results['metadatas'][0] if results['metadatas'] else [{}] * len(docs)
                ids = results['ids'][0]
                
                # In Chroma query, distances are returned. Lower distance = higher similarity.
                # We'll normalize score or return distance.
                distances = results['distances'][0] if 'distances' in results and results['distances'] else [0.0] * len(docs)
                
                for doc, meta, doc_id, dist in zip(docs, metas, ids, distances):
                    output.append({
                        "document": doc,
                        "metadata": meta,
                        "id": doc_id,
                        "score": round(1.0 - dist, 4) if dist <= 1.0 else 0.0
                    })
            return output
        except Exception as e:
            logger.error(f"ChromaDB search failed: {e}. Searching fallback store.")
            return self.fallback_store.similarity_search_with_score(query, k)

# Global Chroma instance
chroma_db = ChromaManager()
