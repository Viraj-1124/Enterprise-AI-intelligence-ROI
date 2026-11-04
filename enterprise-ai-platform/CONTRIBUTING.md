# Contributing

Thanks for contributing to the open evaluation harness. Keep the core runner provider-neutral and deterministic by default.

## Development

Use Python 3.11+, install `uv`, then run `uv sync --extra dev`. Before opening a pull request, run `uv run ruff check app tests` and `uv run pytest`.

## Adding a metric or judge

Metric plugins should accept a case and normalized `AgentTranscript`, then return a numeric score, pass/fail value, and a concise rationale. Judges implement `judge(dimension, input, output, context, rules)` and should avoid hidden external calls. Provider-backed judging must be opt-in, configurable, and disclose model and spend.

## Adding an example suite

Add a versioned YAML file under `config/suites/`, use stable case IDs, and include expected assertions, tool calls, relevant context, and policies where applicable. Keep examples safe to run without secrets or network access.

## Pull requests

Describe the behavior change, include the command used to reproduce it, and attach the generated report for metric or judge changes. CI runs the sample quality gate.
