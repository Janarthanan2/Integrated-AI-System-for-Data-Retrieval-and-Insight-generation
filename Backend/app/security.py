import re

class SecurityManager:
    """
    Handles scope enforcement and intent extraction to ensure secure and valid data access.
    """
    
    def __init__(self):
        # Allowable scopes (Regions)
        self.VALID_SCOPES = ["North", "South", "East", "West"]

    def extract_scope_and_intent(self, query: str):
        """
        Parses the user query to identify the intent (Database vs RAG) and the scope (Region).
        Enforces that only one scope is present.
        """
        query_lower = query.lower()
        
        # 1. Scope Extraction
        detected_scopes = []
        for scope in self.VALID_SCOPES:
            if scope.lower() in query_lower:
                detected_scopes.append(scope)
        
        # Enforce Single Scope Rule
        if len(detected_scopes) > 1:
            raise ValueError(f"Security Alert: Multiple scopes detected ({', '.join(detected_scopes)}). Please limit your query to one region at a time.")
        
        current_scope = detected_scopes[0] if detected_scopes else None
        
        # 2. Intent Detection (Heuristic based for now, can be upgraded to Semantic later)
        # DB Intent: Queries asking for specific metrics, numbers, tables
        # RAG Intent: Queries asking for reasons, explanations, summaries
        
        db_keywords = ["how many", "count", "total", "sum", "average", "list", "show", "price", "sales", "revenue"]
        rag_keywords = ["why", "explain", "cause", "reason", "summary", "analyze", "what happened", "trend"]
        
        is_db = any(k in query_lower for k in db_keywords)
        is_rag = any(k in query_lower for k in rag_keywords)
        
        # Default to RAG if ambiguous or both (usually we need data for RAG anyway, but strict separation requested)
        # If user asks "Why did sales drop in North?", we need DB data for "sales drop" facts AND RAG for "Why".
        # For this modular architecture, we will flag primarily based on the 'Head' of the query.
        
        intent = "RAG"
        if is_db and not is_rag:
            intent = "DATABASE"
        elif is_rag:
            intent = "RAG" # RAG often needs DB data too, but the 'Primary' handler is RAG
        else:
            intent = "CHAT" # Fallback
            
        return {
            "scope": current_scope,
            "intent": intent,
            "sanitized_query": query.replace("'", "''") # Basic SQL injection protection for literal safeguards
        }
    
    def validate_access(self, scope):
        """
        Final check before database execution.
        """
        if scope and scope not in self.VALID_SCOPES:
             raise ValueError(f"Access Denied: Invalid scope '{scope}'.")
        return True
