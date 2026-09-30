from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel, EmailStr, Field


# ---- Auth ----
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class BootstrapRequest(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=8)


# ---- Department / Employee ----
class DepartmentCreate(BaseModel):
    name: str


class DepartmentOut(BaseModel):
    id: str
    name: str
    class Config:
        from_attributes = True


class EmployeeCreate(BaseModel):
    name: str
    email: EmailStr
    department_id: Optional[str] = None
    role: str = "employee"
    hourly_cost: float = Field(..., description="ASSUMPTION / configuration value used for ROI estimation")
    password: str


class EmployeeOut(BaseModel):
    id: str
    name: str
    email: str
    department_id: Optional[str]
    role: str
    hourly_cost: float
    class Config:
        from_attributes = True


# ---- Tasks ----
class TaskStartRequest(BaseModel):
    employee_id: str
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    baseline_minutes: Optional[float] = Field(None, description="ASSUMPTION: manual-effort estimate")


class TaskCompleteRequest(BaseModel):
    notes: Optional[str] = None


class TaskOut(BaseModel):
    id: str
    employee_id: str
    title: str
    description: Optional[str]
    category: Optional[str]
    baseline_minutes: Optional[float]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    actual_minutes: Optional[float]
    status: str
    class Config:
        from_attributes = True


# ---- Sessions ----
class SessionStartRequest(BaseModel):
    employee_id: str
    task_id: Optional[str] = None
    tool: str = "other"


class SessionOut(BaseModel):
    id: str
    employee_id: str
    task_id: Optional[str]
    tool: str
    started_at: datetime
    ended_at: Optional[datetime]
    duration_minutes: Optional[float]
    class Config:
        from_attributes = True


# ---- AI usage ----
class AIUsageEventRequest(BaseModel):
    employee_id: str
    provider: str
    model: Optional[str] = None
    session_id: Optional[str] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    source: str = Field("unavailable", description="connector | observed | imported | estimated | unavailable")
    metadata: Optional[dict[str, Any]] = None


class AIUsageOut(BaseModel):
    id: str
    provider: str
    model: Optional[str]
    input_tokens: Optional[int]
    output_tokens: Optional[int]
    total_tokens: Optional[int]
    cost: Optional[float]
    source: str
    class Config:
        from_attributes = True


# ---- Task outcome ----
class TaskOutcomeRequest(BaseModel):
    files_changed: int = 0
    lines_added: int = 0
    lines_removed: int = 0
    commits: int = 0
    tests_run: int = 0
    tests_passed: int = 0
    build_passed: Optional[bool] = None
    output_generated: bool = False


class TaskOutcomeOut(TaskOutcomeRequest):
    id: str
    task_id: str
    class Config:
        from_attributes = True


# ---- ROI ----
class ROIOut(BaseModel):
    task_id: str
    time_saved_minutes: Optional[float]
    time_saved_percentage: Optional[float]
    estimated_labor_value: Optional[float]
    ai_cost: Optional[float]
    net_value: Optional[float]
    roi_percentage: Optional[float]
    roi_multiple: Optional[float]
    calculation_status: str


# ---- Prompt intelligence ----
class PromptAnalyzeRequest(BaseModel):
    prompt: str


class PromptAnalyzeResponse(BaseModel):
    scores: dict[str, int]
    missing: list[str]
    suggestions: list[str]
    improved_prompt: str


class AgentOptimizeRequest(BaseModel):
    task_id: Optional[str] = None
    employee_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    task_type: Optional[str] = None
    complexity: Optional[str] = None
    required_quality: float = Field(80, ge=0, le=100)
    expected_input_tokens: Optional[int] = Field(None, ge=0)
    expected_output_tokens: Optional[int] = Field(None, ge=0)
    max_latency_ms: Optional[int] = Field(None, gt=0)
    verification_required: Optional[bool] = None


class AgentResultRequest(BaseModel):
    actual_input_tokens: Optional[int] = Field(None, ge=0)
    actual_output_tokens: Optional[int] = Field(None, ge=0)
    actual_cost: Optional[float] = Field(None, ge=0)
    actual_latency_ms: Optional[int] = Field(None, ge=0)
    actual_quality: Optional[float] = Field(None, ge=0, le=100)
    outcome: Optional[str] = None
    verification_required: Optional[bool] = None
    rework_required: Optional[bool] = None


class AgentDecisionOut(BaseModel):
    id: str
    task_id: Optional[str]
    task_type: str
    complexity: str
    required_quality: float
    selected_provider: str
    selected_model: str
    predicted_input_tokens: Optional[int]
    predicted_output_tokens: Optional[int]
    predicted_cost: Optional[float]
    predicted_latency_ms: Optional[int]
    predicted_quality: float
    confidence: float
    rationale: Optional[dict[str, Any]]
    actual_input_tokens: Optional[int]
    actual_output_tokens: Optional[int]
    actual_cost: Optional[float]
    actual_latency_ms: Optional[int]
    actual_quality: Optional[float]
    outcome: Optional[str]
    verification_required: Optional[bool]
    rework_required: Optional[bool]
    created_at: datetime

    class Config:
        from_attributes = True
