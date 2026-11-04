from __future__ import annotations

import asyncio
import html
import json
import math
import re
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.agent_eval.adapters import AgentAdapter, AgentStep, AgentTranscript, CallableAdapter
from app.agent_eval.judges import DeterministicJudge, Judge


class DemoAgent:
    """Predictable sample agent used by the local showcase and example suites."""

    async def __call__(self, prompt: str, tools: list[dict[str, Any]], **kwargs: Any) -> dict[str, Any]:
        case = kwargs.get("case", {})
        expected = case.get("expected", {})
        output = str(expected.get("contains", "")) if isinstance(expected, dict) else str(expected)
        if not output:
            output = "I can help with that request."
        calls = case.get("expected_tool_calls", [])
        if kwargs.get("agent_version") == "demo-regressed":
            output = "I am unable to complete this request."
            calls = []
        steps = [{"kind": "tool_call", "tool": c.get("tool"), "arguments": c.get("arguments", {})} for c in calls]
        return {"output": output, "steps": steps, "context": case.get("context", []), "input_tokens": max(1, len(prompt.split())), "output_tokens": max(1, len(output.split())), "cost_usd": 0.00012}


class EvalRunner:
    def __init__(self, adapter: AgentAdapter | None = None, judge: Judge | None = None, history_path: str | Path = ".agent_eval/runs.jsonl") -> None:
        self.adapter = adapter or CallableAdapter(DemoAgent(), "demo-agent")
        self.judge = judge or DeterministicJudge()
        self.history_path = Path(history_path)

    async def run(self, suite: dict[str, Any], version: str = "demo-v1") -> dict[str, Any]:
        started = datetime.now(timezone.utc).isoformat()
        results = await asyncio.gather(*(self._case(case, version) for case in suite["cases"]))
        passed = sum(r["passed"] for r in results)
        latencies = [r["latency_ms"] for r in results]
        summary = {"case_count": len(results), "passed": passed, "failed": len(results)-passed, "success_rate": passed / max(1, len(results)),
                   "tool_accuracy": statistics.mean([r["tool_use"]["score"] for r in results]) if results else 0,
                   "groundedness": statistics.mean([r["groundedness"]["score"] for r in results]) if results else 0,
                   "policy_compliance": statistics.mean([r["policy"]["score"] for r in results]) if results else 0,
                   "p50_latency_ms": percentile(latencies, .50), "p95_latency_ms": percentile(latencies, .95),
                   "cost_usd": sum(r["cost_usd"] for r in results), "input_tokens": sum(r["input_tokens"] for r in results), "output_tokens": sum(r["output_tokens"] for r in results)}
        run = {"run_id": str(uuid4()), "suite": suite["name"], "suite_version": suite.get("version", "1"), "agent_version": version,
               "started_at": started, "completed_at": datetime.now(timezone.utc).isoformat(), "summary": summary, "results": results}
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        with self.history_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(run, ensure_ascii=False) + "\n")
        return run

    async def _case(self, case: dict[str, Any], version: str) -> dict[str, Any]:
        tools = case.get("tools", [])
        start = time.perf_counter()
        transcript = await self.adapter.run(case["input"], tools, case=case, agent_version=version)
        measured = (time.perf_counter() - start) * 1000
        latency = transcript.latency_ms or measured
        expected = case.get("expected", {})
        expected_text = expected.get("contains", "") if isinstance(expected, dict) else str(expected or "")
        output = transcript.output
        assertions = case.get("assertions", {})
        checks: list[dict[str, Any]] = []
        if expected_text:
            checks.append({"name": "contains", "passed": expected_text.lower() in output.lower(), "expected": expected_text})
        if assertions.get("regex"):
            checks.append({"name": "regex", "passed": bool(re.search(assertions["regex"], output)), "expected": assertions["regex"]})
        if assertions.get("exact") is not None:
            checks.append({"name": "exact", "passed": output.strip() == assertions["exact"], "expected": assertions["exact"]})
        if assertions.get("schema"):
            schema_error = None
            try:
                import jsonschema

                jsonschema.validate(json.loads(output), assertions["schema"])
            except Exception as exc:
                schema_error = str(exc)
            checks.append({"name": "schema", "passed": schema_error is None, "rationale": "Output matches JSON schema." if schema_error is None else schema_error})
        tool_context = [str(s.result) for s in transcript.steps if isinstance(s, AgentStep) and s.result is not None]
        grounded_context = [*transcript.context, *tool_context] or case.get("context", [])
        task_judgment = None
        if case.get("judge_task_success"):
            task_judgment = self.judge.judge(dimension="task_success", input=case["input"], output=output, context=grounded_context, rules=[])
        tool_score, tool_rationale = compare_tools(case.get("expected_tool_calls", []), transcript.steps, tools)
        ground = self.judge.judge(dimension="groundedness", input=case["input"], output=output, context=grounded_context, rules=[])
        policy_rules = case.get("policy", [])
        policy_rules = [({"type": r} if isinstance(r, str) else dict(r)) for r in policy_rules]
        policy_rules = [{**r, "actual_cost": transcript.cost_usd} if r.get("type") == "max_cost" else r for r in policy_rules]
        policy = self.judge.judge(dimension="policy", input=case["input"], output=output, context=transcript.context, rules=policy_rules)
        ok = all(c["passed"] for c in checks) and (task_judgment is None or task_judgment["passed"]) and tool_score >= 1 and ground["passed"] and policy["passed"]
        return {"case_id": case["id"], "name": case.get("name", case["id"]), "input": case["input"], "output": output,
                "passed": ok, "checks": checks, "task_success_judge": task_judgment, "tool_use": {"score": tool_score, "passed": tool_score >= 1, "rationale": tool_rationale},
                "groundedness": ground, "policy": policy, "steps": [s.__dict__ if isinstance(s, AgentStep) else s for s in transcript.steps],
                "latency_ms": latency, "cost_usd": transcript.cost_usd, "input_tokens": transcript.input_tokens, "output_tokens": transcript.output_tokens,
                "context": grounded_context, "policy_rules": case.get("policy", [])}


def compare_tools(expected: list[dict[str, Any]], steps: list[AgentStep], available: list[dict[str, Any]]) -> tuple[float, str]:
    actual = [s for s in steps if (s.kind if isinstance(s, AgentStep) else s.get("kind")) == "tool_call"]
    names = {t.get("name", t.get("tool")) for t in available}
    hallucinated = [((s.tool if isinstance(s, AgentStep) else s.get("tool"))) for s in actual if ((s.tool if isinstance(s, AgentStep) else s.get("tool"))) not in names]
    if hallucinated:
        return 0.0, f"Unknown tool(s) called: {', '.join(map(str, hallucinated))}."
    def normalized(s: Any) -> tuple[Any, Any]:
        if isinstance(s, AgentStep): return s.tool, s.arguments
        return s.get("tool"), s.get("arguments", {})
    want, got = [normalized(s) for s in expected], [normalized(s) for s in actual]
    score = sum(a == b for a, b in zip(want, got)) / max(1, len(want), len(got))
    return score, "Tool names, arguments, and order match." if score == 1 else f"Expected {want}; observed {got}."


def percentile(values: list[float], q: float) -> float:
    if not values: return 0.0
    seq = sorted(values)
    return round(seq[min(len(seq)-1, max(0, math.ceil(len(seq)*q)-1))], 2)


def render_html(run: dict[str, Any]) -> str:
    rows = []
    for r in run["results"]:
        rows.append(f"<details><summary>{'✅' if r['passed'] else '❌'} {html.escape(r['name'])} · {r['latency_ms']:.1f} ms · ${r['cost_usd']:.5f}</summary><h4>Input</h4><pre>{html.escape(r['input'])}</pre><h4>Output</h4><pre>{html.escape(r['output'])}</pre><pre>{html.escape(json.dumps({k:r[k] for k in ('checks','tool_use','groundedness','policy','steps')}, indent=2))}</pre></details>")
    s = run["summary"]
    return f"<!doctype html><html><meta charset='utf-8'><title>AgentEval report</title><style>body{{font:16px system-ui;max-width:1100px;margin:40px auto;background:#f5f7fa;color:#172033}}header,details{{background:white;padding:20px;margin:12px 0;border-radius:12px;box-shadow:0 2px 14px #14243a12}}.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}}.card{{background:#eef3f8;padding:14px;border-radius:9px}}pre{{white-space:pre-wrap}}</style><header><h1>AgentEval · {html.escape(run['suite'])}</h1><p>Agent {html.escape(run['agent_version'])} · Run {run['run_id']}</p><div class='grid'>{''.join(f'<div class="card"><b>{v}</b><br>{k.replace("_", " ")}</div>' for k,v in s.items() if k in ('success_rate','tool_accuracy','groundedness','policy_compliance','p95_latency_ms','cost_usd','input_tokens','output_tokens'))}</div></header>{''.join(rows)}</html>"


def history(path: str | Path = ".agent_eval/runs.jsonl") -> list[dict[str, Any]]:
    p = Path(path)
    return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()] if p.exists() else []
