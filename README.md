# Enterprise AI Intelligence & ROI Platform

An enterprise platform for measuring **AI adoption, AI-assisted productivity, task outcomes, estimated business value, and AI ROI** across development workflows.

The platform connects AI/work activity with measurable work outcomes instead of looking only at AI usage or token consumption.

## Core Idea

```text
AI Usage
   ↓
Work Activity
   ↓
Task Outcome
   ↓
Time Saved
   ↓
Estimated Business Value
   ↓
AI Cost
   ↓
ROI
```

The goal is to help organizations answer:

> **How much value are we actually getting from the AI tools our employees use?**

---

## Features

### 1. AI Usage Tracking

Track AI-assisted activity where legitimate telemetry is available.

Supported information can include:

* AI provider
* Model
* Input tokens
* Output tokens
* Total tokens
* AI cost
* Timestamp
* Employee
* Task
* Session

The system does **not fabricate unavailable AI telemetry**.

If provider/model/token/cost information cannot be obtained through a legitimate source, the platform displays it as unavailable.

---

### 2. Work Session Tracking

Track development work externally through observable activity such as:

* Session start/end
* Task duration
* Git activity
* Commits
* Files changed
* Lines added/removed
* Tests executed
* Test results
* Build results

The platform does not modify or inject into external AI development tools.

---

### 3. Task-Level Productivity

Each task can contain:

* Employee
* Department
* Task type
* Manual baseline time
* Actual completion time
* AI-assisted status
* Work activity
* Task outcome

This allows the platform to estimate how much time was saved on individual tasks.

---

### 4. ROI Calculation

The platform calculates estimated economic value using:

```text
Time Saved =
Manual Baseline - Actual Time
```

```text
Estimated Labor Value =
(Time Saved / 60) × Employee Hourly Cost
```

```text
Net Estimated Value =
Estimated Labor Value - AI Cost
```

```text
ROI (%) =
((Estimated Labor Value - AI Cost) / AI Cost) × 100
```

ROI is shown as **N/A** when reliable AI cost information is unavailable.

### Important

ROI is an estimated economic model based on configured assumptions and observed work activity. It is not presented as causal proof of productivity improvement.

---

## 5. AI Adoption

The platform measures AI adoption at different levels.

### Task Adoption

```text
AI-assisted tasks / Total eligible tasks × 100
```

### Time Adoption

```text
AI-assisted work minutes / Total eligible work minutes × 100
```

### Employee Adoption

```text
Employees using AI / Eligible employees × 100
```

These metrics can be analyzed by:

* Employee
* Team
* Department
* Task type
* Time period

---

## 6. Management Dashboard

The management dashboard provides visibility into:

* AI Spend
* AI-Assisted Tasks
* AI Adoption
* Time Saved
* Estimated Business Value
* Net Estimated Value
* AI Cost
* ROI
* Department-level performance
* AI provider usage
* Task-level results

Charts and drill-down views allow management to move from organization-level metrics to individual tasks.

---

## 7. Task ROI Detail

Each task provides a detailed breakdown of:

### Task Information

* Employee
* Department
* Task
* Status
* Start time
* Completion time
* Duration

### AI Information

* Provider
* Model
* Tokens
* AI cost
* AI interactions

### Work Outcome

* Manual baseline
* Actual time
* Time saved
* Time saved percentage
* Files changed
* Commits
* Tests
* Build status

### Economic Value

* Employee hourly cost
* Estimated labor value
* AI cost
* Net value
* ROI

---

## 8. Prompt Intelligence

The Prompt Intelligence module analyzes prompts based on:

* Clarity
* Context
* Specificity
* Output requirements
* Completeness
* Ambiguity
* Technical requirements
* Testing requirements

It provides:

* Prompt analysis
* Improvement suggestions
* Missing requirement detection
* Improved prompt

Example:

### Original

```text
Build an API for users.
```

### Improved

```text
Build a REST API for user management using FastAPI.
Implement create, read, update, and delete operations.
Use PostgreSQL with SQLAlchemy.
Validate request data with Pydantic.
Return appropriate HTTP status codes.
Add tests for successful requests,
validation failures, and database errors.
```

The current prototype uses lightweight deterministic analysis rather than depending on a complex AI system.

---

# Architecture

```text
                   AI / WORK TOOLS
          ┌──────────┬──────────┬──────────┐
          │ AI Tools │ GitHub   │  Jira    │
          └────┬─────┴────┬─────┴────┬─────┘
               │          │          │
               └──────────┼──────────┘
                          ↓
                   Connector Layer
                          ↓
                   ┌─────────────┐
                   │   FastAPI   │
                   │ ONE BACKEND │
                   └──────┬──────┘
                          ↓
                     PostgreSQL
                          ↓
                  Analytics / ROI
                          ↓
                  Next.js / React
                          ↓
              Management Dashboards
```

---

# Technology Stack

## Backend

* Python
* FastAPI
* SQLAlchemy
* PostgreSQL
* Pydantic
* Alembic
* Pytest

## Frontend

* Next.js
* React
* TypeScript
* Tailwind CSS
* Recharts

## Data Collection

* Python
* Git
* External connectors

## Infrastructure

* Docker
* Docker Compose

---

# Project Structure

```text
enterprise-ai-intelligence/
│
├── backend/
│   ├── app/
│   ├── tests/
│   ├── requirements.txt
│   └── README.md
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── types/
│   └── package.json
│
├── collector/
│   ├── collector.py
│   ├── git_tracker.py
│   ├── session_tracker.py
│   └── tests/
│
├── connectors/
│   ├── base.py
│   ├── openai.py
│   ├── gemini.py
│   ├── claude.py
│   ├── github.py
│   ├── jira.py
│   └── antigravity.py
│
├── analytics/
│   ├── roi_engine.py
│   ├── productivity.py
│   ├── cost.py
│   └── tests/
│
├── docs/
│   ├── architecture.md
│   └── data-model.md
│
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

---

# Installation

## Prerequisites

Install:

* Python 3.11+
* Node.js 20+
* npm
* Docker
* Git

---

# 1. Clone the Repository

```bash
git clone <YOUR_REPOSITORY_URL>
cd enterprise-ai-intelligence
```

---

# 2. Start PostgreSQL

```bash
docker compose up -d postgres
```

Verify:

```bash
docker compose ps
```

---

# 3. Backend Setup

Create a virtual environment:

```bash
cd backend
python -m venv .venv
```

### Windows

```bash
.venv\Scripts\activate
```

### macOS/Linux

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# 4. Environment Variables

Create the environment file:

```bash
cp .env.example .env
```

On Windows, create `.env` manually if `cp` is unavailable.

Configure the required values.

Example:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/enterprise_ai
SECRET_KEY=change-this-secret
```

Provider API keys should only be added when the corresponding connector is actually being used.

**Never commit `.env` to GitHub.**

---

# 5. Database Migration

Run:

```bash
alembic upgrade head
```

---

# 6. Start Backend

From the `backend` directory:

```bash
uvicorn app.main:app --reload
```

Backend:

```text
http://localhost:8000
```

API documentation:

```text
http://localhost:8000/docs
```

---

# 7. Frontend Setup

Open another terminal:

```bash
cd frontend
npm install
```

Start development server:

```bash
npm run dev
```

Frontend:

```text
http://localhost:3000
```

---

# 8. Run Collector

From the project root:

```bash
python collector/collector.py start
```

Stop the collector with:

```bash
python collector/collector.py stop
```

The collector sends normalized work events to the FastAPI backend.

---

# Testing

## Backend

From `backend/`:

```bash
pytest
```

---

## Analytics

From the project root:

```bash
pytest analytics/tests
```

---

## Collector

```bash
pytest collector/tests
```

---

## Frontend

```bash
npm run build
```

---

# Data Provenance

The platform distinguishes between different types of data.

| Source          | Meaning                                        |
| --------------- | ---------------------------------------------- |
| **Observed**    | Directly observed work activity                |
| **Connector**   | Obtained from a supported external integration |
| **Estimated**   | Calculated using configured assumptions        |
| **Imported**    | Provided through an external data import       |
| **Unavailable** | Data cannot currently be obtained              |

This distinction is important for trustworthy ROI reporting.

---

# Privacy & External Tool Policy

The platform is designed as an external measurement layer.

It does **not**:

* Modify AI development tools
* Inject code into AI applications
* Access private application internals
* Fabricate AI telemetry
* Claim access to unavailable token/cost data

Only legitimately accessible external data should be collected.

---

# Current Research Direction

The current prototype focuses on:

```text
AI Adoption
+
Work Activity
+
Task Outcomes
+
AI Cost
+
Estimated Business Value
+
ROI
+
Prompt Intelligence
```

Future research will extend the platform toward:

### Adaptive AI Agent Routing

Automatically selecting the most suitable AI agent/model for a task based on:

* Task complexity
* Expected quality
* Token consumption
* AI cost
* Latency
* Verification effort
* Rework probability
* Historical task performance

The proposed optimization objective is:

```text
Minimize:

AI Cost
+ Verification Cost
+ Rework Cost
+ Latency Cost

Subject to:

Required Quality
and
Required Success Probability
```

This will form the basis for future experimental evaluation.

---

# Limitations

Current limitations include:

* AI telemetry depends on available external APIs/connectors.
* Some AI tools do not expose private token/cost information.
* Manual task baselines may introduce estimation bias.
* Employee hourly cost is an assumption.
* ROI represents modeled economic value rather than causal productivity impact.
* Larger datasets are required for statistically robust research conclusions.

---

# Future Work

Planned research extensions:

1. Dynamic task-effort prediction
2. Counterfactual non-AI task-time estimation
3. AI agent/model routing
4. Cost-aware multi-agent orchestration
5. Quality-aware routing
6. Verification and rework modeling
7. Adaptive routing based on historical outcomes
8. Large-scale experimental evaluation

---

# Project Status

**Current Stage:** Prototype completed

**Implemented scope:**

* AI usage measurement
* Work/session tracking
* Task outcome tracking
* ROI calculation
* AI adoption metrics
* Management dashboard
* Task-level ROI
* Prompt Intelligence
* External connector architecture

**Research optimization layer:** Planned

---

# Disclaimer

The platform provides estimated analytics based on available observations and configured assumptions.

AI ROI should be interpreted as an **estimated economic indicator**, not as definitive proof that AI caused a particular productivity improvement.
