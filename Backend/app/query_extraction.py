import re
import datetime
from .fuzzy_utils import fuzzy_clean_query

class QueryExtractor:
    """
    Agentic Controller (Python-Based)
    
    ROLE:
    1. Understands user intent via Rules/Regex.
    2. Decides which specialized analysis path to take.
    3. Outputs a structured JSON decision for the main loop to execute.
    
    STRICT RULES:
    - NO SQL generation.
    - NO direct database access.
    - Output ONLY structured decisions.
    """
    
    def __init__(self):
        self.metrics_map = {
            "sales": "sales", "revenue": "sales", "amount": "sales",
            "profit": "profit", "earnings": "profit", "loss": "profit",
            "quantity": "quantity", "units": "quantity", "count": "quantity"
        }

    def decide_action(self, query: str) -> dict:
        """
        Main Agentic Entry Point.
        Returns JSON decision object:
        {
          "intent": "...",
          "analysis_type": "kpi" | "trend" | "root_cause" | "comparison",
          "data_functions": [{"name": "...", "parameters": {...}}],
          "use_documents": bool,
          "generate_followups": bool
        }
        """
        q = query.lower()
        cleaned_q = fuzzy_clean_query(query)
        q_clean = cleaned_q.lower()
        
        # 1. Extract Entities (Filters)
        filters = self._extract_filters(q, q_clean)
        
        # 2. Extract Metrics
        metrics = self._extract_metrics(q)
        
        # 3. Determine Analysis Type & Intent
        analysis_type = "kpi" # default
        intent = "AGGREGATE"
        use_docs = False
        data_fns = []
        
        # --- Logic Tree ---
        
        # A. Root Cause / Diagnostic ("Why?")
        if any(x in q for x in ["why", "reason", "cause", "driver", "explain", "drop", "decline", "spike"]):
            analysis_type = "root_cause"
            intent = "DIAGNOSTIC"
            use_docs = True # RAG is crucial for "Why"
            
            # Function: Perform RCA
            data_fns.append({
                "name": "perform_root_cause_analysis",
                "parameters": {
                    "filters": filters,
                    "metric": metrics[0] if metrics else "sales"
                }
            })

        # B. Trend / Over Time ("Trend", "Growth", "Monthly")
        elif any(x in q for x in ["trend", "over time", "monthly", "growth", "line chart", "timeline", "history"]):
            analysis_type = "trend"
            intent = "TREND"
            
            # Function: Get Trend
            data_fns.append({
                "name": "get_trend",
                "parameters": {
                    "filters": filters,
                    "metric": metrics[0] if metrics else "sales",
                    "interval": "month" # Default to monthly
                }
            })

        # C. Comparison ("Compare", "Vs", "Difference")
        elif any(x in q for x in ["compare", "versus", " vs ", "difference", "better", "worse"]):
            analysis_type = "comparison"
            intent = "AGGREGATE" # Technical intent for generation
            
            # Identify dimensions to compare
            # (Simple heuristic: if 2 regions found, or just group by region)
            # For prototype: Default to comparing by Region or Category if mentioned
            dim = "region"
            if "category" in filters or "category" in q: dim = "category"
            
            data_fns.append({
                "name": "get_comparison",
                "parameters": {
                    "filters": filters,
                    "metric": metrics[0] if metrics else "sales",
                    "dimension": dim
                }
            })

        # D. Ranking / Top N ("Top 5", "Best", "Highest")
        elif any(x in q for x in ["top", "bottom", "best", "worst", "highest", "lowest", "rank"]):
            analysis_type = "kpi" # or "list"
            intent = "LIST"
            
            # Determine grouping
            group_by = "sub_category" # default for "top products" (Schema has no product_name, only sub_category)
            if "region" in q: group_by = "region"
            if "category" in q: group_by = "category"
            if "state" in q: group_by = "state"
            if "city" in q: group_by = "city"
            if "customer" in q: group_by = "customer_name"

            data_fns.append({
                "name": "get_top_n",
                "parameters": {
                    "filters": filters,
                    "metric": metrics[0] if metrics else "sales",
                    "group_by": group_by,
                    "n": 5
                }
            })
            
        # E. RAG Only ("How to", "Policy")
        elif any(x in q for x in ["how to", "policy", "definition", "process", "document"]):
            analysis_type = "general"
            intent = "RAG"
            use_docs = True
            # No data function needed

        # F. Standard KPI / Aggregation ("Total sales", "How much")
        else:
            analysis_type = "kpi"
            intent = "AGGREGATE"
            
            data_fns.append({
                "name": "get_kpi",
                "parameters": {
                    "filters": filters,
                    "metrics": metrics
                }
            })

        # 4. Construct Decision JSON
        decision = {
            "intent": intent,
            "analysis_type": analysis_type,
            "data_functions": data_fns,
            "use_documents": use_docs,
            "generate_followups": True, # Default to true for engagement
            "debug_info": {
                "original_query": query,
                "extracted_filters": filters,
                "sanitized_query": cleaned_q
            }
        }
        
        return decision

    def _extract_filters(self, q, q_clean):
        filters = {}
        # Region
        regions = ["North", "South", "East", "West", "Central"]
        for r in regions:
            if r.lower() in q:
                filters["region"] = r # Normalized case?
        
        # Year
        year_match = re.search(r'\b(20[2-3][0-9])\b', q)
        if year_match:
            filters["year"] = int(year_match.group(1))

        # Category from Valid Entities
        from .fuzzy_utils import VALID_ENTITIES
        if VALID_ENTITIES:
            for entity in sorted(VALID_ENTITIES, key=len, reverse=True):
                # exact word match preferred
                if f" {entity.lower()} " in f" {q_clean} ":
                    filters["category"] = entity # We treated everything as 'category' in DB for simplicity
                    break
        return filters

    def _extract_metrics(self, q):
        metrics = []
        for key, val in self.metrics_map.items():
            if key in q:
                metrics.append(val)
        if not metrics:
            metrics = ["sales"] # default
        return list(set(metrics))

    # Compatibility shim if main.py still calls extract_parameters (temporarily)
    def extract_parameters(self, query):
        decision = self.decide_action(query)
        # Map back to old format if needed during migration, or direct main.py to use decide_action
        # For safety during refactor, return a structure that mimics old but includes new
        return {
            "intent": decision["intent"],
            "filters": decision["debug_info"]["extracted_filters"],
            "metrics": ["sales"], # placeholder
            "sanitized_query": decision["debug_info"]["sanitized_query"],
            "agent_decision": decision # Pass full decision payload
        }
