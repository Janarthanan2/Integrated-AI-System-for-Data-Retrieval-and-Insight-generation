def summarize_data(data_list):
    """
    Converts a list of dictionary records into a compact natural language summary.
    Use this to reduce token usage and help the LLM focus on key metrics.
    """
    if not data_list:
        return "No data found."
    
    count = len(data_list)
    
    # Helper to format values for LLM clarity
    def format_value(val, key=""):
        if val is None:
            return "N/A"
        if isinstance(val, float):
            # Currency-like fields get dollar formatting
            if any(k in key.lower() for k in ['profit', 'sales', 'revenue', 'amount', 'price', 'cost']):
                return f"${val:,.2f}"
            # Other floats get comma formatting
            return f"{val:,.2f}"
        if isinstance(val, int):
            return f"{val:,}"
        return str(val)
    
    # SMART STRATEGY: 
    # If the dataset is small (aggregated results), show EVERYTHING.
    # LLMs handle table-like text very well.
    # Optimized for LLM Context: Raw Data Only
    
    # For single aggregated values, provide a clear statement
    if count == 1 and len(data_list[0]) <= 3:
        parts = []
        for k, v in data_list[0].items():
            parts.append(f"{k.replace('_', ' ').title()}: {format_value(v, k)}")
        return "DATA: " + ", ".join(parts)
    
    # 1. Formatting for prompt (Markdown Table preferred for structure)
    lines = []
    # Header
    headers = list(data_list[0].keys())
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    
    # Rows
    for row in data_list:
        values = [format_value(row.get(h), h) for h in headers]
        lines.append("| " + " | ".join(values) + " |")
        
    return "\n".join(lines)

def analyze_trend(data_list):
    """
    Analyzes a time-series dataset to extract key trend insights:
    - Overall direction (Up/Down/Flat)
    - Month-over-Month (MoM) changes
    - Peak and Valley points
    Returns a textual summary of conclusions.
    """
    if not data_list:
        return "No trend data available."
    
    # 1. Identify Metric and Date Keys
    keys = list(data_list[0].keys())
    date_key = next((k for k in keys if "month" in k.lower() or "date" in k.lower()), keys[0]) # Fallback to first
    avg_key_candidates = ['sales', 'profit', 'amount', 'quantity', 'total', 'count']
    metric_key = next((k for k in keys if any(c in k.lower() for c in avg_key_candidates) and isinstance(data_list[0][k], (int, float))), None)
    
    if not metric_key:
        # Fallback: find first numeric key
        metric_key = next((k for k in keys if isinstance(data_list[0][k], (int, float))), None)
    
    if not metric_key:
        return summarize_data(data_list) # Fallback to standard table if no metric found

    # 2. Extract Series
    values = [d[metric_key] for d in data_list]
    dates = [d[date_key] for d in data_list]
    
    if len(values) < 2:
        return summarize_data(data_list)

    # 3. Compute Statistics
    start_val = values[0]
    end_val = values[-1]
    overall_change = end_val - start_val
    pct_change = (overall_change / start_val) * 100 if start_val != 0 else 0
    
    direction = "FLAT"
    if pct_change > 5: direction = "UPWARD"
    elif pct_change < -5: direction = "DOWNWARD"
    
    max_val = max(values)
    min_val = min(values)
    max_date = dates[values.index(max_val)]
    min_date = dates[values.index(min_val)]
    
    # 4. Generate Conclusions
    lines = [f"TREND ANALYSIS ({len(values)} periods):"]
    lines.append(f"- Overall Trend: {direction} ({pct_change:+.1f}%)")
    lines.append(f"- Start: {start_val:,.2f} ({dates[0]}) -> End: {end_val:,.2f} ({dates[-1]})")
    lines.append(f"- Peak: {max_val:,.2f} in {max_date}")
    lines.append(f"- Lowest: {min_val:,.2f} in {min_date}")
    
    # MoM Volatility
    lines.append("\nSignificant Changes:")
    for i in range(1, len(values)):
        curr = values[i]
        prev = values[i-1]
        mom_change = ((curr - prev) / prev) * 100 if prev != 0 else 0
        if abs(mom_change) > 10: # Only report significant >10% shifts
            lines.append(f"- {dates[i]}: {mom_change:+.1f}% vs previous month")
            
    return "\n".join(lines)
