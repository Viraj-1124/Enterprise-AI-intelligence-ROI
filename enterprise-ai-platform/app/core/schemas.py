from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import PrecisionTier, RequestStatus, TaskCategory


class Request(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str = "demo"
    input: str
    task_category: TaskCategory = TaskCategory.GENERATION
    privacy: str = "standard"
    strategy: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Node(BaseModel):
    node_id: str
    task: str
    task_category: TaskCategory
    depends_on: list[str] = Field(default_factory=list)
    required_fields: list[str] = Field(default_factory=list)
    input: str | None = None
    model_id: str | None = None
    precision: PrecisionTier | None = None
    status: str = "pending"
    is_edge: bool = False
    edge_rationale: str | None = None
    escalation_reason: str | None = None


class Plan(BaseModel):
    nodes: list[Node]


class NodeResult(BaseModel):
    node_id: str
    output: Any
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0
    latency_ms: float = 0
    model_id: str = ""
    provider: str = "mock"
    tier: str = "small"
    is_edge: bool = False
    critical_path_member: bool = False
    precision: PrecisionTier = PrecisionTier.FP8
    attempts: int = 1
    escalation_count: int = 0
    escalated: bool = False
    escalated_from: str | None = None
    escalation_reason: str | None = None
    edge_rationale: str | None = None
    precision_requested: str = "unknown"
    precision_verified: bool = False
    observed_model_artifact: str | None = None
    precision_note: str | None = None
    attempt_trace: list[str] = Field(default_factory=list)
    final_status: str = "succeeded"


class Trace(BaseModel):
    request_id: str
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    events: list[dict[str, Any]] = Field(default_factory=list)
    nodes: list[NodeResult] = Field(default_factory=list)
    critical_path_latency_ms: float = 0
    critical_path_length: int = 0
    parallel_efficiency: float = 0
    retry_count: int = 0
    escalation_count: int = 0
    jev_decisions: dict[str, dict[str, Any]] = Field(default_factory=dict)
    jev_error: str | None = None
    routing_path: str | None = None


class ModelSpec(BaseModel):
    id: str
    display_name: str | None = None
    provider: str = "mock"
    actual_precision: str = "unknown"
    tier: str
    precisions: list[PrecisionTier]
    cost_per_1k_in: float = 0
    cost_per_1k_out: float = 0
    capability_tags: list[str] = Field(default_factory=list)
    quant_accuracy_delta: dict[str, float] = Field(default_factory=dict)
    context_window: int = 8192
    quality: float = 0.9


class RoutingDecision(BaseModel):
    model_id: str
    precision: PrecisionTier
    strategy: str
    rationale: str
    confidence: float = 1.0


class ValidationResult(BaseModel):
    valid: bool
    errors: list[str] = Field(default_factory=list)


class MetricRecord(BaseModel):
    request_id: str
    user_id: str = "demo"
    task_category: TaskCategory
    complexity_score: int = 1
    strategy_used: str = "cost_quality"
    nodes: list[dict[str, Any]] = Field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0
    latency_ms: float = 0
    parallel_efficiency: float = 0
    critical_path_latency_ms: float = 0
    retry_count: int = 0
    escalation_count: int = 0
    jev_decision_count: int = 0
    jev_decisions_covered: int = 0
    successful: bool = True
    quantization_accuracy_delta: dict[str, float] = Field(default_factory=dict)
    harness_config_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EvaluationRun(BaseModel):
    run_id: str = Field(default_factory=lambda: str(uuid4()))
    mode: str = "benchmark"
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None
    results: dict[str, Any] = Field(default_factory=dict)


class HarnessConfig(BaseModel):
    config_id: str = Field(default_factory=lambda: str(uuid4()))
    prompt_style: str = "concise"
    memory_policy: str = "parents_only"
    tool_choices: list[str] = Field(default_factory=list)
    max_iters: int = 1
    score: float = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class HarnessResult(BaseModel):
    configs_evaluated: int
    scores_per_config: list[dict[str, Any]]
    chosen_config: dict[str, Any]
    improvement_over_baseline: float
    total_cost_usd: float
    total_latency_ms: float


class RequestResponse(BaseModel):
    request_id: str
    status: RequestStatus
    result: Any = None
    trace: Trace | None = None
