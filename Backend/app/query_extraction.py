import re
from .fuzzy_utils import fuzzy_clean_query

class QueryExtractor:
    """
    A logic-based extractor that determines the intent and parameters from a natural language query.
    Replaces the heavy text-to-SQL approach with a deterministic routing logic.
    """
    def __init__(self):
        print("Initializing Logic-Based Query Extractor...")
        # keywords mapping
        self.intent_map = {
            "AGGREGATE": ["total", "sum", "average", "mean", "count", "how many", "sales", "profit", "quantity", "volume", "top", "rank", "best", "worst", "visualize", "chart", "graph", "plot"],
            "TREND": ["trend", "growth", "over time", "monthly", "year over year", "yoy", "history", "progress", "change", "month"],
            "LIST": ["list", "show", "what are", "names", "bottom", "table", "raw data"],
            "GREETING": ["hi", "hello", "hey", "greetings", "good morning", "good afternoon", "good evening"],
            "LIST": ["list", "show", "what are", "names", "bottom", "table", "raw data"],
            "GREETING": ["hi", "hello", "hey", "greetings", "good morning", "good afternoon", "good evening"],
            "DOCUMENT": ["how to", "policy", "strategy", "reason", "cause", "document", "report", "details", "explain"]
        }
        
    def extract_parameters(self, query: str) -> dict:
        """
        Decides the action to take based on the user query and extracts parameters.
        Returns a dictionary compatible with the execution engine in main.py.
        """
        query_lower = query.lower()
        
        # 1. Determine Intent
        intent = "UNKNOWN" # Default fallback
        max_score = 0
        
        for cand_intent, keywords in self.intent_map.items():
            score = sum(1 for k in keywords if k in query_lower)
            if score > max_score:
                max_score = score
                intent = cand_intent
                
        # Heuristics updates
        if "compare" in query_lower:
            intent = "AGGREGATE" # Comparisons are usually aggregations
            
        # Priority: TREND overrides AGGREGATE if explicit trend keywords are present
        if "trend" in query_lower or "growth" in query_lower or "over time" in query_lower:
            intent = "TREND"
            
        if "why" in query_lower and ("sales" in query_lower or "profit" in query_lower or "drop" in query_lower):
            # RCA detection
            return self._handle_rca(query)
            
        if ("identify" in query_lower or "which" in query_lower) and ("decline" in query_lower or "declining" in query_lower):
             # Decline Analysis detection
             return self._handle_decline_analysis(query)

        # 2. Extract Entities (Basic Regex/Keyword)
        # We rely on database.py's dynamic query builder for strict filtering, 
        # so here we just extract potential keys.
        
        filters = {}
        # Clean query using fuzzy matcher to normalize entity names
        try:
             # Pass generic valid options if known, else it uses global cache
            clean_q = fuzzy_clean_query(query)
        except Exception:
            clean_q = query
            
        # Extract Year
        year_match = re.search(r'\b(20\d{2})\b', clean_q)
        if year_match:
            filters["year"] = int(year_match.group(1))
        
        # Extract Quarter (Q1, Q2, Q3, Q4 or "first quarter", "third quarter", etc.)
        quarter_map = {
            'q1': [1, 2, 3], 'first quarter': [1, 2, 3],
            'q2': [4, 5, 6], 'second quarter': [4, 5, 6],
            'q3': [7, 8, 9], 'third quarter': [7, 8, 9],
            'q4': [10, 11, 12], 'fourth quarter': [10, 11, 12]
        }
        
        query_lower_clean = clean_q.lower()
        for quarter_key, months in quarter_map.items():
            if quarter_key in query_lower_clean:
                filters["quarter_months"] = months
                break
            
        # Extract Region (Simplified check - real app would use the entity list)
        regions = ["north", "south", "east", "west", "central", "canada"]
        for r in regions:
            if r in clean_q.lower():
                filters["region"] = r.title()
                break # Only pick first match
        
        # Extract Category (Check dynamically loaded entities in cleaned query)
        # Import the global entity list from fuzzy_utils
        from .fuzzy_utils import VALID_ENTITIES
        
        # VALID_ENTITIES contains all unique values from category, sub_category, region, state columns
        # We check if any of these entities appear in the query
        for entity in VALID_ENTITIES:
            if entity.lower() in clean_q.lower():
                # Determine if it's a category-type filter (not a region or state)
                # Regions are already handled above, so skip them
                if entity.lower() not in [r.lower() for r in regions]:
                    filters["category"] = entity
                    break

        # Extract Limit (Top/Bottom N)
        limit = None
        limit_match = re.search(r'\b(top|bottom|first|last)\s+(\d+)\b', clean_q.lower())
        if limit_match:
            try:
                limit = int(limit_match.group(2))
            except ValueError:
                pass
        
        # Default limit for explicit "Top" without number (usually implies 5 or 10)
        if not limit and ("top" in clean_q.lower() or "best" in clean_q.lower()):
             # explicit "top products" without number -> limit to 5
             limit = 5
                
        # 3. Determine Analysis Type
        analysis_type = "text"
        
        # Explicit Visualization Overrides
        if "box plot" in query_lower or "boxplot" in query_lower:
            analysis_type = "box_plot"
        elif "violin" in query_lower: # Mapped to box plot variants in frontend for now
            analysis_type = "violin"
        elif "heatmap" in query_lower or "heat map" in query_lower:
            analysis_type = "heatmap"
        elif "treemap" in query_lower or "tree map" in query_lower:
            analysis_type = "treemap"
        elif "bubble" in query_lower:
            analysis_type = "bubble"
        elif "area" in query_lower and "chart" in query_lower:
            analysis_type = "area"
        elif "lag" in query_lower and "plot" in query_lower:
            analysis_type = "lag"
        elif "donut" in query_lower or "doughnut" in query_lower:
            analysis_type = "donut"
        elif "lollipop" in query_lower:
            analysis_type = "lollipop"
        elif "stacked" in query_lower:
            analysis_type = "stacked"
        elif "scatter" in query_lower:
            analysis_type = "scatter"
        elif "pie" in query_lower:
            analysis_type = "pie"
        elif "bar" in query_lower:
            analysis_type = "bar"
        elif "line" in query_lower:
            analysis_type = "line"
        
        # Default Logic if no explicit type requested
        elif intent == "TREND":
            analysis_type = "line"
        elif intent == "AGGREGATE":
             if "region" in query_lower or "state" in query_lower or "category" in query_lower:
                 analysis_type = "bar"
             elif "top" in query_lower or "rank" in query_lower:
                 analysis_type = "bar" # Top N usually looks best as a bar chart
             else:
                 analysis_type = "stat" # Single number
        elif intent == "LIST":
            analysis_type = "table"

        # 4. Construct Data Metrics & Groups
        metrics = []
        group_by = []
        
        if intent in ["AGGREGATE", "TREND", "LIST"]:
            # Metrics
            if "profit" in query_lower: metrics.append("profit")
            if "quantity" in query_lower: metrics.append("quantity")
            if not metrics: metrics.append("sales") # Default
            
            # Group By
            if intent == "TREND":
                group_by = ["date"]
            # Only check other groupings if NOT trend, to avoid mixed signals
            # Hierarchical Priority: City > State > Region
            elif "city" in query_lower: group_by.append("city")
            elif "state" in query_lower: group_by.append("state")
            elif "region" in query_lower: group_by.append("region")
            elif "category" in query_lower: group_by.append("category")
            elif "sub-category" in query_lower or "sub category" in query_lower: group_by.append("sub_category")
            elif "product" in query_lower: group_by.append("product_name")
            elif "segment" in query_lower: group_by.append("segment")
            elif "quarter" in query_lower: group_by.append("quarter")

        return {
            "intent": intent,
            "filters": filters,
            "sanitized_query": clean_q,
            "visualization_type": analysis_type,
            "metrics": metrics,
            "group_by": group_by,
            "limit": limit,
            # Legacy debug info if needed
            "debug_info": {
                "original_query": query,
                "score": max_score
            }
        }

    def _handle_decline_analysis(self, query: str) -> dict:
        """Handle Decline Analysis requests."""
        return {
            "intent": "DIAGNOSTIC", # Re-using DIAGNOSTIC intent but with specific visualization
            "filters": {"analysis_mode": "decline"}, # Special filter to trigger specific logic in main
            "sanitized_query": query,
            "visualization_type": "decline",
            "metrics": ["sales"],
            "group_by": ["category"],
            "debug_info": {"mode": "DECLINE_ANALYSIS"}
        }

    def _handle_rca(self, query: str) -> dict:
        """Handle Root Cause Analysis requests."""
        return {
            "intent": "DIAGNOSTIC",
            "filters": {},
            "sanitized_query": query,
            "visualization_type": "rca",
            "metrics": ["sales"], # Default for RCA
            "group_by": [],
            "debug_info": {"mode": "RCA"}
        }
