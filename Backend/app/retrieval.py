from sentence_transformers import SentenceTransformer, util
import os
import glob
import torch
import pickle
from functools import lru_cache

class RetrievalManager:
    """
    Manages document loading, embedding, and semantic retrieval using Sentence Transformers.
    Optimized with Caching, Normalization, and Stop-word Removal.
    """
    
    def __init__(self, data_dir: str = "../data"):
        print("Initializing Retrieval Manager...")
        self.data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), data_dir))
        self.cache_path = os.path.join(self.data_dir, "embeddings_cache.pkl")
        
        # Load Model
        device = "cuda" if torch.cuda.is_available() else "cpu"
        try:
             self.model = SentenceTransformer('all-MiniLM-L6-v2', device=device)
        except Exception as e:
             self.model = SentenceTransformer('all-MiniLM-L6-v2', device="cpu")
             
        self.documents = []
        self.filenames = []
        self.doc_metadata = [] # Store metadata for chunks (filename, chunk_index)
        self.embeddings = None
        
        self.load_documents()

    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50):
        """
        Splits text into chunks.
        Strategy: Split by double newlines (paragraphs), then sub-chunk if too long.
        """
        chunks = []
        paragraphs = text.split('\n\n')
        
        current_chunk = ""
        
        for para in paragraphs:
            para = para.strip()
            if not para: continue
            
            # Simple accumulation
            if len(current_chunk) + len(para) < chunk_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para + "\n\n"
        
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        return chunks

    def load_documents(self):
        """Loads documents. Uses Disk Cache if available and valid."""
        if not os.path.exists(self.data_dir):
            return

        # 1. Try Loading from Cache
        if os.path.exists(self.cache_path):
            try:
                print("Loading embeddings from cache...")
                with open(self.cache_path, "rb") as f:
                    cache_data = pickle.load(f)
                    self.documents = cache_data['documents']
                    self.filenames = cache_data['filenames']
                    self.doc_metadata = cache_data.get('doc_metadata', []) # Load metadata
                    self.embeddings = cache_data['embeddings']
                print(f"Loaded {len(self.documents)} chunks from cache.")
                return 
            except Exception as e:
                print(f"Cache load failed ({e}), rebuilding...")

        # 2. Rebuild if no cache
        self.documents = []
        self.filenames = []
        extensions = ['*.txt', '*.md', '*.csv', '*.json']
        
        for ext in extensions:
            for filepath in glob.glob(os.path.join(self.data_dir, ext)):
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                        if content.strip():
                            # Chunking applied here
                            file_chunks = self._chunk_text(content)
                            for i, chunk in enumerate(file_chunks):
                                self.documents.append(chunk)
                                self.filenames.append(os.path.basename(filepath))
                                self.doc_metadata.append({"filename": os.path.basename(filepath), "chunk_index": i})
                except Exception as e:
                    print(f"Error reading {filepath}: {e}")

        if self.documents:
            print(f"Embedding {len(self.documents)} documents...")
            self.embeddings = self.model.encode(self.documents, convert_to_tensor=True)
            
            # Save to Cache
            try:
                with open(self.cache_path, "wb") as f:
                    pickle.dump({
                        'documents': self.documents,
                        'filenames': self.filenames,
                        'doc_metadata': self.doc_metadata,
                        'embeddings': self.embeddings
                    }, f)
                print("Embedding complete and cached.")
            except Exception as e:
                 print(f"Warning: Could not save cache: {e}")

    @staticmethod
    def normalize_query(query: str) -> str:
        """
        Simple normalization to improve cache hit rate and focus on keywords.
        Removes common stop words.
        """
        stop_words = {'can', 'you', 'please', 'tell', 'me', 'what', 'happened', 'to', 'in', 'the', 'is', 'are', 'a', 'an', 'of', 'for', 'show'}
        words = query.lower().split()
        keywords = [w for w in words if w not in stop_words]
        return " ".join(keywords)

    @lru_cache(maxsize=100)
    def retrieve_cached(self, query: str, top_k: int):
        """Cached wrapper for retrieval math."""
        if not self.documents or self.embeddings is None:
            return []
            
        query_emb = self.model.encode(query, convert_to_tensor=True)
        scores = util.cos_sim(query_emb, self.embeddings)[0]
        top_results = torch.topk(scores, k=min(top_k, len(self.documents)))
        
        results = []
        for score, idx in zip(top_results.values, top_results.indices):
            idx = int(idx)
            if score < 0.2: continue
            
            # Enrich with metadata if available
            meta = self.doc_metadata[idx] if idx < len(self.doc_metadata) else {}
            results.append((self.filenames[idx], self.documents[idx], float(score), meta))
        return results

    def retrieve(self, query: str, top_k: int = 3):
        """
        Retrieves top-k most relevant documents.
        """
        norm_query = self.normalize_query(query)
        # Use cached method
        raw_results = self.retrieve_cached(norm_query, top_k)
        
        # Convert back to dict list
        return [{"filename": r[0], "content": r[1], "score": r[2], "metadata": r[3]} for r in raw_results]