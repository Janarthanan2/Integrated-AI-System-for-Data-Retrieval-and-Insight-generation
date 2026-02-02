from mcp.server.fastmcp import FastMCP
import os
import glob
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Initialize FastMCP Server
mcp = FastMCP("rag-server")

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data"))

def get_documents():
    """Reads all .txt and .md files from the data directory."""
    docs = []
    filenames = []
    
    # Simple text loader for prototype
    for filepath in glob.glob(os.path.join(DATA_DIR, "*.txt")):
        with open(filepath, "r", encoding="utf-8") as f:
            docs.append(f.read())
            filenames.append(os.path.basename(filepath))
            
    return filenames, docs

@mcp.tool()
def list_documents() -> str:
    """List all available documents in the knowledge base."""
    filenames, _ = get_documents()
    return f"Available Documents: {', '.join(filenames)}"

@mcp.tool()
def search_documents(query: str) -> str:
    """
    Search for relevant document chunks using Semantic Search (Sentence Transformers).
    Returns the most relevant text segments.
    """
    filenames, docs = get_documents()
    if not docs:
        return "No documents found in the knowledge base."

    print("DEBUG: Loading Sentence Transformer Model...")
    from sentence_transformers import SentenceTransformer, util
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # 1. Encode the query
    query_embedding = model.encode(query, convert_to_tensor=True)
    
    # 2. Encode documents (In a real app, these should be pre-computed and stored in a Vector DB)
    doc_embeddings = model.encode(docs, convert_to_tensor=True)
    
    # 3. Compute Cosine Similarity
    # util.cos_sim returns a matrix [queries, docs]
    cosine_scores = util.cos_sim(query_embedding, doc_embeddings)[0]
    
    # 4. Find the best match
    best_score_idx = int(cosine_scores.argmax())
    best_score = float(cosine_scores[best_score_idx])
    
    print(f"DEBUG: Best Match Score: {best_score}")
    
    if best_score < 0.1: # Threshold lowered for prototype
        return f"I couldn't find a perfect match in the documents (Best Match: {best_score:.2f})."
        
    best_filename = filenames[best_score_idx]
    best_content = docs[best_score_idx]
    
    # --- Smart Summarization Step ---
    # Split content into sentences to find the specific answer
    import re
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', best_content)
    
    # Filter out empty or short sentences
    sentences = [s.strip() for s in sentences if len(s) > 20]
    
    if not sentences:
        return best_content[:500]
        
    # Encode sentences to find the best specific answer
    sentence_embeddings = model.encode(sentences, convert_to_tensor=True)
    sent_scores = util.cos_sim(query_embedding, sentence_embeddings)[0]
    
    best_sent_idx = int(sent_scores.argmax())
    best_sentence = sentences[best_sent_idx]
    
    # Return a structured, precise answer
    return f"According to **{best_filename}**:\n\n\"{best_sentence}\"\n\n(Context: {best_content[:200]}...)"

@mcp.tool()
def read_document(filename: str) -> str:
    """Read specific document content."""
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        return "File not found."
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

if __name__ == "__main__":
    mcp.run()
