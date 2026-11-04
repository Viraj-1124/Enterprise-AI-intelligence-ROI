from pathlib import Path
import re

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.agent_eval.runner import EvalRunner, history
from app.agent_eval.suites import load_suite

router = APIRouter(prefix="/v1/agent-eval", tags=["agent-evaluation"])
SUITES_DIR = Path("config/suites")


class AgentEvalRequest(BaseModel):
    suite_id: str = Field(pattern=r"^[a-z0-9_-]+$")
    agent_version: str = "demo-v1"


@router.get("/suites")
async def list_suites() -> list[dict[str, object]]:
    output = []
    for path in sorted(SUITES_DIR.glob("*.yaml")):
        suite = load_suite(path)
        output.append({"id": path.stem, "name": suite["name"], "description": suite.get("description", ""), "case_count": len(suite["cases"]), "type": suite.get("type", "standard")})
    return output


@router.get("/runs")
async def list_runs() -> list[dict[str, object]]:
    return history()


@router.post("/run")
async def run_suite(body: AgentEvalRequest) -> dict[str, object]:
    if not re.fullmatch(r"[a-z0-9_-]+", body.suite_id):
        raise HTTPException(status_code=422, detail="Invalid suite id")
    path = SUITES_DIR / f"{body.suite_id}.yaml"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Evaluation suite not found")
    suite = load_suite(path)
    return await EvalRunner().run(suite, body.agent_version)
