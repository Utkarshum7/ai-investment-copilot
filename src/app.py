from fastapi import FastAPI
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
import json
import asyncio
from typing import Dict, Any, List

from src.safety import check
from src.classifier import classify
from src.agents.portfolio_health import run as portfolio_health_run

app = FastAPI()


# ---- Request Schema (FIXES Swagger input issue) ----
class QueryRequest(BaseModel):
    query: str
    user: Dict[str, Any]
    session_id: str = "default"


# ---- simple in-memory session store ----
SESSIONS: dict[str, list[dict]] = {}


def get_history(session_id: str) -> list[dict]:
    return SESSIONS.setdefault(session_id, [])


def append_history(session_id: str, role: str, content: str):
    SESSIONS.setdefault(session_id, []).append({
        "role": role,
        "content": content
    })


# ---- router ----
def route_to_agent(intent: str, agent: str, user: Dict[str, Any], entities: dict):
    if agent == "portfolio_health":
        return portfolio_health_run(user)

    # stub for unimplemented agents (required by spec)
    return {
        "type": "not_implemented",
        "intent": intent,
        "agent": agent,
        "entities": entities,
        "message": f"{agent} agent is not implemented in this build.",
    }


# ---- streaming endpoint ----
@app.post("/query")
async def query(req: QueryRequest):

    async def event_generator():
        try:
            async with asyncio.timeout(6.0):
                body = req.model_dump() if hasattr(req, "model_dump") else req.dict()
                query_text = body.get("query", "") or ""
                user = body.get("user", {}) or {}
                session_id = body.get("session_id", "default") or "default"

                # 1) Safety (NO LLM)
                # Safety guard MUST run before classifier. Classifier MUST NOT execute if blocked.
                verdict = check(query_text)
                if verdict.blocked:
                    yield {
                        "event": "error",
                        "data": json.dumps({
                            "type": "safety_block",
                            "category": verdict.category,
                            "message": verdict.message,
                        }),
                    }
                    return

                # 2) Classifier
                history = get_history(session_id)
                try:
                    cls = classify(query_text, history=history[-2:], llm=None)  # mocked / rule-based
                except Exception:
                    from src.classifier import ClassificationResult
                    cls = ClassificationResult(agent="portfolio_health", intent="portfolio_health", entities={})

                append_history(session_id, "user", query_text)

                # 3) Route
                result = route_to_agent(cls.intent, cls.agent, user, cls.entities)

                # 4) Streaming response
                payload = {
                    "agent": cls.agent,
                    "entities": cls.entities,
                    "data": result,
                }

                text = json.dumps(payload)
                if not text:
                    return

                chunk_size = 120

                for i in range(0, len(text), chunk_size):
                    yield {
                        "event": "message",
                        "data": json.dumps({"chunk": text[i:i + chunk_size]}),
                    }
                    await asyncio.sleep(0.02)  # simulate streaming

                append_history(session_id, "assistant", text)

                yield {"event": "end", "data": ""}

        except asyncio.TimeoutError:
            yield {
                "event": "error",
                "data": json.dumps({
                    "type": "timeout",
                    "message": "Request exceeded time limit",
                }),
            }
        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({
                    "type": "internal_error",
                    "message": str(e),
                }),
            }

    return EventSourceResponse(event_generator())