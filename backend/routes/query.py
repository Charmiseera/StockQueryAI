"""
routes/query.py — The AI query endpoint.

Orchestrates the LLM agentic loop. Separated from auth and inventory concerns.
Rate limited to prevent LLM API abuse.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address

from auth.dependencies import CurrentUser
from ai.agent import run_query, QueryResponse

log = logging.getLogger(__name__)
router = APIRouter(prefix="/query", tags=["query"])
limiter = Limiter(key_func=get_remote_address)


class QueryRequest(BaseModel):
    question: str


@router.post("", response_model=QueryResponse)
@limiter.limit("30/minute")
async def query_inventory(
    request: Request,
    body: QueryRequest,
    current_user: CurrentUser,
):
    """
    Natural language inventory query endpoint.
    Rate limited to 30 requests/minute per IP.
    The agentic loop runs entirely through MCP tools — user_id is passed
    as a scoping parameter so every tool filters data correctly.
    """
    question = body.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        return await run_query(question=question, current_user=current_user)
    except Exception as e:
        err = str(e)
        log.error(f"[QUERY] Failed for user_id={current_user['id']}: {err}", exc_info=True)
        if "401" in err or "Unauthorized" in err:
            raise HTTPException(status_code=503, detail="AI service authentication failed. Check NEBIUS_API_KEY.")
        if "429" in err:
            raise HTTPException(status_code=429, detail="AI service rate limit reached. Please wait and retry.")
        raise HTTPException(status_code=500, detail="Query failed. Please try again.")
