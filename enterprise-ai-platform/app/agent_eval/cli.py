"""Installed command entry point for AgentEval."""
import argparse
import asyncio
import json
from pathlib import Path

from app.agent_eval.runner import EvalRunner, history, render_html
from app.agent_eval.suites import load_suite


def main() -> int:
    parser = argparse.ArgumentParser(description="Vendor-neutral agent evaluation harness")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="Run a YAML evaluation suite")
    run.add_argument("suite", type=Path)
    run.add_argument("--agent-version", default="demo-v1")
    run.add_argument("--json", dest="json_path", type=Path, default=Path("agent-eval-results.json"))
    run.add_argument("--html", dest="html_path", type=Path, default=Path("agent-eval-report.html"))
    run.add_argument("--min-success", type=float, default=0.0)
    run.add_argument("--max-cost", type=float, default=float("inf"))
    hist = sub.add_parser("history", help="Show saved run history")
    hist.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.command == "history":
        runs = history()
        print(json.dumps(runs, indent=2) if args.json else f"{len(runs)} run(s) saved")
        return 0
    suite = load_suite(args.suite)
    result = asyncio.run(EvalRunner().run(suite, args.agent_version))
    args.json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    args.html_path.write_text(render_html(result), encoding="utf-8")
    s = result["summary"]
    print(f"{suite['name']} · {args.agent_version}")
    print("+----------------------+--------------+")
    print("| Metric               | Value        |")
    print("+----------------------+--------------+")
    for label, value in (("Cases", f"{s['passed']}/{s['case_count']} passed"), ("Success rate", f"{s['success_rate']:.1%}"), ("Tool accuracy", f"{s['tool_accuracy']:.1%}"), ("Groundedness", f"{s['groundedness']:.1%}"), ("Policy compliance", f"{s['policy_compliance']:.1%}"), ("p50 latency", f"{s['p50_latency_ms']:.1f} ms"), ("p95 latency", f"{s['p95_latency_ms']:.1f} ms"), ("Estimated cost", f"${s['cost_usd']:.5f}")):
        print(f"| {label:<20} | {value:<12} |")
    print("+----------------------+--------------+")
    for case in result["results"]:
        print(f"{'PASS' if case['passed'] else 'FAIL'}  {case['case_id']}: {case['name']}")
    print(f"JSON: {args.json_path}  HTML: {args.html_path}")
    return 1 if s["success_rate"] < args.min_success or s["cost_usd"] > args.max_cost else 0
