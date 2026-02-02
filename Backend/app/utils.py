def summarize_data(data_list):
    """
    Converts a list of dictionary records into a compact natural language summary.
    Use this to reduce token usage and help the LLM focus on key metrics.
    """
    if not data_list:
        return "No data found."
    
    count = len(data_list)
    
    # SMART STRATEGY: 
    # If the dataset is small (aggregated results), show EVERYTHING.
    # LLMs handle table-like text very well.
    if count <= 50:
        lines = [f"Dataset contains {count} records:"]
        # Header
        headers = list(data_list[0].keys())
        lines.append(" | ".join(headers))
        lines.append("-" * (len(headers) * 10))
        
        # Rows
        for row in data_list:
            values = [str(row.get(h, "")) for h in headers]
            lines.append(" | ".join(values))
            
        return "\n".join(lines)
    
    # Fallback for large raw datasets (e.g. 1000 rows): Heuristic Summary
    # 1. Basic Stats
    summary_lines = [f"Dataset contains {count} records (Showing top 10 samples only)."]
    
    # 2. Key Metrics Heuristics (Summing large raw data)
    numeric_sums = {}
    total_loss = 0.0
    
    for row in data_list:
        for k, v in row.items():
            k_lower = k.lower()
            if isinstance(v, (int, float)):
                 if any(term in k_lower for term in ['sales', 'amount', 'profit', 'quantity', 'total']):
                     numeric_sums[k] = numeric_sums.get(k, 0) + v
                 if 'profit' in k_lower and v < 0:
                     total_loss += v
    
    if numeric_sums:
        for k, v in numeric_sums.items():
             summary_lines.append(f"- Net {k.title()}: {v:,.2f}")
        
    # 3. Snippet (Top 10)
    for i, row in enumerate(data_list[:10]):
        row_str = ", ".join([f"{k}: {v}" for k,v in row.items()])
        summary_lines.append(f"  {i+1}. {row_str}")
        
    return "\n".join(summary_lines)
