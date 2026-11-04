# React demo guide

## Start the demo

Use two PowerShell terminals from the `enterprise-ai-platform` directory.

**Terminal 1 — API**

```powershell
uv run uvicorn app.main:app --reload
```

**Terminal 2 — frontend**

```powershell
cd frontend
npm install
npm run dev
```

Open the Vite URL, usually `http://localhost:5173`. The frontend uses Vite's proxy to reach the API on port 8000. The local default API key is `demo-key`; override the UI key with `VITE_API_KEY` if your `.env` uses a different API key.

## Suggested five-minute walkthrough

1. Start on **Overview**. Explain that the live KPI cards read from the local API and the trend chart fills after evaluation runs.
2. Open **Jev · no-LLM work**. Keep the duplicate-charge example and run it. Show the structured refund decision, billing-rule route, zero model nodes, and Jev decision in the trace.
3. Open **SLM vs LLM**. Select a model available through the configured backend and run the task. Point out that the trace records the selected model, provider, precision request, latency, and cost. Registry quality/cost metadata are estimates until measured by real evaluations.
4. Open **Edge AI**. Run the classification example with strict privacy, then switch to reasoning. The former demonstrates local placement; the latter shows that the configured edge model does not support this task under the current policy. Default mock mode labels the provider as `mock`; use Ollama for an actual local-model call.
5. Open **Automatic switching**. Run **Compare confidence**. The same request is sent once with high confidence and once with low confidence; compare the model IDs and route rationales.
6. Open **Task parallelism** and run a multi-step task. Inspect the node count, critical path, and trace. Then open **Orchestration agent** and compare hierarchical, pipeline, and swarm dependency patterns.
7. Open **Quantization**. Select a model and supported precision, run the task, and inspect `precision_requested`, `precision_verified`, and `precision_note`. A mock precision label is explicitly unverified.
8. Open **Agent evaluation**. Run `demo-v1` to show passing cases, then `demo-regressed` to show a release regression and rationale. The run is saved and appears in history.

## What is live and what is simulated

The routing, Jev rule path, execution graph, release-gate runner, and API traces are real local project code. In the default configuration the model adapter is deterministic mock inference, so latency and output do not represent production models. Model quality, quantization deltas, and cost fields from YAML are registry estimates. Use configured OpenAI/Anthropic/Ollama adapters and run the YAML suites to produce backend-specific measurements. Mobile inference runtimes and an autonomous planning model are not included.
