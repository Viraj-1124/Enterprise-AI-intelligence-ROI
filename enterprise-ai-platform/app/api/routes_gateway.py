from pathlib import Path

import yaml
from fastapi import APIRouter, Depends, Header, HTTPException

from app.api.deps import get_registry, get_router, get_store
from app.core.enums import RequestStatus, TaskCategory
from app.core.errors import EdgeUnavailable
from app.core.schemas import MetricRecord, Node, Plan, Request, RequestResponse, Trace
from app.edge.edge_router import EdgeRouter
from app.execution.dag_scheduler import DAGScheduler
from app.execution.task_executor import TaskExecutor
from app.routing.jev_mock import JevHTTPBackend, JevMockBackend
from app.routing.rule_engine import RuleEngine
from app.settings import get_settings

router = APIRouter()
REQUESTS: dict[str, RequestResponse] = {}


@router.post("/v1/request", response_model=RequestResponse)
async def submit_request(
    body: Request,
    x_api_key: str | None = Header(default=None),
    routing=Depends(get_router),  # noqa: B008
    registry=Depends(get_registry),  # noqa: B008
    store=Depends(get_store),  # noqa: B008
) -> RequestResponse:
    if x_api_key != get_settings().api_key:
        raise HTTPException(status_code=401, detail="invalid API key")
    rule_field = (
        "email" if body.task_category == TaskCategory.EXTRACTION and "@" in body.input else None
    )
    settings = get_settings()
    jev = JevHTTPBackend(settings.jev_base_url) if settings.jev_base_url else JevMockBackend()
    jev_decisions: dict[str, dict[str, object]] = {}
    jev_error: str | None = None
    routing_path = "strategy"
    if jev.applies_to(body.task_category.value):
        schema_data = yaml.safe_load(Path("config/jev_schemas.yaml").read_text(encoding="utf-8"))
        questions = {
            key: choices for schema in schema_data.values() for key, choices in schema.items()
        }
        try:
            jev_decisions = await jev.decide(body.input, questions)
        except Exception as error:  # noqa: BLE001 - Jev errors fall back to ordinary routing.
            jev_error = str(error)
        map_config = yaml.safe_load(Path("config/router.yaml").read_text(encoding="utf-8"))
        rule_result = None
        for condition, destination in map_config.get("jev_routing_map", {}).items():
            key, expected = condition.split("=", maxsplit=1)
            if jev_decisions.get(key, {}).get("choice") != expected:
                continue
            if destination == "rule:billing_handler":
                rule_result = RuleEngine.billing_handler()
                routing_path = f"jev_map:{condition} -> {destination}"
                break
            if destination.startswith("tier:"):
                tier = destination.partition(":")[2]
                available = registry.candidates(get_settings().model_provider.lower())
                chosen = next((model for model in available if model.tier == tier), None)
                if chosen:
                    routing_path = f"jev_map:{condition} -> {destination}"
                    break
        else:
            rule_result = None
    else:
        rule_result = None
    if routing_path == "strategy":
        rule_result = RuleEngine().handle(body.task_category.value, body.input, rule_field)
        if jev_error:
            routing_path = "jev_error -> strategy_fallback"
        elif jev_decisions:
            routing_path = "jev_no_match -> strategy"
        else:
            routing_path = "rule" if rule_result is not None else "strategy"
    if rule_result is not None:
        trace = Trace(
            request_id=body.request_id,
            jev_decisions=jev_decisions,
            jev_error=jev_error,
            routing_path=routing_path,
            events=[
                {"route": "rule", "result": rule_result},
                {"jev_decisions": jev_decisions},
                {"routing_path": routing_path},
                *([{"jev_error": jev_error}] if jev_error else []),
            ],
        )
        result = rule_result
    else:
        supplied_nodes = body.metadata.get("subtasks")
        if supplied_nodes:
            plan = Plan(nodes=[Node.model_validate(item) for item in supplied_nodes])
        else:
            plan = Plan(
                nodes=[
                    Node(
                        node_id="main",
                        task=body.input,
                        input=body.input,
                        task_category=body.task_category,
                    )
                ]
            )
        decisions = {}
        tier_override = None
        if routing_path.startswith("jev_map:") and "tier:" in routing_path:
            tier_override = routing_path.rsplit("tier:", maxsplit=1)[1]
        for node in plan.nodes:
            node_request = body.model_copy(
                update={"input": node.input or node.task, "task_category": node.task_category}
            )
            decision = routing.route(node_request)
            selected = (
                next(
                    (
                        model
                        for model in registry.candidates(get_settings().model_provider.lower())
                        if model.tier == tier_override
                    ),
                    None,
                )
                if tier_override
                else None
            )
            node.model_id = node.model_id or (selected.id if selected else decision.model_id)
            node.precision = node.precision or decision.precision
            local_models = registry.candidates("ollama")
            local_model = local_models[0] if local_models and registry.provider_ready else None
            placement = EdgeRouter().place(body, node, local_model)
            node.is_edge = placement.target == "edge"
            node.edge_rationale = placement.rationale
            node.escalation_reason = placement.escalation_reason
            if placement.target == "edge":
                node.model_id = local_model.id
                if node.precision not in local_model.precisions:
                    node.precision = local_model.precisions[0]
            elif placement.escalation_reason and get_settings().model_provider.lower() == "ollama":
                raise EdgeUnavailable(
                    "strict reasoning or generation requires a cloud provider, but only Ollama is configured"
                )
            decisions[node.node_id] = {
                "model_id": node.model_id,
                "strategy": decision.strategy,
                "precision": node.precision.value,
                "placement": placement.target,
                "placement_rationale": placement.rationale,
            }
        trace = await DAGScheduler(TaskExecutor(registry)).schedule(plan, body.request_id)
        trace.jev_decisions = jev_decisions
        trace.jev_error = jev_error
        trace.routing_path = routing_path
        trace.events.extend(
            [
                {"routes": decisions},
                {"jev_decisions": jev_decisions},
                {"routing_path": routing_path},
                *([{"jev_error": jev_error}] if jev_error else []),
            ]
        )
        result = (
            trace.nodes[0].output
            if len(trace.nodes) == 1
            else {
                node.node_id: next(
                    (r.output for r in trace.nodes if r.node_id == node.node_id), None
                )
                for node in plan.nodes
            }
        )
    metric = MetricRecord(
        request_id=body.request_id,
        user_id=body.user_id,
        task_category=body.task_category,
        strategy_used=body.strategy or get_settings().default_strategy,
        nodes=[n.model_dump(mode="json") for n in trace.nodes],
        input_tokens=sum(n.input_tokens for n in trace.nodes),
        output_tokens=sum(n.output_tokens for n in trace.nodes),
        cost_usd=sum(n.cost_usd for n in trace.nodes),
        latency_ms=sum(n.latency_ms for n in trace.nodes),
        critical_path_latency_ms=trace.critical_path_latency_ms,
        parallel_efficiency=trace.parallel_efficiency,
        retry_count=trace.retry_count,
        escalation_count=trace.escalation_count,
        jev_decision_count=len(jev_decisions),
        jev_decisions_covered=len(jev_decisions),
        quantization_accuracy_delta={
            node.model_id: registry.get(node.model_id).quant_accuracy_delta.get(
                body.task_category.value, 0.0
            )
            for node in trace.nodes
        },
        successful=True,
    )
    store.write(metric)
    response = RequestResponse(
        request_id=body.request_id, status=RequestStatus.SUCCEEDED, result=result, trace=trace
    )
    REQUESTS[body.request_id] = response
    return response


@router.get("/v1/request/{request_id}", response_model=RequestResponse)
async def request_status(request_id: str) -> RequestResponse:
    if request_id not in REQUESTS:
        raise HTTPException(status_code=404, detail="request not found")
    return REQUESTS[request_id]
