"""
FastAPI application for T3 Governed Agent Cloud Run service.
"""

import os
from contextlib import asynccontextmanager

from agent import GovernedAgent, create_agent
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

agent_instance: GovernedAgent | None = None


def get_agent() -> GovernedAgent:
    global agent_instance
    if agent_instance is None:
        agent_instance = create_agent()
    return agent_instance


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_agent()
    yield


app = FastAPI(
    title="T3 Governed Cloud Run Agent",
    version="2.0.0",
    lifespan=lifespan,
)


class QueryRequest(BaseModel):
    prompt: str = Field(
        ..., min_length=1, max_length=2000, description="Query prompt for the agent"
    )


class QueryResponse(BaseModel):
    status: str
    response: str
    model: str
    runtime: str


@app.get("/health")
@app.get("/healthz")
async def healthz():
    """Liveness/readiness health check probe."""
    return {
        "status": "healthy",
        "service": "t3-cloud-run-agent",
        "deployment_id": os.getenv("DEPLOYMENT_ID", "local"),
        "model": os.getenv("AGENT_MODEL_NAME", "gemini-2.5-flash"),
    }


@app.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest):
    """Execute governed agent reasoning query."""
    agent = get_agent()
    result = agent.query(req.prompt)
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message", "Agent query error"))

    return QueryResponse(
        status=result["status"],
        response=result["response"],
        model=result["model"],
        runtime=result.get("runtime", "cloud-run"),
    )
