# Suite format and metrics

Suites are shareable, versioned YAML. `name`, `version`, `type` (`standard` or `robustness`) and a `cases` array are supported. A case has a stable `id`, `input`, optional `tools`, ordered `expected_tool_calls`, `expected.contains` or exact expected text, `assertions.regex` / `assertions.exact` / `assertions.schema`, optional `context`, and extensible `policy` rules.

```yaml
name: Example
version: 1.0.0
type: standard
cases:
  - id: lookup-1
    input: "Look up order A-17"
    tools: [{name: lookup_order}]
    expected_tool_calls: [{tool: lookup_order, arguments: {order_id: A-17}}]
    expected: {contains: "In transit"}
    context: ["Order A-17 is in transit"]
    policy: [no_pii]
```

Metrics reported per case and suite: task success, tool name/argument/order correctness (including unknown-tool penalties), groundedness, policy compliance, p50/p95 latency, input/output tokens, and estimated USD cost. Every judge response includes a score, pass result, and rationale. Deterministic substring, exact, and regex assertions run locally. Custom judges may be supplied through the `Judge` interface; `ProviderJudge` adapts a caller-configured provider completion without selecting a vendor or silently making network calls.

Run `python scripts/agent_eval.py run config/suites/customer_support.yaml --agent-version release-42 --min-success 0.8 --max-cost 0.02`. Outputs are JSON and standalone HTML. JSONL history is stored at `.agent_eval/runs.jsonl`; run comparison is shown in AgentEval Studio. A nonzero exit code means the requested success or cost gate failed.

## Adapter API

An adapter implements `async run(prompt, tools, **kwargs) -> AgentTranscript`. Transcripts preserve ordered tool calls, tool results, assistant steps, agent identity, final output, retrieved context, token counts, measured latency, and cost. `CallableAdapter` wraps a sync/async callable; `LangChainAdapter` and `CrewAIAdapter` bridge common runnable/crew interfaces without adding hard dependencies. Multi-agent systems can include a distinct `agent` field on each `AgentStep`.

## Extension points

Implement the `Judge` protocol for custom/LLM judges. `MetricRegistry.register(name, callable)` accepts custom metric functions over a case and normalized transcript and makes those metrics available to the integrating runner. Configure provider judging via an injected completion callable; the harness itself does not pick a judge model.
