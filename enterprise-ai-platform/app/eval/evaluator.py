from datetime import datetime, timezone
from pathlib import Path

import yaml

from app.core.schemas import EvaluationRun
from app.eval.scorer import score_output


class Evaluator:
    def __init__(self, path: str | Path = "config/eval_tasks.yaml") -> None:
        self.tasks = yaml.safe_load(Path(path).read_text(encoding="utf-8"))["tasks"]

    async def run(self) -> EvaluationRun:
        scores = {
            t["id"]: score_output(f"Processed: {t['input']}", t["expected"]) for t in self.tasks
        }
        return EvaluationRun(
            mode="benchmark",
            completed_at=datetime.now(timezone.utc),
            results={"scores": scores, "accuracy": sum(scores.values()) / max(1, len(scores))},
        )
