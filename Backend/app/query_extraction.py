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
            "DOCUMENT": ["how to", "policy", "strategy", "reason", "cause", "document", "report", "details", "explain"]
        }
        
        # Dynamic column loading from database
        self.groupable_columns = []
        self.metric_columns = []
        self.date_columns = []  # NEW: Track date columns for derived dimensions
        self.derived_time_dimensions = {}  # NEW: Map time keywords to source date column
        self._load_schema_columns()
        
    def _load_schema_columns(self):
        """Dynamically load column names from the database schema."""
        try:
            from sqlalchemy import create_engine, inspect
            import os
            from dotenv import load_dotenv
            load_dotenv()
            
            base_dir = os.path.dirname(os.path.abspath(__file__))
            data_dir = os.path.join(base_dir, "..", "data")
            default_db_path = os.path.join(data_dir, "sales_data.db")
            db_url = os.getenv("DATABASE_URL", f"sqlite:///{default_db_path}")
            
            engine = create_engine(db_url)
            inspector = inspect(engine)
            
            # Get columns from sales_data table
            columns = inspector.get_columns("sales_data")
            
            # Categorize columns
            numeric_types = ['INTEGER', 'REAL', 'FLOAT', 'DOUBLE', 'DECIMAL', 'NUMERIC', 'INT', 'BIGINT']
            date_indicators = ['date', 'time', 'timestamp', 'datetime', 'created', 'updated']
            
            for col in columns:
                col_name = col['name'].lower()
                col_type = str(col['type']).upper()
                
                # Skip ID columns
                if 'id' in col_name:
                    continue
                
                # Detect DATE columns (by type OR by name pattern)
                is_date = 'DATE' in col_type or 'TIME' in col_type or any(di in col_name for di in date_indicators)
                
                if is_date:
                    self.date_columns.append(col_name)
                    # Generate derived time dimensions for this date column
                    self._register_time_dimensions(col_name)
                elif any(nt in col_type for nt in numeric_types):
                    self.metric_columns.append(col_name)
                else:
                    # Text/categorical columns are groupable
                    self.groupable_columns.append(col_name)
            
            print(f"DEBUG: Loaded {len(self.groupable_columns)} groupable columns: {self.groupable_columns}")
            print(f"DEBUG: Loaded {len(self.metric_columns)} metric columns: {self.metric_columns}")
            print(f"DEBUG: Loaded {len(self.date_columns)} date columns: {self.date_columns}")
            print(f"DEBUG: Derived time dimensions: {list(self.derived_time_dimensions.keys())}")
            
        except Exception as e:
            print(f"WARN: Could not load schema dynamically, using defaults: {e}")
            # Fallback defaults
            self.groupable_columns = ['region', 'category', 'sub_category', 'state', 'city', 'segment', 'product_name']
            self.metric_columns = ['sales', 'profit', 'quantity', 'discount']
            self.date_columns = ['order_date']
            self._register_time_dimensions('order_date')
    
    def _register_time_dimensions(self, date_column: str):
        """
        Register derived time dimensions for a date column.
        E.g., for 'order_date', creates mappings for 'month', 'year', 'quarter', etc.
        """
        # Time units and their keyword variations
        time_units = {
            "month": ["month", "months", "monthly"],
            "year": ["year", "years", "yearly", "annual", "annually"],
            "quarter": ["quarter", "quarters", "quarterly", "q1", "q2", "q3", "q4"],
        }
        
        for unit, keywords in time_units.items():
            for kw in keywords:
                # Map keyword -> (unit_type, source_column)
                self.derived_time_dimensions[kw] = {"unit": unit, "source": date_column}
    
    def _normalize_column_name(self, name: str) -> str:
        """Normalize column names for matching (handles hyphens, underscores, spaces)."""
        return name.lower().replace('-', '_').replace(' ', '_')
    
    def _find_grouping_column(self, query_lower: str) -> str:
        """
        Dynamically find which column the user wants to group by.
        Uses semantic similarity for flexible matching.
        """
        # 1. Direct Match: Check for exact column name variations
        sorted_columns = sorted(self.groupable_columns, key=len, reverse=True)
        
        def pluralize(word):
            if word.endswith('y') and len(word) > 1 and word[-2] not in 'aeiou':
                return word[:-1] + 'ies'
            return word + 's'
        
        for col in sorted_columns:
            base_forms = [
                col,
                col.replace('_', '-'),
                col.replace('_', ' '),
                col.replace('_', ''),
            ]
            variations = base_forms.copy()
            for base in base_forms:
                variations.append(pluralize(base))
            
            for var in variations:
                if var in query_lower:
                    return col
        
        # 2. Semantic Match: Use embeddings to find closest column
        try:
            from .fuzzy_utils import get_semantic_model
            model = get_semantic_model()
            if model:
                # Extract nouns from query (words > 3 chars not in stopwords)
                stopwords = {'what', 'which', 'show', 'give', 'list', 'find', 'tell', 'the', 'are', 'best', 'highest', 'lowest'}
                query_words = [w for w in query_lower.split() if len(w) > 3 and w not in stopwords]
                
                print(f"DEBUG SEMANTIC: Query words for matching: {query_words}")
                
                if query_words:
                    # Use descriptive labels for better semantic matching
                    # Map column names to richer descriptions
                    col_descriptions = {
                        'region': 'geographic region area location',
                        'state': 'state province territory',
                        'category': 'category type class',
                        'sub_category': 'product item subcategory product_name goods merchandise'
                    }
                    
                    # Build list of (column, description) for matching
                    cols_to_match = []
                    descriptions = []
                    for col in self.groupable_columns:
                        cols_to_match.append(col)
                        descriptions.append(col_descriptions.get(col, col))
                    
                    col_embeddings = model.encode(descriptions)
                    query_embeddings = model.encode(query_words)
                    
                    from sklearn.metrics.pairwise import cosine_similarity
                    import numpy as np
                    
                    similarities = cosine_similarity(query_embeddings, col_embeddings)
                    best_score = np.max(similarities)
                    best_idx = np.unravel_index(np.argmax(similarities), similarities.shape)
                    matched_word = query_words[best_idx[0]]
                    matched_col = cols_to_match[best_idx[1]]
                    
                    print(f"DEBUG SEMANTIC: Best match '{matched_word}' -> '{matched_col}' (score: {best_score:.3f})")
                    
                    if best_score > 0.35:  # Lowered threshold for descriptive matching
                        return matched_col
        except Exception as e:
            print(f"WARN: Semantic matching failed: {e}")
        
        return None
        
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
        
        print(f"DEBUG LIMIT: Extracted limit={limit} from query: {clean_q}")
                
        # 3. Determine Analysis Type
        analysis_type = None
        
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
            
            # Group By - FULLY DYNAMIC!
            if intent == "TREND":
                group_by = ["date"]
            else:
                # Check for time-based dimensions (auto-detected from DATE columns)
                found_time_dim = None
                for kw, info in self.derived_time_dimensions.items():
                    if kw in query_lower:
                        found_time_dim = info["unit"]  # e.g., "month", "year", "quarter"
                        break
                
                if found_time_dim:
                    group_by.append(found_time_dim)
                else:
                    # Check for schema columns (auto-detected from database)
                    found_col = self._find_grouping_column(query_lower)
                    if found_col:
                        group_by.append(found_col)

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
