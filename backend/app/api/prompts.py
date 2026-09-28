from fastapi import APIRouter

from app.schemas.schemas import PromptAnalyzeRequest, PromptAnalyzeResponse
from app.services.prompt_analyzer import analyze_prompt

router = APIRouter(prefix="/api/prompt", tags=["prompt-intelligence"])


@router.post("/analyze", response_model=PromptAnalyzeResponse)
def analyze(req: PromptAnalyzeRequest):
    result = analyze_prompt(req.prompt)
    return PromptAnalyzeResponse(**result)
