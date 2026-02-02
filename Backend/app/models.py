from pydantic import BaseModel
from typing import List, Optional, Any

class QueryRequest(BaseModel):
    query: str
    history: Optional[List[dict]] = []

class QueryResponse(BaseModel):
    reply: str
    intent: str
    scope: Optional[str]
    context_used: Any
    backend_module: str
    follow_up_questions: List[str] = []
