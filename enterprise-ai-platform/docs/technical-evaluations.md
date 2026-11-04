# Technical evaluation workstreams

This repository includes a reproducible harness and the seven research tracks from the product brief. No benchmark results are claimed here: no Jev service, model endpoints, representative edge devices, or approved datasets were supplied in the local environment. The table below records a practical experiment plan and current recommendation; populate measured values by running these tracks against the example YAML suites on target hardware.

## Implementation status

| Track | Implemented now | What the demo proves | What still needs a real backend/device |
|---|---|---|---|
| Jev / no-LLM work | Local Jev mock decision path, billing rule routing, optional `JEV_BASE_URL` HTTP adapter | Structured decisions can take a rule path with zero model calls in the mock flow | A real Jev service and a measured baseline for the same tasks |
| SLM replacing LLM | Small/medium/advanced model registry, local Qwen Ollama entry, confidence routing, model quality/cost metadata | Compare catalog estimates and see when confidence routing escalates | Run identical eval suites against actual small and large model endpoints; current catalog values are not measured |
| Edge AI | Strict-privacy placement policy and Ollama adapter for local laptop inference | Classification/extraction can be assigned local placement; unsupported strict tasks show a cloud escalation reason | Mobile Core ML/ONNX/llama.cpp adapters, device measurements, and verified local artifacts |
| Automatic model switching | Cost/quality, rule, complexity, and confidence strategies plus retry/escalation | Compare route choices and low-confidence escalation in the Workstreams page | Calibrated confidence/quality measurements and evaluation on production-like traffic |
| Task parallelism | Production DAG scheduler executes ready tasks concurrently and records critical path | Compare sequential and parallel scheduling with deterministic worker timings | Model-backed repetitions measuring coordination overhead and error propagation |
| Orchestration agent | Hierarchical, pipeline, and swarm DAG templates with worker identities/results in the simulator | Inspect delegation structure, dependencies, outputs, and critical path | An autonomous planning/delegation model; the sample planner is deterministic |
| Quantization | FP8/AWQ4/FP16 precision labels, catalog quality deltas, cost metadata, and provider precision truth fields | Inspect estimated trade-offs; real Ollama precision can be marked verified when exposed | Run actual quantized artifacts and measure quality, memory, and latency; mock labels are not quantization |

## Run the interactive workstreams demo

From `enterprise-ai-platform`, start the platform API in one terminal with `uv run uvicorn app.main:app --reload`, then start React in another with `cd frontend`, `npm install`, and `npm run dev`. Open the Vite URL and use the left navigation to open the seven simulations. The mock-first local API works without external model keys. See [docs/react-demo-guide.md](react-demo-guide.md) for a presentation walkthrough. The older Streamlit pages remain available but are no longer the primary demo UI.

For actual laptop inference, install Ollama, pull `qwen3.5:4b`, set `MODEL_PROVIDER=ollama` and `OLLAMA_BASE_URL`, then start the API. The API's strict privacy policy places supported classification/extraction tasks on the local model. Keep the dashboard's precision badge in view: a requested precision label is not a verified model artifact unless the provider confirms it.

| Workstream | Harness experiment | Measurements to record | Current integration recommendation |
|---|---|---|---|
| Jev / non-LLM compute | Compare deterministic tool execution with Jev and a local Python baseline on identical data-preparation and numerical tasks | wall time, error rate, setup/runtime cost | Keep Jev behind a tool adapter; route only when schema validation and measured benefit justify it |
| SLM substitution | Run the same cases against a small and large model, paired by task type | success, groundedness, policy, p50/p95, tokens, USD | Select per task type only after quality gates pass; record model identity in run metadata |
| Edge AI | Run an identical suite through Ollama, llama.cpp, ONNX Runtime, and Core ML adapters per device | quality, latency, peak memory, energy if available | Extend adapter metadata with device/runtime and verified model artifact |
| Automatic model switching | Compare fixed model, rules router, classifier router, and judge router on a frozen suite | success delta, cost delta, route choice, latency | Preserve route decisions as transcript events so regression diffs explain model switches |
| Task parallelism | Compare sequential and DAG/parallel execution on decomposable cases | wall-clock speedup, critical path, coordination cost, error propagation | Add concurrency and critical-path fields to transcript/run metadata |
| Orchestration agent | Compare hierarchical, swarm, and pipeline implementations on the same tasks | task success, tool correctness, total cost, latency, delegation trace | Preserve agent identity and parent/child relationships on every step |
| Quantization | Run model artifacts at FP16, INT8, and INT4 where supported | quality delta, latency, peak memory, artifact hash | Gate quantized variants on per-suite quality tolerance and verified precision metadata |

## Result template

For each track, save environment/device, model and artifact IDs, prompt/suite commit, adapter/runtime versions, run JSON, and HTML report. Record at least three repetitions per configuration and report median and spread. Do not compare costs unless token accounting and price assumptions are documented. These workstreams are intentionally reported as unmeasured until real backends are configured; mock runs validate the harness flow only.
