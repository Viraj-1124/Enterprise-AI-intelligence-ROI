"""Interactive showcase for the evaluation harness."""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

# Streamlit places this script's folder on sys.path. That folder also contains
# dashboard/app.py, which can shadow the actual top-level `app` package.
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) in sys.path:
    sys.path.remove(str(ROOT))
sys.path.insert(0, str(ROOT))

import pandas as pd
import plotly.express as px
import streamlit as st

from app.agent_eval.runner import EvalRunner, history
from app.agent_eval.suites import load_suite

SUITES = ROOT / "config" / "suites"
st.set_page_config(page_title="AgentEval Studio", page_icon="🧪", layout="wide")
st.markdown("<style>.block-container{padding-top:2rem}.hero{padding:25px 28px;border-radius:18px;background:linear-gradient(120deg,#102344,#275b73);color:white;margin-bottom:20px}.hero p{color:#d2e4f2}.stMetric{background:#f5f8fc;padding:14px;border-radius:12px}</style>", unsafe_allow_html=True)
st.markdown("<div class='hero'><h1>AgentEval Studio</h1><p>Run realistic agent quality gates, inspect every judgment, and compare releases.</p></div>", unsafe_allow_html=True)
suite_files = sorted(SUITES.glob("*.yaml"))
suite_names = {load_suite(p)["name"]: p for p in suite_files}
if "latest_run" not in st.session_state:
    st.session_state.latest_run = None

left, right = st.columns([1, 2])
with left:
    st.subheader("Run configuration")
    selected = st.selectbox("Evaluation suite", list(suite_names))
    version = st.selectbox("Agent / prompt version", ["demo-v1", "demo-regressed"], help="Choose demo-regressed to see case failures and regression diffs. Replace the adapter in code to run your own agent.")
    gate = st.slider("Minimum success-rate gate", 0, 100, 80, format="%d%%")
    max_cost = st.number_input("Maximum run cost (USD)", min_value=0.0, value=0.01, step=0.001, format="%.4f")
    suite = load_suite(suite_names[selected])
    st.caption(suite.get("description", ""))
    st.write(f"**{len(suite['cases'])} cases** · {suite['type']} suite · v{suite['version']}")
    with st.expander("Preview case inputs"):
        for case in suite["cases"]:
            st.markdown(f"**{case.get('name', case['id'])}**\n\n{case['input']}")
    run_clicked = st.button("▶ Run evaluation", type="primary", width="stretch")
with right:
    st.subheader("Evaluation dimensions")
    st.markdown("Task success · tool selection, arguments and order · groundedness · policy compliance · latency p50/p95 · token and dollar cost")
    st.info("The included demo agent produces reproducible fixture outputs. Plug in a callable adapter or framework bridge to evaluate a real agent.")
    st.code("python scripts/agent_eval.py run config/suites/customer_support.yaml --agent-version v2", language="powershell")

if run_clicked:
    with st.spinner("Running cases and recording auditable judgments…"):
        st.session_state.latest_run = asyncio.run(EvalRunner(history_path=ROOT / ".agent_eval" / "runs.jsonl").run(suite, version))

runs = history(ROOT / ".agent_eval" / "runs.jsonl")
current = st.session_state.latest_run or (runs[-1] if runs else None)
if current:
    s = current["summary"]
    st.divider()
    st.subheader(f"Latest run · {current['suite']} · {current['agent_version']}")
    cols = st.columns(6)
    labels = ["Success", "Tool accuracy", "Groundedness", "Policy", "p95 latency", "Run cost"]
    values = [f"{s['success_rate']:.0%}", f"{s['tool_accuracy']:.0%}", f"{s['groundedness']:.0%}", f"{s['policy_compliance']:.0%}", f"{s['p95_latency_ms']:.1f} ms", f"${s['cost_usd']:.5f}"]
    for col, label, value in zip(cols, labels, values):
        col.metric(label, value)
    if s["success_rate"] < gate / 100 or s["cost_usd"] > max_cost:
        st.error("Release gate failed: success threshold or cost cap was breached.")
    else:
        st.success("Release gate passed for the configured thresholds.")
    cases = current["results"]
    overview, details, regression = st.tabs(["Case results", "Judgment details", "Run comparison"])
    with overview:
        df = pd.DataFrame([{"Case": c["name"], "Status": "Passed" if c["passed"] else "Failed", "Latency (ms)": c["latency_ms"], "Cost (USD)": c["cost_usd"]} for c in cases])
        st.dataframe(df, hide_index=True, width="stretch")
        st.plotly_chart(px.bar(df, x="Case", y="Latency (ms)", color="Status", color_discrete_map={"Passed":"#21a179","Failed":"#df5262"}), width="stretch")
    with details:
        for c in cases:
            with st.expander(f"{'✅' if c['passed'] else '❌'} {c['name']}"):
                st.markdown(f"**Input**\n\n{c['input']}\n\n**Agent output**\n\n{c['output']}")
                st.json({"assertions": c["checks"], "tool_use": c["tool_use"], "groundedness": c["groundedness"], "policy": c["policy"], "transcript_steps": c["steps"]})
    with regression:
        prior = [r for r in runs if r["suite"] == current["suite"] and r["run_id"] != current["run_id"]]
        if not prior:
            st.info("Run the suite with another agent version to populate the comparison.")
        else:
            prev = prior[-1]
            st.caption(f"Comparing {prev['agent_version']} → {current['agent_version']}")
            a, b = st.columns(2)
            a.metric("Success rate change", f"{(s['success_rate']-prev['summary']['success_rate'])*100:+.1f} pp")
            b.metric("Cost change", f"${s['cost_usd']-prev['summary']['cost_usd']:+.5f}")
            old = {r["case_id"]: r for r in prev["results"]}
            changed = [{"Case": c["name"], "Previous": "Pass" if old.get(c["case_id"], {}).get("passed") else "Fail", "Current": "Pass" if c["passed"] else "Fail", "Reason": c["tool_use"]["rationale"] if c["tool_use"]["score"] < 1 else (c["checks"] or [{"name":"all checks"}])[-1].get("name", "judgment changed")} for c in cases if c["case_id"] not in old or old[c["case_id"]]["passed"] != c["passed"]]
            st.dataframe(pd.DataFrame(changed) if changed else pd.DataFrame([{"Case":"All cases","Previous":"Pass","Current":"Pass","Reason":"No outcome regressions"}]), hide_index=True, width="stretch")
    st.download_button("Download run JSON", json.dumps(current, indent=2), file_name="agent-eval-results.json", mime="application/json")
else:
    st.divider()
    st.markdown("### Run history")
    if runs:
        st.dataframe(pd.DataFrame([{"Run":r["run_id"][:8],"Suite":r["suite"],"Agent":r["agent_version"],"Success":r["summary"]["success_rate"],"Cost":r["summary"]["cost_usd"],"Started":r["started_at"]} for r in runs]).tail(12), hide_index=True, width="stretch")
    else:
        st.caption("No runs yet. Choose a suite and run the simulator to generate an evaluation report.")
