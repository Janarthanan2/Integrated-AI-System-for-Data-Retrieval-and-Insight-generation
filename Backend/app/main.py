from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .security import SecurityManager
from .database import DatabaseManager
from .retrieval import RetrievalManager
from .generation import GenerationManager
from .models import QueryRequest, QueryResponse
import uvicorn
import os
from fastapi.responses import StreamingResponse
import json
import asyncio
import numpy as np

# Import conversation history components
from .routers import auth_router, conversations_router
from .db_models.base import init_db, close_db


# Lifespan event handler for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup: Initialize conversation history database
    print("🚀 Initializing conversation history database...")
    try:
        await init_db()
        print("✅ Conversation history database ready")
    except Exception as e:
        print(f"⚠️ Could not initialize history DB (continuing anyway): {e}")
    
    yield  # App running
    
    # Shutdown: Close database connections
    print("🛑 Closing database connections...")
    await close_db()


# Initialize FastAPI with lifespan
app = FastAPI(
    title="Modular AI Analytics Backend",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Modules (Lazy loading can be considered, but direct init for now)
from .query_extraction import QueryExtractor

# Initialize Modules
try:
    security = SecurityManager()
    database = DatabaseManager()
    retrieval = RetrievalManager()
    generation = GenerationManager()
    extractor = QueryExtractor()
    print("All modules initialized successfully.")
except Exception as e:
    print(f"Startup Error: {e}")

from .utils import summarize_data, analyze_trend
import time

# ... (Imports)

@app.post("/query") # Removed response_model since it's a stream
async def process_query(request: QueryRequest):
    async def event_generator():
        start_time = time.time()
        user_query = request.query
        
        # Initialize variables to avoid UnboundLocalError
        intent = "UNKNOWN"
        context_data = ""
        print(f"DEBUG: Processing query: {user_query}")
        

        
        try:
            # 1. Intent & Parameter Extraction
            params = extractor.extract_parameters(user_query)
            print(f"DEBUG EXTRACTION: Intent={params.get('intent')} Filters={params.get('filters')} GroupBy={params.get('group_by')} Metrics={params.get('metrics')} Viz={params.get('visualization_type')}")
            
            # Context Recovery Logic (Follow-up handling)
            # If the user asks for a visualization but we couldn't detect grouping/metrics,
            # recover context from the previous query.
            has_viz_request = params.get("visualization_type") is not None
            needs_context = (not params.get("group_by")) and (params.get("intent") in ["LIST", "UNKNOWN", "AGGREGATE"])
            
            print(f"DEBUG CONTEXT: has_viz_request={has_viz_request}, needs_context={needs_context}, history_len={len(request.history) if request.history else 0}")
            
            if has_viz_request and needs_context and request.history:
                # Find the last USER message that was a DATA query (not a viz-change request)
                # Skip messages that are purely about changing visualization
                viz_only_keywords = ["visualize", "piechart", "barchart", "linechart", "show as", "convert to", "change to"]
                
                reversed_hist = request.history[::-1]
                last_data_msg = None
                for m in reversed_hist:
                    if m.get('role') != 'user':
                        continue
                    content = m.get('content', '').lower()
                    # Skip current query
                    if content.strip() == user_query.lower().strip():
                        continue
                    # Skip pure viz-change requests (short queries with only viz keywords)
                    is_viz_only = len(content.split()) <= 5 and any(k in content for k in viz_only_keywords)
                    if not is_viz_only:
                        last_data_msg = m
                        break
                
                if last_data_msg:
                    print(f"Recovering context from previous data query: {last_data_msg['content']}")
                    prev_params = extractor.extract_parameters(last_data_msg['content'])
                    
                    # Keep the viz type from current request, but use data context from previous
                    current_viz = params["visualization_type"]
                    params["intent"] = prev_params["intent"]
                    params["filters"] = prev_params["filters"]
                    params["metrics"] = prev_params["metrics"]
                    params["group_by"] = prev_params["group_by"]
                    params["limit"] = prev_params.get("limit")  # Also keep limit!
                    params["visualization_type"] = current_viz
                    
                    print(f"Context Recovered. Intent={params['intent']}, GroupBy={params['group_by']}, Limit={params.get('limit')}, Viz={params['visualization_type']}")

            intent = params["intent"]
            filters = params["filters"]
            scope = filters.get("region", "Global")
            if "category" in filters: scope += f" / {filters['category']}"
            sanitized_query = params["sanitized_query"]
            
            if intent == "GREETING":
                yield json.dumps({"type": "token", "chunk": "Hello! I am AI Data Analyst, your advanced AI analytics assistant. Ask me to analyze sales trends, show top products, or explain business strategies."}) + "\n"
                return

            # 2. Data Retrieval
            chart_metadata = None

            # 2. Data Retrieval
            if intent in ["AGGREGATE", "TREND", "LIST", "DATABASE", "DIAGNOSTIC", "DIRECT"]:
                
                db_start = time.time()
                
                if intent == "DIAGNOSTIC":
                    metric = params.get("metrics", ["sales"])[0]
                    
                    if params["filters"].get("analysis_mode") == "decline":
                         # Decline Analysis
                         from .analytics import perform_decline_analysis
                         decline_result = await perform_decline_analysis()
                         
                         if "error" in decline_result:
                             context_data += f"ANALYSIS ERROR: {decline_result['error']}\n"
                         else:
                             # STRICT RULE: Pass ONLY conclusions.
                             # decline_result is a list of dicts.
                             declining_items = [d for d in decline_result if d['sales_change'] < 0]
                             
                             if not declining_items:
                                 context_data += "CONCLUSION: No categories are currently declining. All patterns show growth or stability.\n"
                             else:
                                 context_data += "CONCLUSION: The following categories are declining (Month-over-Month):\n"
                                 for d in declining_items:
                                     context_data += f"- {d['category']}: Declined by {abs(d['sales_change'])}% (Current Sales: {d['current_sales']})\n"
                             
                             chart_metadata = {"type": params.get("visualization_type", "decline"), "data": declining_items}

                    else:
                        # Standard RCA
                        rca_result = await perform_root_cause_analysis(params["filters"], metric)
                        
                        if "error" in rca_result:
                             context_data += f"DIAGNOSTIC ERROR: {rca_result['error']}\n"
                        else:
                             factors_text = "\n".join([f"- {f['name']} contributed {f['impact']:+.2f}" for f in rca_result['factors']])
                             context_data += f"DIAGNOSTIC ANALYSIS ({rca_result['period']}):\n{rca_result['summary']}\nTop Drivers:\n{factors_text}\n\n"
                             chart_metadata = {"type": "rca", "data": rca_result.get('factors', [])}

                else:
                    db_results = await database.query_dynamic(params)
                    
                    if isinstance(db_results, dict) and "error" in db_results:
                        yield json.dumps({"type": "error", "content": db_results['error']}) + "\n"
                        return

                    # HARD STOP: If data is missing/empty, do NOT call LLM.
                        yield json.dumps({"type": "token", "chunk": "I don't see sufficient data to answer this question."}) + "\n"
                        return

                    # CLEAN DATA: Replace NaN with None for JSON compliance
                    for r in db_results:
                        for k, v in r.items():
                            if isinstance(v, float) and (np.isnan(v) or np.isinf(v)):
                                r[k] = None

                    print(f"DEBUG: Data retrieved. Rows={len(db_results)} Keys={list(db_results[0].keys())}")
                    
                    # Summarize
                    if intent == "TREND":
                        structured_summary = analyze_trend(db_results)
                    else:
                        structured_summary = summarize_data(db_results)
                        
                    # Just inject the raw table/summary. 
                    # The Prompt Template will handle labeling if needed.
                    context_data += f"{structured_summary}\n\n"
                    
                    # Chart Generation Logic
                    # Only show chart if:
                    # 1. User explicitly asked for it (visualization_type is set)
                    # 2. It's a TREND (inherently visual)
                    # 3. There is a grouping dimension (e.g., Sales by Region)
                    # Chart Generation Logic
                    explicit_viz = params.get("visualization_type")
                    grouping_present = bool(params.get("group_by"))
                    is_trend = (intent == "TREND")
                    
                    print(f"DEBUG CHART LOGIC: explicit_viz={explicit_viz}, is_trend={is_trend}, grouping_present={grouping_present} (raw: {params.get('group_by')})")
                    
                    if explicit_viz or is_trend or grouping_present:
                        # Safe fallback: if explicit_viz is None, use intent.lower()
                        chart_type = explicit_viz.lower() if explicit_viz else intent.lower()
                        chart_metadata = {"type": chart_type, "data": db_results}
                        print(f"DEBUG CHART_METADATA: type={chart_type}, rows={len(db_results)}")
                    else:
                        # Suppress chart for simple scalar aggregates (e.g. "Total Sales")
                        chart_metadata = None
                        print("DEBUG CHART: Suppressed (No grouping/explicit request)")

                    # SAFETY CHECK: Raw Transaction Data
                    # If we accidentally got raw rows (order_id) and user didn't explicitly ask for a list/table,
                    # we must block it from the LLM.
                    if db_results and isinstance(db_results, list) and len(db_results) > 0 and "order_id" in db_results[0]:
                         if intent != "LIST":
                             yield json.dumps({"type": "token", "chunk": "I cannot analyze raw transactional data directly. Please ask for an aggregation (e.g., 'Total Sales') or a specific list."}) + "\n"
                             return
                         else:
                             # If it IS a list, just return the table directly without LLM
                             # Use the utility to format it as a table
                             table_str = summarize_data(db_results)
                             yield json.dumps({"type": "token", "chunk": table_str}) + "\n"
                             yield json.dumps({"type": "chart", "content": chart_metadata}) + "\n"
                             return

                queries_duration = time.time() - db_start

                queries_duration = time.time() - db_start

            elif intent == "DOCUMENT":
                retr_start = time.time()
                docs = retrieval.retrieve(sanitized_query, top_k=3)
                
                if docs:
                    doc_text = "\n".join([f"- {d['content'][:300].replace(chr(10), ' ')}" for d in docs])
                    context_data += f"DOCUMENT INSIGHTS:\n{doc_text}\n\n"
            
            elif intent == "UNKNOWN":
                 # Fallback to general chat or simple acknowledgment
                 # For now, we can try RAG as a "Hail Mary" or just admit defeat nicely.
                 # User requested "Clear error message" -> implying safe failure.
                 yield json.dumps({"type": "token", "chunk": "I'm not sure I understand. Could you verify if you're asking about sales data, trends, or documentation?"}) + "\n"
                 return
            

            
            # 3. Generation Stream
            
            # Send Meta-data about charts/intent first
            meta_payload = {
                "type": "meta", 
                "intent": intent, 
                "scope": scope, 
                "chart": chart_metadata 
            }
            yield json.dumps(meta_payload) + "\n"

            # CRITICAL FIX: Frontend expects "chart" type, not just "meta"
            if chart_metadata:
                yield json.dumps({"type": "chart", "content": chart_metadata}) + "\n"

            # Context Trimming (Critical for Speed)
            MAX_CONTEXT_CHARS = 1200
            if len(context_data) > MAX_CONTEXT_CHARS:
                 context_data = context_data[:MAX_CONTEXT_CHARS] + "... (truncated)"

            if not context_data and intent != "CHAT":
                 yield json.dumps({"type": "token", "chunk": "I couldn't find any relevant data for your query."}) + "\n"
            else:
                 # Stream tokens
                 for chunk in generation.generate_response_stream(user_query, context_data, intent, history=request.history):
                     yield json.dumps({"type": "token", "chunk": chunk}) + "\n"

        except asyncio.CancelledError:
            print(f"Client disconnected. Stopping generation for query: {user_query[:20]}...")
            yield json.dumps({"type": "error", "content": "Generation stopped by user."}) + "\n"
            return
        except ValueError as ve:
            yield json.dumps({"type": "error", "content": str(ve)}) + "\n"
        except Exception as e:
            print(f"Error: {e}")
            yield json.dumps({"type": "error", "content": f"Internal Error: {str(e)}"}) + "\n"
        finally:
            print(f"Request processing finished (Title: {intent}). Duration: {time.time() - start_time:.2f}s")
            
    return StreamingResponse(event_generator(), media_type="application/x-ndjson")

@app.get("/health")
def health_check():
    return {"status": "active", "modules": ["database", "retrieval", "generation", "security", "analytics"]}

from .analytics import router as analytics_router, perform_root_cause_analysis
app.include_router(analytics_router)

# Include conversation history routers
app.include_router(auth_router)
app.include_router(conversations_router)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
