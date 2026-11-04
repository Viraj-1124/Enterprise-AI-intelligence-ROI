"""Interactive, explicitly mock-labeled simulations for the seven research tracks."""
from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) in sys.path:
    sys.path.remove(str(ROOT))
sys.path.insert(0, str(ROOT))

import pandas as pd
import plotly.express as px
import streamlit as st
import yaml

from app.core.enums import PrecisionTier, TaskCategory
from app.core.schemas import Node, NodeResult, Plan, Request
from app.edge.edge_router import EdgeRouter
from app.execution.dag_scheduler import DAGScheduler
from app.providers.registry import ModelRegistry
from app.routing.jev_mock import JevMockBackend
from app.routing.precision_policy import PrecisionPolicy
from app.routing.strategies import STRATEGIES


st.set_page_config(page_title="AI Workstreams Lab", page_icon="🧭", layout="wide")
st.title("AI Workstreams Lab")
st.caption("Seven interactive architecture demos. Mock and catalog estimates are labeled; no benchmark numbers are presented as real-model measurements.")

registry = ModelRegistry()
mock_models = registry.candidates("mock")
local_models = registry.candidates("ollama")
tabs = st.tabs(["Jev / no LLM", "SLM vs LLM", "Edge AI", "Model switching", "Parallelism", "Orchestration", "Quantization"])


def run_async(coro):
    """Run an async demo in Streamlit's synchronous script context."""
    return asyncio.run(coro)


with tabs[0]:
    st.subheader("Use structured decisions for work that does not need generation")
    st.write("The mock Jev adapter answers configured classification questions locally. A mapped answer can return a rule result before the model path is called.")
    jev_input = st.text_input("Example request", "I was charged twice for my subscription. Please refund.", key="jev_input")
    if st.button("Simulate Jev decision", key="jev_run", type="primary"):
        schemas = yaml.safe_load((ROOT / "config" / "jev_schemas.yaml").read_text(encoding="utf-8"))
        questions = {key: choices for schema in schemas.values() for key, choices in schema.items()}
        decisions = run_async(JevMockBackend(ROOT / "config" / "router.yaml").decide(jev_input, questions))
        refund = decisions.get("refund_request", {}).get("choice")
        route = "rule:billing_handler" if refund == "Yes" else "regular model/router path"
        left, right = st.columns(2)
        left.metric("Decision", str(refund or "No refund decision"))
        right.metric("Selected path", route)
        st.json({"decisions": decisions, "route": route, "mock_model_calls": 0 if route.startswith("rule:") else 1})
        st.caption("This demonstrates the local Jev mock integration. Point JEV_BASE_URL at a real Jev service to exercise its HTTP adapter.")

with tabs[1]:
    st.subheader("Can a small model handle this task?")
    category = st.selectbox("Task type", ["classification", "extraction", "reasoning", "generation"], key="slm_category")
    model_rows = []
    for model in registry.list():
        delta = model.quant_accuracy_delta.get(category, 0.0)
        model_rows.append({"Model": model.display_name or model.id, "Provider": model.provider, "Size tier": model.tier,
                           "Catalog quality estimate": round(model.quality, 3), "Quality delta metadata": f"{delta:+.1%}",
                           "Input $ / 1K": model.cost_per_1k_in, "Output $ / 1K": model.cost_per_1k_out,
                           "Local option": "Yes" if model.provider == "ollama" else "No"})
    st.dataframe(pd.DataFrame(model_rows), hide_index=True, width="stretch")
    st.info("These are model-registry estimates, not measured SLM-vs-LLM benchmark results. Use AgentEval suites with actual provider adapters to measure task success, latency, tokens, and cost.")
    st.markdown("**Current small local model entry:** `qwen3.5:4b` through Ollama, for classification and extraction. Larger mock tiers provide a cost/quality baseline for routing simulations.")

with tabs[2]:
    st.subheader("Place privacy-sensitive work on a device")
    edge_category = st.selectbox("Task type", ["classification", "extraction", "reasoning", "generation"], key="edge_category")
    edge_privacy = st.selectbox("Privacy", ["strict", "standard"], key="edge_privacy")
    edge_model = local_models[0] if local_models else None
    edge_request = Request(input="Classify a private customer request", task_category=TaskCategory(edge_category), privacy=edge_privacy)
    edge_node = Node(node_id="edge-demo", task=edge_request.input, task_category=TaskCategory(edge_category))
    placement = EdgeRouter().place(edge_request, edge_node, edge_model)
    a, b, c = st.columns(3)
    a.metric("Placement decision", placement.target.upper())
    b.metric("Local model configured", edge_model.id if edge_model else "None")
    c.metric("Fallback reason", placement.escalation_reason or "Not required")
    st.write(placement.rationale)
    st.caption("Placement policy is implemented. Real laptop inference requires Ollama and the configured model; mobile runtimes (Core ML / ONNX / llama.cpp) still need provider adapters and device testing.")
    st.code("ollama pull qwen3.5:4b\n$env:MODEL_PROVIDER='ollama'\nuv run uvicorn app.main:app --reload", language="powershell")

with tabs[3]:
    st.subheader("Route each request to a suitable model")
    route_category = st.selectbox("Incoming task", ["classification", "extraction", "reasoning", "generation", "safety_critical"], key="route_category")
    confidence = st.slider("Router confidence", 0.0, 1.0, 0.9, 0.05)
    route_request = Request(input=f"Demo {route_category} request", task_category=TaskCategory(route_category), metadata={"confidence": confidence})
    route_rows = []
    for strategy_name in ("cost_quality", "rule_based", "complexity_based", "confidence_based"):
        decision = STRATEGIES[strategy_name].select(route_request, mock_models, PrecisionPolicy(ROOT / "config" / "precision_policy.yaml"))
        spec = registry.get(decision.model_id)
        route_rows.append({"Strategy": strategy_name, "Selected model": decision.model_id, "Tier": spec.tier,
                           "Precision label": decision.precision.value, "Confidence": f"{decision.confidence:.0%}", "Why": decision.rationale})
    st.dataframe(pd.DataFrame(route_rows), hide_index=True, width="stretch")
    st.caption("The confidence router escalates low-confidence requests to a higher-quality eligible model. Runtime retries and validation failures can also trigger escalation.")


class SimulatedExecutor:
    """Deterministic worker used to visualize scheduler behavior without LLM calls."""

    async def execute(self, node: Node, context: dict[str, str]) -> NodeResult:
        await asyncio.sleep(0.12)
        return NodeResult(node_id=node.node_id, output=f"Completed: {node.task}", latency_ms=120, cost_usd=0.0001, model_id="simulated-worker", provider="simulation")


def make_plan(pattern: str) -> Plan:
    if pattern == "pipeline":
        nodes = [Node(node_id="retrieve", task="Retrieve source data", task_category=TaskCategory.EXTRACTION),
                 Node(node_id="analyze", task="Analyze source data", task_category=TaskCategory.REASONING, depends_on=["retrieve"]),
                 Node(node_id="summarize", task="Summarize analysis", task_category=TaskCategory.GENERATION, depends_on=["analyze"])]
    elif pattern == "swarm":
        nodes = [Node(node_id="research", task="Research the request", task_category=TaskCategory.EXTRACTION),
                 Node(node_id="risk", task="Check policy risks", task_category=TaskCategory.CLASSIFICATION),
                 Node(node_id="finance", task="Estimate cost impact", task_category=TaskCategory.COMPUTATION),
                 Node(node_id="coordinator", task="Combine worker results", task_category=TaskCategory.GENERATION, depends_on=["research", "risk", "finance"])]
    else:
        nodes = [Node(node_id="planner", task="Break request into work", task_category=TaskCategory.CLASSIFICATION),
                 Node(node_id="researcher", task="Find supporting facts", task_category=TaskCategory.EXTRACTION, depends_on=["planner"]),
                 Node(node_id="analyst", task="Analyze the request", task_category=TaskCategory.REASONING, depends_on=["planner"]),
                 Node(node_id="synthesizer", task="Combine findings", task_category=TaskCategory.GENERATION, depends_on=["researcher", "analyst"])]
    return Plan(nodes=nodes)


with tabs[4]:
    st.subheader("Compare sequential work with parallel execution")
    if st.button("Run scheduler comparison", key="parallel_run", type="primary"):
        serial_trace = run_async(DAGScheduler(SimulatedExecutor()).schedule(make_plan("pipeline"), "serial-demo"))
        parallel_trace = run_async(DAGScheduler(SimulatedExecutor()).schedule(make_plan("swarm"), "parallel-demo"))
        serial_total = sum(n.latency_ms for n in serial_trace.nodes)
        parallel_total = parallel_trace.critical_path_latency_ms
        speedup = serial_total / max(1, parallel_total)
        left, middle, right = st.columns(3)
        left.metric("Sequential sum", f"{serial_total:.0f} ms")
        middle.metric("Parallel critical path", f"{parallel_total:.0f} ms")
        right.metric("Simulated speedup", f"{speedup:.2f}×")
        st.caption("Uses the production DAG scheduler with fixed-duration simulated workers; this measures scheduler structure, not model inference latency.")

with tabs[5]:
    st.subheader("Orchestrator patterns")
    pattern = st.selectbox("Pattern", ["hierarchical", "pipeline", "swarm"], key="orchestration_pattern")
    if st.button("Run orchestration plan", key="orchestration_run", type="primary"):
        plan = make_plan(pattern)
        trace = run_async(DAGScheduler(SimulatedExecutor()).schedule(plan, f"{pattern}-demo"))
        rows = [{"Worker": node.node_id, "Task": node.task, "Depends on": ", ".join(node.depends_on) or "—", "Output": next((str(r.output) for r in trace.nodes if r.node_id == node.node_id), "")} for node in plan.nodes]
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
        st.metric("Critical path", f"{trace.critical_path_latency_ms:.0f} ms")
        st.json({"pattern": pattern, "critical_path": next((e["critical_path"] for e in trace.events if "critical_path" in e), []), "worker_count": len(plan.nodes)})
    st.caption("This simulates orchestration plans and multi-worker traces. The planner is deterministic demo logic; an LLM meta-agent adapter is not configured by default.")

with tabs[6]:
    st.subheader("Compare precision and quantization trade-offs")
    quant_category = st.selectbox("Task category", ["classification", "extraction", "reasoning", "generation"], key="quant_category")
    precision_rows = []
    for model in mock_models:
        for precision in model.precisions:
            delta = model.quant_accuracy_delta.get(quant_category, 0.0) if precision == PrecisionTier.AWQ4 else 0.0
            precision_rows.append({"Model": model.id, "Precision option": precision.value, "Catalog quality": model.quality,
                                   "Estimated quality after delta": round(max(0.0, model.quality + delta), 3),
                                   "Quality delta metadata": f"{delta:+.1%}", "Input $ / 1K": model.cost_per_1k_in,
                                   "Output $ / 1K": model.cost_per_1k_out})
    precision_df = pd.DataFrame(precision_rows)
    st.dataframe(precision_df, hide_index=True, width="stretch")
    st.plotly_chart(px.scatter(precision_df, x="Output $ / 1K", y="Estimated quality after delta", color="Precision option", hover_name="Model", title="Catalog trade-off (estimated)"), width="stretch")
    st.caption("Mock precision labels and quality deltas demonstrate the evaluation flow only. For real quantization results, compare actual quantized model artifacts and confirm runtime precision in Provider Truth.")

