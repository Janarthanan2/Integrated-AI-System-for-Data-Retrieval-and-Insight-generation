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
        self.embeddings = None
        
        self.load_documents()

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
                    self.embeddings = cache_data['embeddings']
                print(f"Loaded {len(self.documents)} documents from cache.")
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
                            self.documents.append(content)
                            self.filenames.append(os.path.basename(filepath))
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
            results.append((self.filenames[idx], self.documents[idx], float(score))) # Return tuple
        return results

    def retrieve(self, query: str, top_k: int = 3):
        """
        Retrieves top-k most relevant documents.
        """
        norm_query = self.normalize_query(query)
        # Use cached method
        raw_results = self.retrieve_cached(norm_query, top_k)
        
        # Convert back to dict list
        return [{"filename": r[0], "content": r[1], "score": r[2]} for r in raw_results]