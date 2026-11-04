import time

from app.core.errors import OllamaUnreachable
from app.core.schemas import Node, NodeResult
from app.providers.registry import ModelRegistry
from app.validation.escalation import EscalationManager
from app.validation.retry_manager import RetryManager
from app.validation.validators import SchemaValidator


class TaskExecutor:
    def __init__(self, registry: ModelRegistry, retry_manager: RetryManager | None = None) -> None:
        self.registry = registry
        if retry_manager is None:
            from app.settings import get_settings

            settings = get_settings()
            retry_manager = RetryManager(
                settings.max_retries_per_node, settings.max_retries_per_request
            )
        self.retry_manager = retry_manager
        self.validator = SchemaValidator()
        self.escalation = EscalationManager()

    async def execute(self, node: Node, context: dict[str, str]) -> NodeResult:
        spec = self.registry.get(node.model_id or "mock-small-fp8")
        user_input = node.input or node.task
        prompt = f"Task: {node.task.strip()}\nUser input: {user_input.strip()}"
        if context:
            prompt += "\nParent outputs: " + str(context)
        precision = node.precision or spec.precisions[0]
        attempts = 0
        escalation_count = 0
        escalated_from: str | None = None
        attempt_trace: list[str] = []
        while True:
            attempts += 1
            adapter = self.registry.adapter(spec.id)
            actual_provider = getattr(adapter, "provider", spec.provider)
            start = time.perf_counter()
            try:
                output = await adapter.generate(
                    prompt,
                    precision,
                    category=node.task_category.value,
                    node_id=node.node_id,
                    task=node.task,
                    user_input=user_input,
                    parent_outputs=context,
                )
                latency = (time.perf_counter() - start) * 1000
                validation = self.validator.validate(
                    node.task_category.value, output, node.required_fields
                )
                if not validation.valid:
                    raise ValueError("; ".join(validation.errors))
                precision_verified = False
                precision_note = None
                observed_artifact = None
                if actual_provider == "ollama" and spec.actual_precision != "unknown":
                    observed_artifact = spec.actual_precision
                    precision_verified = spec.actual_precision.lower() == precision.value.lower()
                    if not precision_verified:
                        precision_note = (
                            f"requested {precision.value}; observed {spec.actual_precision}"
                        )
                elif actual_provider == "mock":
                    precision_note = "mock adapter — precision is a routing label only"
                else:
                    precision_note = "adapter does not expose precision; treat as unverified"
                attempt_trace.append(f"{attempts}:{spec.id}:{precision.value}:validated")
                in_tokens, out_tokens = max(1, len(prompt.split())), max(1, len(output.split()))
                cost = (in_tokens * spec.cost_per_1k_in + out_tokens * spec.cost_per_1k_out) / 1000
                return NodeResult(
                    node_id=node.node_id,
                    output=output,
                    input_tokens=in_tokens,
                    output_tokens=out_tokens,
                    cost_usd=cost,
                    latency_ms=latency,
                    model_id=spec.id,
                    provider=actual_provider,
                    tier=spec.tier,
                    is_edge=node.is_edge or actual_provider == "ollama",
                    edge_rationale=node.edge_rationale,
                    escalation_reason=node.escalation_reason,
                    precision=precision,
                    precision_requested=precision.value,
                    precision_verified=precision_verified,
                    observed_model_artifact=observed_artifact,
                    precision_note=precision_note,
                    attempts=attempts,
                    escalation_count=escalation_count,
                    escalated=escalation_count > 0,
                    escalated_from=escalated_from,
                    attempt_trace=attempt_trace,
                )
            except Exception as error:
                attempt_trace.append(f"{attempts}:{spec.id}:{precision.value}:failed:{error}")
                if isinstance(error, OllamaUnreachable):
                    raise
                if self.retry_manager.consume(node.node_id):
                    continue
                from app.settings import get_settings

                next_model = self.escalation.next_model(
                    spec,
                    self.registry.candidates(get_settings().model_provider.lower()),
                    node.task_category.value,
                )
                if next_model is None:
                    raise
                escalation_count += 1
                escalated_from = spec.id
                spec, precision = next_model, next_model.precisions[0]
