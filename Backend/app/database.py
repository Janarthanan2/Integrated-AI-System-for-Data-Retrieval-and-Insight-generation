from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
import pandas as pd
import time
from .fuzzy_utils import fuzzy_clean_query

load_dotenv()

class DatabaseManager:
    def __init__(self):
        # Default to a safe placeholder if not set
        base_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up one level from 'app' to 'Backend', then into 'data'
        data_dir = os.path.join(base_dir, "..", "data")
        default_db_path = os.path.join(data_dir, "sales_data.db")
        
        self.db_url = os.getenv("DATABASE_URL", f"sqlite:///{default_db_path}") 
        
        # Handle MySQL vs SQLite (prototype flexibility)
        print(f"DEBUG: Active Database URL: {self.db_url}")
        
        if "mysql" in self.db_url:
             self.engine = create_engine(self.db_url, execution_options={"isolation_level": "READ UNCOMMITTED"})
        else:
             self.engine = create_engine(self.db_url)
             
        self.load_entities()

    def load_entities(self):
        """
        Dynamically loads unique values from the database to populate the fuzzy matcher.
        """
        try:
            from .fuzzy_utils import set_valid_entities
            
            entities = []
            # We want to catch typos in these columns
            target_cols = ['category', 'sub_category', 'region', 'state']
            
            with self.engine.connect() as conn:
                for col in target_cols:
                    try:
                        # query = f"SELECT DISTINCT {col} FROM sales_data"
                        # efficient pandas read
                        df = pd.read_sql(f"SELECT DISTINCT {col} FROM sales_data", conn)
                        if not df.empty:
                            entities.extend(df[col].dropna().astype(str).tolist())
                    except Exception:
                        # Table might not exist yet during first run/migration
                        pass
            
            if entities:
                set_valid_entities(entities)
                
        except Exception as e:
            print(f"WARN: Failed to load dynamic entities: {e}")
    
    
    def query_dynamic(self, params: dict):
        """
        Constructs and executes a safe SQL query based on structured parameters.
        Pushing aggregation to the database engine (SQLite) for performance and correctness.
        """
        try:
            intent = params.get("intent", "LIST")
            metrics = params.get("metrics", ["sales"])
            filters = params.get("filters", {})
            group_by = params.get("group_by", [])
            
            # --- 1. Query Construction ---
            table_name = "sales_data"
            conditions = []
            sql_params = {}
            
            # Filters (Case-Insensitive)
            if "region" in filters:
                val = filters["region"]
                if isinstance(val, (list, tuple, set)):
                    # Multi-value logic
                    params_dict = {f"reg_{i}": v for i, v in enumerate(val)}
                    placeholders = ", ".join([f":reg_{i}" for i in range(len(val))])
                    conditions.append(f"LOWER(region) IN ({', '.join([f'LOWER(:reg_{i})' for i in range(len(val))])})")
                    sql_params.update(params_dict)
                else:
                    conditions.append("LOWER(region) = LOWER(:region)")
                    sql_params["region"] = val
                
            if "category" in filters:
                val = filters["category"]
                if isinstance(val, (list, tuple, set)):
                    # Multi-value logic for Category OR Sub-Category
                    # (cat IN (...) OR subcat IN (...))
                    # Simplified: We treat 'category' as generic.
                    # We need dynamic placeholders
                    placeholders = []
                    for i, v in enumerate(val):
                        key = f"cat_{i}"
                        sql_params[key] = v
                        placeholders.append(f"LOWER(:{key})")
                    
                    in_clause = ", ".join(placeholders)
                    conditions.append(f"(LOWER(category) IN ({in_clause}) OR LOWER(sub_category) IN ({in_clause}))")
                else:
                    conditions.append("(LOWER(category) = LOWER(:category) OR LOWER(sub_category) = LOWER(:category))")
                    sql_params["category"] = val
                
            if "year" in filters:
                conditions.append("substr(order_date, 1, 4) = :year")
                sql_params["year"] = str(filters["year"])
            
            where_clause = " AND ".join(conditions)
            if where_clause:
                where_clause = f"WHERE {where_clause}"

            # --- 2. Intent Handling ---
            
            if intent == "AGGREGATE":
                # Constructs: SELECT region, SUM(sales) as sales FROM ... GROUP BY region
                # Handling Date grouping specially
                select_groups = []
                group_clause_items = []
                
                for g in group_by:
                    if g == "date":
                        # Monthly trend default for aggregates involving date
                        select_groups.append("substr(order_date, 1, 7) as month")
                        group_clause_items.append("month")
                    elif g in ["region", "category", "sub_category", "state", "city", "product_name"]:
                         # Map specific internal names to DB columns if needed
                         col = g
                         if g == "product_name": col = "sub_category" # Fallback: No product column in schema
                         select_groups.append(col)
                         group_clause_items.append(col)

                # Metric Aggregation
                # Force CAST to ensure we sum numbers even if stored as text strings from CSV
                select_metrics = [f"SUM(CAST({m} AS REAL)) as {m}" for m in metrics]
                
                if not select_groups:
                    # Global Aggregate
                    final_sql = f"SELECT {', '.join(select_metrics)} FROM {table_name} {where_clause}"
                else:
                    # Grouped Aggregate
                    groups_str = ", ".join(select_groups)
                    # For GROUP BY clause, use the base column names or aliases
                    group_clause_str = ", ".join(group_clause_items)
                    
                    final_sql = f"SELECT {groups_str}, {', '.join(select_metrics)} FROM {table_name} {where_clause} GROUP BY {group_clause_str} ORDER BY {metrics[0]} DESC LIMIT 50"

            elif intent == "TREND":
                # Force Monthly Trend
                # SELECT substr(order_date, 1, 7) as month, SUM(sales) ... GROUP BY month
                select_metrics = [f"SUM(CAST({m} AS REAL)) as {m}" for m in metrics]
                final_sql = f"SELECT substr(order_date, 1, 7) as month, {', '.join(select_metrics)} FROM {table_name} {where_clause} GROUP BY month ORDER BY month ASC"
                
            else:
                # LIST / DEFAULT (Limit 50)
                # Select all columns
                final_sql = f"SELECT * FROM {table_name} {where_clause} LIMIT 50"

            # --- 3. Execution ---
            # print(f"DEBUG: Generated SQL: {final_sql} | Params: {sql_params}") 
            with self.engine.connect() as conn:
                df = pd.read_sql(text(final_sql), conn, params=sql_params)
            
            if df.empty:
                return []
                
            return df.to_dict(orient="records")
            
        except Exception as e:
            print(f"PYTHON QUERY ERROR: {e}")
            return {"error": str(e)}

    def get_kpi(self, filters: dict, metrics: list):
        """
        Agent Function: KPI Summary
        Returns simple aggregated values.
        """
        params = {
            "intent": "AGGREGATE",
            "metrics": metrics,
            "filters": filters,
            "group_by": [] # Global aggregate
        }
        return self.query_dynamic(params)

    def get_trend(self, filters: dict, metric: str, interval: str = "month"):
        """
        Agent Function: Trend Analysis
        Returns timeseries data.
        """
        params = {
            "intent": "TREND",
            "metrics": [metric],
            "filters": filters,
            "group_by": ["date"]
        }
        return self.query_dynamic(params)

    def get_top_n(self, filters: dict, metric: str, group_by: str, n: int = 5):
        """
        Agent Function: Ranking
        Returns top N items.
        """
        # We need to tweak query_dynamic to handle LIMIT and Order By specifically if not generic
        # OR we just construct a specific query here.
        # For prototype consistency, we re-use query_dynamic which handles "AGGREGATE" with group_by
        # query_dynamic applies LIMIT 50 by default, we can slice it or add n param later if needed.
        params = {
            "intent": "AGGREGATE",
            "metrics": [metric],
            "filters": filters,
            "group_by": [group_by]
        }
        results = self.query_dynamic(params)
        
        if isinstance(results, dict) and "error" in results:
            return results # Propagate error
            
        return results[:n] if isinstance(results, list) else []

    def get_comparison(self, filters: dict, metric: str, dimension: str):
        """
        Agent Function: Comparison
        Returns grouped data for comparison.
        """
        params = {
            "intent": "AGGREGATE",
            "metrics": [metric],
            "filters": filters,
            "group_by": [dimension]
        }
        return self.query_dynamic(params)

    def execute_query(self, query_text: str, scope: str = None):
        """
        Executes a SQL query with strictly enforced scope injection.
        """
        # 1. Validation: Read-Only Check
        if not query_text.strip().upper().startswith("SELECT"):
            return {"error": "Security Violation: Only SELECT queries are allowed."}

        # 2. Scope Injection
        # ... logic ...
        
        # 3. Execution
        try:
            # SAFETY LIMIT: Prevent LLM Context Overflow
            # If the query doesn't already have a LIMIT, we inject one.
            final_query = query_text
            
            # Auto-correction for known table mismatch (Prototype Helper)
            # Fix: Only replace 'FROM sales' if it isn't already 'FROM sales_data'
            # We check if 'sales' is followed by space/end and NOT preceded by '_'
            if "FROM sales_data" not in final_query:
                 if "FROM sales " in final_query or final_query.strip().endswith("FROM sales"):
                     final_query = final_query.replace("FROM sales", "FROM sales_data")
                     
            # Simple SQL parsing to inject scope if needed
            if scope:
                 # Auto-correct scope if it's a known category typo
                 # e.g. scope="Fiñnes" -> "Sports & Fitness"
                 clean_scope = fuzzy_clean_query(scope)
                 
                 if "WHERE" in final_query.upper():
                    final_query += f" AND region = '{clean_scope}'"
                 else:
                    final_query += f" WHERE region = '{clean_scope}'"

            # SMART LIMIT: Allow unlimited aggregation queries, limit raw SELECT *
            # Aggregation keywords: SUM, COUNT, AVG, MAX, MIN, GROUP BY
            has_aggregation = any(keyword in final_query.upper() for keyword in ['SUM(', 'COUNT(', 'AVG(', 'MAX(', 'MIN(', 'GROUP BY'])
            
            if not has_aggregation and "LIMIT" not in final_query.upper():
                # CONFIGURABLE LIMIT: Allow user to set limit or disable it (0/None)
                default_limit = os.getenv("DEFAULT_DB_LIMIT", "50")
                
                if default_limit and default_limit.lower() not in ["0", "none", "unlimited", "false"]:
                    try:
                        valid_limit = int(default_limit)
                        final_query += f" LIMIT {valid_limit}"
                    except ValueError:
                        final_query += " LIMIT 50" # Fallback if env var is garbage
                else:
                    print(f"DEBUG: Unlimited Query Execution (DEFAULT_DB_LIMIT={default_limit})")
            
            query_start = time.time()
            with self.engine.connect() as connection:
                print(f"DEBUG: Executing SQL: {final_query}")
                result = pd.read_sql(text(final_query), connection)
                query_duration = time.time() - query_start
                
                print(f"DEBUG: SQL Query Time: {query_duration:.2f}s, Rows: {len(result)}")
                
                return result.to_dict(orient="records")
        except Exception as e:
            print(f"CRITICAL DB ERROR: {e}")
            return {"error": str(e)}

    def get_schema(self):
        """Returns simplified schema for the LLM to understand structure."""
        # Hardcoding for the prototype as 'inspect' can be slow on large remote DBs
        return """
        Table: sales_data
        Columns:
        - Order ID
        - Date
        - Category
        - Product
        - Sales
        - Quantity
        - Profit
        """
