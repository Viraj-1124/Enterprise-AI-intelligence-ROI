# Enterprise AI Platform backend

This folder contains the Python/FastAPI backend, AgentEval harness, legacy Streamlit dashboards, configuration, and the React frontend in `frontend/`.

For the complete project overview and collaborator setup—from cloning the repository through starting both frontend and backend—see the [repository README](../README.md).

## Quick start from this folder

Requirements: Python 3.10+, [`uv`](https://docs.astral.sh/uv/), Node.js 20+, and npm. The default demo uses mock models and needs no provider credentials.

1. Create local configuration and install Python dependencies:

   ```powershell
   Copy-Item .env.example .env
   uv sync --extra dev
   ```

2. In terminal one, start the API from this folder:

   ```powershell
   uv run uvicorn app.main:app --reload
   ```

3. In terminal two, install and start the React UI:

   ```powershell
   cd frontend
   npm ci
   npm run dev
   ```

4. Open <http://localhost:5173>. The API health check is <http://127.0.0.1:8000/health> and API documentation is at <http://127.0.0.1:8000/docs>.

The primary interactive demo is the **Simulation** tab. It shows the seven research capabilities and the backend's execution trace. The Streamlit dashboards under `app/dashboard/` are retained for legacy metrics screens.

## Other useful commands

```powershell
uv run pytest
uv run ruff check app tests
uv run python scripts/agent_eval.py run config/suites/customer_support.yaml --agent-version demo-v1
npm --prefix frontend run build
```

For technical evaluation boundaries and optional local-model setup, see [technical evaluations](docs/technical-evaluations.md) and the [runbook](RUNBOOK.md).
