"""Deterministic, history-aware agent routing recommendations."""
import re

from sqlalchemy.orm import Session

from app.models.models import AgentDecision

# Price units are USD per million tokens, based on public provider pricing in
# September 2026 (Google: ai.google.dev/gemini-api/docs/pricing; OpenAI:
# developers.openai.com/api/docs/pricing; Anthropic: anthropic.com/news/claude-sonnet-5
# and official Claude model pricing PDF). Refresh before production use.
# Quality and latency are conservative capability priors, not guarantees.
AGENTS = [
    {"provider": "google", "model": "gemini-3.1-flash-lite", "quality": 76, "input": 0.25, "output": 1.50, "latency": 900},
    {"provider": "openai", "model": "gpt-4o-mini", "quality": 84, "input": 0.15, "output": 0.60, "latency": 1300},
    {"provider": "anthropic", "model": "claude-haiku-4-5", "quality": 85, "input": 1.00, "output": 5.00, "latency": 1400},
    {"provider": "openai", "model": "gpt-4o", "quality": 94, "input": 2.50, "output": 10.00, "latency": 2400},
    {"provider": "anthropic", "model": "claude-sonnet-5", "quality": 96, "input": 2.00, "output": 10.00, "latency": 3000},
]


def model_pricing(provider: str, model: str | None) -> dict | None:
    match = next((a for a in AGENTS if a["provider"] == provider and a["model"] == model), None)
    return {"input": match["input"], "output": match["output"]} if match else None


def _task_type(req) -> str:
    if req.task_type:
        return req.task_type.strip().lower()
    text = f"{req.title} {req.description or ''}".lower()
    for category, terms in {
        "coding": ("code", "implement", "bug", "api", "function", "refactor", "endpoint"),
        "analysis": ("analyze", "analysis", "compare", "research", "evaluate"),
        "writing": ("write", "draft", "summarize", "email", "document"),
    }.items():
        if any(term in text for term in terms):
            return category
    return (req.category or "general").strip().lower() if hasattr(req, "category") else "general"


def recommend(db: Session, req) -> tuple[dict, dict]:
    task_type = _task_type(req)
    text = f"{req.title} {req.description or ''}"
    complexity = (req.complexity or ("high" if len(text.split()) > 100 or re.search(r"\b(architecture|security|migration|distributed|critical)\b", text, re.I) else "medium" if len(text.split()) > 25 else "low")).lower()
    if complexity not in {"low", "medium", "high"}:
        complexity = "medium"
    min_quality = max(req.required_quality, {"low": 65, "medium": 75, "high": 88}[complexity])
    in_tokens = req.expected_input_tokens if req.expected_input_tokens is not None else max(100, len(text.split()) * 2)
    out_tokens = req.expected_output_tokens if req.expected_output_tokens is not None else {"low": 300, "medium": 700, "high": 1400}[complexity]
    verification = req.verification_required if req.verification_required is not None else complexity == "high" or task_type in {"coding", "analysis"} and min_quality >= 90

    history = db.query(AgentDecision).filter(AgentDecision.outcome.isnot(None)).all()
    scored = []
    for profile in AGENTS:
        rows = [r for r in history if r.selected_provider == profile["provider"] and r.selected_model == profile["model"] and r.task_type == task_type and r.verification_required == verification]
        reliability = (sum(1 for r in rows if (r.actual_quality or 0) >= r.required_quality and r.outcome.lower() in {"success", "completed", "passed"} and not r.rework_required) + 2) / (len(rows) + 3)
        empirical_quality = sum(r.actual_quality for r in rows if r.actual_quality is not None) / max(1, sum(r.actual_quality is not None for r in rows))
        quality = min(profile["quality"], (profile["quality"] * 0.75 + empirical_quality * 0.25)) if empirical_quality else profile["quality"]
        if quality < min_quality or reliability < 0.5 or req.max_latency_ms and profile["latency"] > req.max_latency_ms:
            continue
        cost = (in_tokens * profile["input"] + out_tokens * profile["output"]) / 1_000_000
        scored.append((cost, in_tokens + out_tokens, profile["latency"], profile, quality, reliability, len(rows)))
    if not scored:
        # If no model satisfies hard constraints, choose highest capability and be explicit.
        profile = max(AGENTS, key=lambda p: p["quality"])
        scored = [((in_tokens * profile["input"] + out_tokens * profile["output"]) / 1_000_000, in_tokens + out_tokens, profile["latency"], profile, profile["quality"], 2 / 3, 0)]
    cost, _, latency, profile, quality, reliability, samples = min(scored, key=lambda item: (item[0], item[1], item[2]))
    rationale = {
        "selection_policy": "lowest estimated cost among candidates meeting predicted quality and latency constraints",
        "quality_threshold": min_quality,
        "historical_success_rate": round(reliability, 3),
        "historical_samples": samples,
        "verification_recommended": verification,
        "catalog_quality_is_estimate": True,
        "meets_quality_threshold": quality >= min_quality,
        "meets_latency_threshold": req.max_latency_ms is None or latency <= req.max_latency_ms,
        "all_requirements_met": quality >= min_quality and (req.max_latency_ms is None or latency <= req.max_latency_ms),
    }
    return {
        "task_type": task_type, "complexity": complexity, "required_quality": min_quality,
        "selected_provider": profile["provider"], "selected_model": profile["model"],
        "predicted_input_tokens": in_tokens, "predicted_output_tokens": out_tokens,
        "predicted_cost": cost, "predicted_latency_ms": latency,
        "predicted_quality": quality, "confidence": reliability, "rationale": rationale,
        "verification_required": verification,
    }, profile
