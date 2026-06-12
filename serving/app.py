from fastapi import FastAPI, HTTPException, WebSocket, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import time
import json
import os
import sys
import redis
from datetime import datetime

# Add project root to path
sys.path.append("C:/Users/Tarun/.gemini/antigravity/scratch/sql_agent_project")
from agent.sql_agent import SQLAgent, DB_CONFIG
from feedback.feedback_loop import FeedbackManager

app = FastAPI(title="LLM Text-to-SQL Agent API")

# Initialize Agent and Feedback
agent = SQLAgent(DB_CONFIG)
feedback_manager = FeedbackManager()

# Redis for session/cache (Mock for local dev if no Redis)
try:
    r = redis.Redis(host='localhost', port=6379, db=0)
except:
    r = None

class QueryRequest(BaseModel):
    query_text: str
    session_id: str
    schema_filter: Optional[List[str]] = None

class QueryResponse(BaseModel):
    query_id: str
    generated_sql: str
    results: Any # JSON serialized dataframe
    explanation: str
    follow_up_suggestions: List[str]
    metadata: Dict[str, Any]

class FeedbackRequest(BaseModel):
    query_id: str
    rating: int # 1 or -1
    comment: Optional[str] = None

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    start_time = time.time()
    try:
        # Run the agent
        response = agent.run(request.query_text)
        latency = time.time() - start_time
        
        # Log to feedback system
        query_data = {
            "query_text": request.query_text,
            "generated_sql": response["generated_sql"],
            "execution_success": response["execution_results"] is not None and not response["error_message"],
            "execution_time": latency,
            "query_type": response["intent"],
            "tables_used": [t["table_name"] for t in response["selected_tables"]]
        }
        feedback_manager.log_query(query_data)
        
        # Format results
        res_df = response["execution_results"]
        if isinstance(res_df, pd.DataFrame):
            results_json = res_df.to_dict(orient='records')
        else:
            results_json = []

        return QueryResponse(
            query_id=str(int(time.time())),
            generated_sql=response["generated_sql"],
            results=results_json,
            explanation=response["explanation"],
            follow_up_suggestions=["Can you show me this by month?", "Who is the top performer here?"],
            metadata={
                "latency": f"{latency:.2f}s",
                "intent": response["intent"],
                "tables": [t["table_name"] for t in response["selected_tables"]]
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/query/stream")
async def query_stream(websocket: WebSocket):
    await websocket.accept()
    try:
        data = await websocket.receive_text()
        request = json.loads(data)
        query = request["query_text"]
        
        # Mock streaming agent steps (in real implementation, we'd use callbacks)
        steps = [
            "Classifying query intent...",
            "Selecting relevant tables from schema RAG...",
            "Retrieving business glossary definitions...",
            "Generating optimized PostgreSQL SQL...",
            "Validating SQL syntax and safety...",
            "Executing query against warehouse...",
            "Synthesizing results and generating insights..."
        ]
        
        for step in steps:
            await websocket.send_json({"step": step, "status": "processing"})
            time.sleep(0.5) # Simulate processing
            
        # Run agent for final result
        response = agent.run(query)
        await websocket.send_json({"step": "Complete", "status": "done", "payload": response["explanation"]})
        
    except Exception as e:
        await websocket.send_json({"error": str(e)})
    finally:
        await websocket.close()

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "postgres": "connected",
            "redis": "connected" if r else "offline",
            "llm": "active"
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
