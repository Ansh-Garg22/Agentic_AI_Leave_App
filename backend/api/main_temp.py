from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import json
import os

load_dotenv()

from agent.agentic_core import setup_agent
from api.tools import read_json_db, USERS_DB_PATH

app = FastAPI(
    title="Agentic Leave Management API",
    description="A single-endpoint API that uses a LangChain agent to handle leave management tasks.",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "null"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent_executor = setup_agent()

class LoginRequest(BaseModel):
    user_id: str

class AgentRequest(BaseModel):
    user_id: str
    query: str


@app.get("/")
def read_root():
    return {"message": "Welcome to the Agentic Leave Management API v3."}

@app.post("/login")
async def login(request: LoginRequest):
    
    users = read_json_db(USERS_DB_PATH)
    for user in users:
        if user['user_id'] == request.user_id:
            return {"success": True, "user": {"id": user['user_id'], "name": user['name']}}
    raise HTTPException(status_code=404, detail="User ID not found")


@app.post("/agent/invoke")
async def agent_invoke(request: AgentRequest):
    
    print(f"Invoking agent for User '{request.user_id}' with query: '{request.query}'")

    try:
        response = await agent_executor.ainvoke({"user_id": request.user_id, "query": request.query}) # Direct mapping
        
        output = response.get('output')
        
        if output is None:
            raise HTTPException(status_code=500, detail="Agent returned an empty or invalid response.")

        return output

    except Exception as e:
        print(f"An error occurred while invoking the agent: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred in the agent: {str(e)}")
    

    