import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.schemas import HarnessResult
from app.eval.scorer import score_output
from app.providers.registry import ModelRegistry
from app.settings import get_settings


class HarnessOptimizer:
    def __init__(self, output_path: str | Path = "config/harness/best.json") -> None:
        self.output_path = Path(output_path)
        self.history_path = self.output_path.with_name("history.jsonl")

    async def optimize(
        self,
        task_set: list[dict[str, str]],
        base_config: dict[str, Any] | None = None,
        candidates: list[dict[str, Any]] | None = None,
        budget_per_task: int = 1,
    ) -> HarnessResult:
        if candidates is None:
            base = base_config or {"prompt_style": "baseline", "memory_policy": "parents_only"}
            candidates = [
                dict(base),
                {**base, "prompt_style": "concise"},
                {**base, "prompt_style": "few_shot"},
            ]
        if len(candidates) < 2:
            raise ValueError("Harness optimizer requires at least two candidate configs")
        if budget_per_task < 1:
            raise ValueError("budget_per_task must be at least one")

        settings = get_settings()
        registry = ModelRegistry()
        evaluations: list[dict[str, Any]] = []
        traces: dict[str, tuple[float, float]] = {}
        for index, candidate in enumerate(candidates):
            config = {"prompt_style": "baseline", "memory_policy": "parents_only", **candidate}
            scores: list[float] = []
            cost_total = latency_total = 0.0
            for task in task_set:
                category = task.get("category", "generation")
                model = next(
                    (
                        item
                        for item in registry.candidates(settings.model_provider.lower())
                        if category in item.capability_tags
                    ),
                    None,
                )
                if model is None:
                    raise ValueError(f"No {settings.model_provider} model supports {category}")
                prompt = self._prompt(config, task)
                for _ in range(budget_per_task):
                    start = time.perf_counter()
                    output = await registry.adapter(model.id).generate(
                        prompt, model.precisions[0], category=category
                    )
                    latency_ms = (time.perf_counter() - start) * 1000
                    in_tokens = max(1, len(prompt.split()))
                    out_tokens = max(1, len(output.split()))
                    cost = (
                        in_tokens * model.cost_per_1k_in + out_tokens * model.cost_per_1k_out
                    ) / 1000
                    cost_total += cost
                    latency_total += latency_ms
                    scores.append(score_output(output, task["expected"]))
            mean_score = sum(scores) / max(1, len(scores))
            config_id = str(config.get("config_id") or f"candidate-{index + 1}")
            evaluations.append(
                {
                    "config_id": config_id,
                    "config": config,
                    "mean_score": mean_score,
                    "rollouts": len(scores),
                    "cost_usd": cost_total,
                    "latency_ms": latency_total,
                }
            )
            traces[config_id] = (cost_total, latency_total)

        winner = max(evaluations, key=lambda row: (row["mean_score"], -row["cost_usd"]))
        baseline = evaluations[0]
        result = HarnessResult(
            configs_evaluated=len(evaluations),
            scores_per_config=evaluations,
            chosen_config=winner["config"],
            improvement_over_baseline=winner["mean_score"] - baseline["mean_score"],
            total_cost_usd=sum(row["cost_usd"] for row in evaluations),
            total_latency_ms=sum(row["latency_ms"] for row in evaluations),
        )
        persisted = result.model_dump(mode="json")
        persisted["completed_at"] = datetime.now(timezone.utc).isoformat()
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_path.write_text(json.dumps(persisted, indent=2), encoding="utf-8")
        with self.history_path.open("a", encoding="utf-8") as history:
            history.write(json.dumps(persisted) + "\n")
        return result

    @staticmethod
    def _prompt(config: dict[str, Any], task: dict[str, str]) -> str:
        style = config.get("prompt_style", "baseline")
        prefix = {
            "concise": "Respond concisely. ",
            "few_shot": "Use the supplied examples. ",
            "explicit": "Follow the task requirements. ",
        }.get(style, "")
        return prefix + task["input"]
