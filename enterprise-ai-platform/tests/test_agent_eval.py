import json

import pytest

from app.agent_eval.adapters import AgentStep, AgentTranscript
from app.agent_eval.runner import EvalRunner, compare_tools, render_html
from app.agent_eval.suites import load_suite


def test_load_suite_checks_unique_case_ids(tmp_path):
    suite_file = tmp_path / "suite.yaml"
    suite_file.write_text("name: Demo\ncases:\n  - {id: one, input: hello}\n", encoding="utf-8")
    assert load_suite(suite_file)["name"] == "Demo"
    suite_file.write_text("name: Demo\ncases:\n  - {id: one, input: hi}\n  - {id: one, input: hello}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Duplicate case id"):
        load_suite(suite_file)


def test_tool_match_checks_sequence_arguments_and_unknown_tools():
    expected = [{"tool": "lookup", "arguments": {"id": 4}}]
    available = [{"name": "lookup"}]
    exact, _ = compare_tools(expected, [AgentStep("tool_call", tool="lookup", arguments={"id": 4})], available)
    wrong, _ = compare_tools(expected, [AgentStep("tool_call", tool="lookup", arguments={"id": 5})], available)
    hallucinated, rationale = compare_tools(expected, [AgentStep("tool_call", tool="made_up")], available)
    assert exact == 1
    assert wrong == 0
    assert hallucinated == 0
    assert "Unknown tool" in rationale


@pytest.mark.asyncio
async def test_runner_records_metrics_history_and_html_report(tmp_path):
    suite = load_suite("config/suites/customer_support.yaml")
    runner = EvalRunner(history_path=tmp_path / "runs.jsonl")
    run = await runner.run(suite)
    assert run["summary"]["success_rate"] == 1
    assert run["summary"]["p95_latency_ms"] >= run["summary"]["p50_latency_ms"]
    saved = json.loads((tmp_path / "runs.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert saved["run_id"] == run["run_id"]
    assert "Customer Support Quality" in render_html(run)


@pytest.mark.asyncio
async def test_regressed_demo_fails_release_cases(tmp_path):
    suite = load_suite("config/suites/policy_compliance.yaml")
    run = await EvalRunner(history_path=tmp_path / "runs.jsonl").run(suite, "demo-regressed")
    assert run["summary"]["success_rate"] == 0
    assert all(not case["passed"] for case in run["results"])


def test_transcript_preserves_multi_agent_metadata_shape():
    transcript = AgentTranscript(output="done", steps=[AgentStep("assistant", "done", agent="planner")])
    assert transcript.steps[0].agent == "planner"
