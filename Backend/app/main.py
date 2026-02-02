from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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

# Initialize FastAPI
app = FastAPI(title="Modular AI Analytics Backend")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    extractor = QueryExtractor() # New Python-based extractor
    print("All modules initialized successfully.")
except Exception as e:
    print(f"Startup Error: {e}")

from .utils import summarize_data
import time

# ... (Imports)

@app.post("/query") # Removed response_model since it's a stream
async def process_query(request: QueryRequest):
    async def event_generator():
        start_time = time.time()
        user_query = request.query
        
        try:
            # 1. Agentic Decision Making
            # The agent decides WHAT to do (Intent, Data Functions, RAG)
            agent_decision = extractor.decide_action(user_query)
            
            intent = agent_decision["intent"]
            analysis_type = agent_decision["analysis_type"]
            data_fns = agent_decision["data_functions"]
            use_docs = agent_decision["use_documents"]
            
            # Debug: Stream decision to frontend (optional, hidden by default but useful)
            # yield json.dumps({"type": "debug", "decision": agent_decision}) + "\n"

            context_data = ""
            chart_metadata = None
            db_results = []

            # 2. Execution Loop: Run Prescribed Data Functions
            for task in data_fns:
                fn_name = task["name"]
                fn_params = task["parameters"]
                
                # Dynamic dispatch to database manager
                if hasattr(database, fn_name):
                    method = getattr(database, fn_name)
                    result = method(**fn_params)
                    
                    if result:
                        if isinstance(result, list):
                            db_results.extend(result)
                        elif isinstance(result, dict) and "error" not in result:
                            db_results.append(result)
                            
                        # Format for Context
                        # (Simple JSON dump or tailored summary)
                        from .utils import summarize_data
                        summary = summarize_data(result)
                        context_data += f"DATA INSIGHT ({fn_name}):\n{summary}\n\n"
                        
                        # Set chart data (taking the first valid one for now)
                        if not chart_metadata:
                            chart_metadata = {"type": analysis_type, "data": result}
                
                elif fn_name == "perform_root_cause_analysis":
                    # Special Case: Analytics Module
                    rca_result = perform_root_cause_analysis(**fn_params)
                    if "summary" in rca_result:
                        context_data += f"DIAGNOSTIC ANALYSIS:\n{rca_result['summary']}\nTop Drivers:\n{rca_result.get('factors', [])}\n\n"
                        chart_metadata = {"type": "rca", "data": rca_result.get('factors', [])}

            # 3. RAG / Document Retrieval (if Agents requested it)
            if use_docs:
                sanitized_query = agent_decision["debug_info"]["sanitized_query"]
                docs = retrieval.retrieve(sanitized_query, top_k=2) # Keep it focused
                if docs:
                     doc_text = "\n".join([f"- {d['content'][:300].replace(chr(10), ' ')}" for d in docs])
                     context_data += f"DOCUMENT KNOWLEDGE:\n{doc_text}\n\n"

            # 4. Strict Generation
            # Meta-data first
            scope = agent_decision["debug_info"]["extracted_filters"].get("region", "Global")
            meta_payload = {
                "type": "meta", 
                "intent": intent, 
                "scope": scope, 
                "chart": chart_metadata 
            }
            yield json.dumps(meta_payload) + "\n"

            # Short Circuit if Empty
            if not context_data.strip() and intent != "RAG": # RAG might answer without DB data
                 yield json.dumps({"type": "token", "chunk": "I don’t see sufficient data to answer this question."}) + "\n"
            else:
                 # Stream Response
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

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
