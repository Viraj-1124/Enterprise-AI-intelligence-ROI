from fastapi import APIRouter, Depends

from app.schemas.schemas import PromptAnalyzeRequest, PromptAnalyzeResponse
from app.services.prompt_analyzer import analyze_prompt
from app.services.auth import get_current_employee

router = APIRouter(prefix="/api/prompt", tags=["prompt-intelligence"])


@router.post("/analyze", response_model=PromptAnalyzeResponse)
def analyze(req: PromptAnalyzeRequest, _employee=Depends(get_current_employee)):
    result = analyze_prompt(req.prompt)
    return PromptAnalyzeResponse(**result)
