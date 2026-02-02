from fastapi import APIRouter, HTTPException
from .database import DatabaseManager
import pandas as pd
from sqlalchemy import text

router = APIRouter(prefix="/analytics", tags=["analytics"])
db = DatabaseManager()

@router.get("/monthly-sales")
async def get_monthly_sales():
    """
    Returns total sales aggregated by month for the last 12 months (or all available).
    """
    query = """
    SELECT 
        substr(order_date, 1, 7) as month,
        SUM(sales) as total_sales
    FROM sales_data 
    GROUP BY substr(order_date, 1, 7)
    ORDER BY month ASC
    """
    try:
        with db.engine.connect() as conn:
            result = pd.read_sql(text(query), conn)
        return result.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/regional-performance")
async def get_regional_performance():
    """
    Returns total sales and profit by region.
    """
    query = """
    SELECT 
        region,
        SUM(sales) as total_sales,
        SUM(profit) as total_profit
    FROM sales_data
    GROUP BY region
    ORDER BY total_sales DESC
    """
    try:
        with db.engine.connect() as conn:
            result = pd.read_sql(text(query), conn)
        return result.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/declining-categories")
async def get_declining_categories():
    """
    Identifies categories where the latest month's sales are lower than the previous month's.
    """
    # SQLite Query to compare last 2 months for each category
    # Complex query: Get monthly sales per category, then lag comparison
    # helping logic:
    # 1. Get Month-Category Sales
    # 2. Filter for top 2 recent months
    # 3. Compare python side for simplicity (since sqlite w/o window functions or old versions can be tricky, 
    #    though recent sqlite supports window. Let's do python side logic for safety/simplicity with pandas).
    
    query = """
    SELECT 
        category,
        order_date,
        sales
    FROM sales_data
    """
    try:
        with db.engine.connect() as conn:
            df = pd.read_sql(text(query), conn)
        
        df['order_date'] = pd.to_datetime(df['order_date'])
        df['month'] = df['order_date'].dt.to_period('M')
        
        monthly_cat = df.groupby(['category', 'month'])['sales'].sum().reset_index()
        
        # Get last 2 months
        latest_month = monthly_cat['month'].max()
        prev_month = latest_month - 1
        
        latest_data = monthly_cat[monthly_cat['month'] == latest_month].set_index('category')
        prev_data = monthly_cat[monthly_cat['month'] == prev_month].set_index('category')
        
        declining = []
        for cat in latest_data.index:
            if cat in prev_data.index:
                curr_sales = latest_data.loc[cat, 'sales']
                old_sales = prev_data.loc[cat, 'sales']
                if curr_sales < old_sales:
                    declining.append({
                        "category": cat,
                        "current_month": str(latest_month),
                        "previous_month": str(prev_month),
                        "sales_change": round(((curr_sales - old_sales) / old_sales) * 100, 2),
                        "current_sales": round(curr_sales, 2),
                        "previous_sales": round(old_sales, 2)
                    })
        
        # Sort by biggest drop %
        declining.sort(key=lambda x: x['sales_change'])
        
        return declining
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/top-products")
async def get_top_products():
    """
    Returns top 10 selling products (sub-categories) by total revenue.
    """
    query = """
    SELECT 
        sub_category as product,
        SUM(sales) as total_sales,
        SUM(quantity) as total_quantity
    FROM sales_data
    GROUP BY sub_category
    ORDER BY total_sales DESC
    LIMIT 10
    """
    try:
        with db.engine.connect() as conn:
            result = pd.read_sql(text(query), conn)
        return result.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from .optimization import generate_dynamic_optimization

@router.get("/optimize-schema")
async def optimize_schema():
    """
    Dynamically analyzes the sales_data table and returns SQL optimization commands.
    """
    try:
        # Load entire dataset for analysis (in production run sample or use schema inspection)
        # Since we need cardinality, we load data.
        with db.engine.connect() as conn:
            df = pd.read_sql("SELECT * FROM sales_data", conn)
            
        sql_commands = generate_dynamic_optimization(df, "sales_data")
        return {"sql_commands": sql_commands}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def perform_root_cause_analysis(filters: dict = None, metric: str = "sales"):
    """
    Internal function to perform diagnostic analysis/drill-down on data.
    Identifies drivers of change between periods.
    """
    if filters is None: filters = {}
    
    # default to 2 recent months
    query = f"""
    SELECT order_date, region, category, sub_category, {metric} as value
    FROM sales_data
    """
    
    try:
        with db.engine.connect() as conn:
            df = pd.read_sql(text(query), conn)
            
        if df.empty:
            return {"error": "No data available."}
            
        df['order_date'] = pd.to_datetime(df['order_date'])
        df['month'] = df['order_date'].dt.to_period('M')
        
        all_months = sorted(df['month'].unique())
        if len(all_months) < 2:
            return {"error": "Insufficient history for trend analysis."}
            
        current_month = all_months[-1]
        prev_month = all_months[-2]
        
        # Filter if needed (e.g. if user asked "Why did East drop?")
        # We apply filtering in memory for now for complex intersection
        target_df = df.copy()
        if "region" in filters:
            target_df = target_df[target_df['region'].str.lower() == filters['region'].lower()]
        
        current_data = target_df[target_df['month'] == current_month]
        prev_data = target_df[target_df['month'] == prev_month]
        
        if current_data.empty or prev_data.empty:
             return {"error": f"No data found for comparison between {prev_month} and {current_month} with filters {filters}"}

        # Global Delta
        curr_total = current_data['value'].sum()
        prev_total = prev_data['value'].sum()
        delta = curr_total - prev_total
        percent_change = ((delta / prev_total) * 100) if prev_total != 0 else 0
        
        # Drill Downs
        drivers = []
        
        # 1. Region Impact
        if "region" not in filters: # Only drill region if not already filtered by it
            reg_curr = current_data.groupby('region')['value'].sum()
            reg_prev = prev_data.groupby('region')['value'].sum()
            reg_delta = (reg_curr - reg_prev).dropna()
            for r, d in reg_delta.items():
                drivers.append({"name": f"Region: {r}", "impact": d, "type": "Region"})
                
        # 2. Sub-Category Impact
        sub_curr = current_data.groupby('sub_category')['value'].sum()
        sub_prev = prev_data.groupby('sub_category')['value'].sum()
        sub_delta = (sub_curr - sub_prev).dropna()
        for s, d in sub_delta.items():
            drivers.append({"name": f"Product: {s}", "impact": d, "type": "Product"})
            
        # Sort drivers by raw impact interaction with global direction
        # If Global is DOWN (-), we want things that are NEGATIVE.
        # If Global is UP (+), we want things that are POSITIVE.
        
        is_growth = delta > 0
        
        # Sort by actual value
        drivers.sort(key=lambda x: x['impact'])
        
        if not is_growth:
            # Dropping: Show bottom 3 (biggest negatives)
            top_factors = drivers[:3]
        else:
            # Growing: Show top 3 (biggest positives)
            top_factors = drivers[-3:][::-1]
            
        return {
            "intent": "DIAGNOSTIC",
            "metric": metric,
            "period": f"{prev_month} vs {current_month}",
            "global_change": delta,
            "pct_change": percent_change,
            "factors": top_factors,
            "summary": f"{metric.title()} {'increased' if is_growth else 'decreased'} by {abs(delta):.2f} ({percent_change:.1f}%)."
        }

    except Exception as e:
        return {"error": str(e)}
