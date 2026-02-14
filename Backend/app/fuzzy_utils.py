from difflib import get_close_matches
from sentence_transformers import SentenceTransformer, util
import torch

# Global variables
VALID_ENTITIES = []
ENTITY_EMBEDDINGS = None
MODEL = None

def load_embedding_model():
    """Lazy load the model to avoid circular import delays or startup bottlenecks."""
    global MODEL
    if MODEL is None:
        try:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            MODEL = SentenceTransformer('all-MiniLM-L6-v2', device=device)
        except Exception as e:
            print(f"WARN: Model load failed, falling back to CPU: {e}")
            MODEL = SentenceTransformer('all-MiniLM-L6-v2', device="cpu")

def get_semantic_model():
    """Returns the loaded embedding model for use in other modules."""
    global MODEL
    if MODEL is None:
        load_embedding_model()
    return MODEL

def set_valid_entities(entities: list):
    """
    Updates the list of valid entities and pre-computes their embeddings.
    """
    global VALID_ENTITIES, ENTITY_EMBEDDINGS, MODEL
    
    # Flatten and Clean
    clean_entities = list(set([str(e) for e in entities if e and len(str(e)) > 2]))
    VALID_ENTITIES = clean_entities
    
    # Pre-compute Embeddings
    try:
        load_embedding_model()
        if VALID_ENTITIES:
            ENTITY_EMBEDDINGS = MODEL.encode(VALID_ENTITIES, convert_to_tensor=True)
    except Exception as e:
        print(f"WARN: Failed to cache entity embeddings: {e}")

def fuzzy_clean_query(query: str, valid_options: list = None) -> str:
    """
    Hybrid Resolution Strategy:
    1. Exact Match (Dictionary)
    2. Strict Fuzzy Match (Difflib > 0.85)
    3. Semantic Match (Embeddings > 0.75)
    """
    global MODEL, ENTITY_EMBEDDINGS
    
    # Determine Reference Set
    reference_list = valid_options if valid_options else VALID_ENTITIES
    
    if not reference_list:
        return query
        
    words = query.split()
    new_words = []
    
    # Common words that should NEVER be fuzzy matched to entities
    STOP_WORDS = {
        "what", "where", "how", "who", "when", "which",
        "show", "list", "give", "tell", "me", "find",
        "top", "best", "worst", "bottom", "most", "least",
        "sales", "profit", "quantity", "revenue", "count",
        "average", "sum", "total", "metrics", "performance",
        "analyze", "analysis", "report", "trend", "growth",
        "and", "or", "with", "without", "for", "in", "by", "of", "at", "to",
        "state", "states", "city", "cities", "region", "regions",
        "category", "categories", "product", "products", "year", "month", "date"
    }
    
    # Load model if needed (for ad-hoc options or if not loaded)
    if MODEL is None:
        load_embedding_model()
        
    for word in words:
        # Skip small words and STOP_WORDS
        if len(word) < 4 or word.lower() in STOP_WORDS:
            new_words.append(word)
            continue
            
        word_lower = word.lower()
        
        # --- STRATEGY 1: EXACT MATCH (Case-Insensitive) ---
        exact_match = next((e for e in reference_list if e.lower() == word_lower), None)
        if exact_match:
            new_words.append(exact_match)
            continue
            
        # --- STRATEGY 2: STRICT FUZZY MATCH (Typos) ---
        # 0.85 Threshold for very close typos (e.g. "Phnes" -> "Phones")
        fuzzy_matches = get_close_matches(word, reference_list, n=1, cutoff=0.85)
        if fuzzy_matches:
            new_words.append(fuzzy_matches[0])
            continue
            
        # --- STRATEGY 3: SEMANTIC EMBEDDINGS (Synonyms) ---
        # "Notebooks" -> "Binders" or "Cell" -> "Phones"
        # Only run if we have a model and embeddings
        best_semantic_match = None
        
        try:
            # If using global list, use cached embeddings
            if reference_list is VALID_ENTITIES and ENTITY_EMBEDDINGS is not None:
                word_emb = MODEL.encode(word, convert_to_tensor=True)
                scores = util.cos_sim(word_emb, ENTITY_EMBEDDINGS)[0]
                best_score_idx = torch.argmax(scores).item()
                best_score = scores[best_score_idx].item()
                
                if best_score > 0.75: # High confidence for synonym
                    best_semantic_match = VALID_ENTITIES[best_score_idx]
                    # print(f"DEBUG: Semantic correction '{word}' -> '{best_semantic_match}' ({best_score:.2f})")
            
            # If using custom options (ad-hoc), compute on fly (slower but necessary)
            elif valid_options:
                word_emb = MODEL.encode(word, convert_to_tensor=True)
                opt_embs = MODEL.encode(valid_options, convert_to_tensor=True)
                scores = util.cos_sim(word_emb, opt_embs)[0]
                best_score_idx = torch.argmax(scores).item()
                if scores[best_score_idx].item() > 0.75:
                    best_semantic_match = valid_options[best_score_idx]

        except Exception as e:
            # Fallback loop
            pass
            
        if best_semantic_match:
            new_words.append(best_semantic_match)
        else:
            # No match found, keep original
            new_words.append(word)
            
    return " ".join(new_words)
