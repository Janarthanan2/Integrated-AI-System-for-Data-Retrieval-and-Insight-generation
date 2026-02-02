import pandas as pd
from typing import List

def generate_dynamic_optimization(df: pd.DataFrame, table_name: str) -> str:
    """
    Analyzes a DataFrame and generates SQL optimization commands (Constraints & Indexes).
    """
    commands = []
    
    # 1. Primary Key Detection
    # Logic: Column is unique (count == nunique) AND contains 'id' in name
    for col in df.columns:
        if 'id' in col.lower() and df[col].is_unique:
            commands.append(f"ALTER TABLE {table_name} ADD CONSTRAINT pk_{table_name}_{col} PRIMARY KEY ({col});")
    
    # 2. Date Indexes
    # Logic: Datetime type OR 'date'/'time' in name
    for col in df.columns:
        is_datetime = pd.api.types.is_datetime64_any_dtype(df[col])
        name_match = any(x in col.lower() for x in ['date', 'time', 'created_at', 'timestamp'])
        
        if is_datetime or name_match:
            idx_name = f"idx_{table_name}_{col}"
            commands.append(f"CREATE INDEX {idx_name} ON {table_name}({col});")
            
    # 3. Filter Indexes (Categorical)
    # Logic: Object/String type AND low cardinality (< 50 unique)
    for col in df.columns:
        if df[col].dtype == 'object' or df[col].dtype.name == 'category':
            n_unique = df[col].nunique()
            if 0 < n_unique < 50:
                # Skip if it's likely a boolean or extremely small enum (optional, but requested logic is <50)
                # Also ensure it's not the PK (already handled, but PK usually high cardinality)
                idx_name = f"idx_{table_name}_{col}"
                # Check if we haven't already indexed this (e.g. if it had 'date' in name?) 
                # Simplest is just add it. SQL engines handle redundant index creation errors or we can ignore here.
                # However, intended for 'categorical' text.
                commands.append(f"CREATE INDEX {idx_name} ON {table_name}({col});")

    # 4. Composite Indexes (Hierarchies)
    # Logic: Detect pairs like (Region, State), (Category, Sub-Category)
    # Heuristics: Look for specific semantic pairs or parent-child naming patterns
    hierarchy_pairs = [
        ('region', 'state'),
        ('category', 'sub_category'),
        ('country', 'city'),
        ('brand', 'model'),
        ('section', 'aisle')
    ]
    
    cols_lower = [c.lower() for c in df.columns]
    col_map = {c.lower(): c for c in df.columns}
    
    for parent, child in hierarchy_pairs:
        if parent in cols_lower and child in cols_lower:
            actual_parent = col_map[parent]
            actual_child = col_map[child]
            idx_name = f"idx_{table_name}_{parent}_{child}"
            commands.append(f"CREATE INDEX {idx_name} ON {table_name}({actual_parent}, {actual_child});")

    return "\n".join(commands)
