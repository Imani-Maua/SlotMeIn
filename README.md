# SlotMeIn

**SlotMeIn** is a FastAPI-based shift scheduling REST API that intelligently assigns employees ("talents") to shifts while respecting availability, labor regulations, and predicted demand — backed by a CP-SAT optimization solver and a trained ML staffing-tier predictor.

---

## Table of Contents

- [Live Demo](#live-demo)
- [Architecture Overview](#architecture-overview)
- [Project Structure](#project-structure)
- [Key Features](#key-features)
  - [1. CP-SAT Scheduling Engine](#1-cp-sat-scheduling-engine)
  - [2. ML Demand Prediction](#2-ml-demand-prediction)
  - [3. Async Job Queue (Redis Streams)](#3-async-job-queue-redis-streams)
  - [4. Constraint System](#4-constraint-system)
  - [5. Talent & Shift Management](#5-talent--shift-management)
  - [6. Authentication & Security](#6-authentication--security)
  - [7. Database Architecture](#7-database-architecture)
- [Setup](#setup)
- [Try Out SlotMeIn](#try-out-slotmein)
- [Tech Stack](#tech-stack)

---

## Live Demo

Experience the live application: **[SlotMeIn Live Demo](https://slotmein.vercel.app)**

> This app is invite-only by design. To explore the platform, use:
> - **Username:** `test.user`
> - **Password:** `Password@123`

The test database is pre-loaded with AI-generated data. User creation endpoints are restricted, but all core scheduling functionality is available.

---

## Architecture Overview

SlotMeIn runs as **two separate processes**:

```
┌─────────────────────┐     Redis Streams      ┌──────────────────────┐
│  API Server         │ ──── job queue ────►   │  Solver Worker       │
│  cmd/server/main.py │ ◄─── SSE events ─────  │  cmd/solver_pipeline │
│  (FastAPI)          │                         │  /main.py            │
└─────────────────────┘                         └──────────────────────┘
```

The API server accepts schedule generation requests, enqueues them as jobs in a Redis Stream, and immediately returns a `job_id`. Clients poll `/schedule/jobs/{job_id}` or subscribe to Server-Sent Events at `/schedule/events/{job_id}` to receive results as the solver completes.

---

## Project Structure

```
├── cmd/
│   ├── server/               # FastAPI entry point
│   │   └── main.py
│   └── solver_pipeline/      # Standalone solver worker process
│       └── main.py
├── app/
│   ├── authentication/       # JWT auth, user management
│   ├── config/               # Settings, logging, shift definitions
│   ├── core/
│   │   ├── constraints/      # Labor rule definitions & per-talent assignments
│   │   ├── schedule/
│   │   │   ├── allocator/    # CP-SAT scheduler (CSPScheduler)
│   │   │   ├── ml/           # Staffing-tier predictor (Random Forest)
│   │   │   ├── staffing/     # Staffing requirements routes & service
│   │   │   ├── shifts/       # Shift resolution logic
│   │   │   ├── talents/      # Talent assembly for scheduling
│   │   │   └── events/       # Redis job queue abstraction
│   │   ├── shift_template/   # Reusable shift pattern definitions
│   │   ├── shift_period/     # Shift time intervals
│   │   └── talents/          # Employee CRUD
│   ├── database/             # SQLAlchemy models, session, auth
│   └── redis/                # Redis client, job queue, result store, worker, event publisher
├── alembic/                  # Database migrations
├── data/
│   ├── raw/                  # Real hotel occupancy & rota data
│   └── prerocessed/          # Feature-engineered training sets
├── data_prep/                # Occupancy preprocessing scripts
├── models/                   # Trained .pkl model artifacts
├── notebooks/                # Jupyter notebooks (EDA, training, simulation)
├── scripts/                  # Thesis figure generation
├── tests/
│   ├── unit/
│   └── integration/
├── requirements.txt
└── alembic.ini
```

---

## Key Features

### 1. CP-SAT Scheduling Engine

`app/core/schedule/allocator/service.py`

The core scheduler uses **Google OR-Tools CP-SAT**, a constraint programming solver, to find an optimal or best-feasible schedule within a 30-second time budget.

**Hard constraints:**
- Each slot filled by at most one talent
- Each talent assigned at most one slot per shift
- One shift per talent per calendar day
- Minimum 11-hour rest between consecutive working days
- Maximum 6 consecutive working days (rolling window, accounting for history)

**Objective function** (maximized):

| Term | Weight |
|---|---|
| Filled slot | +200 per slot |
| Talent with scheduling constraint filled | +50 bonus |
| Shortfall below contracted weekly hours | −80 per centihour |
| Mild overwork (up to 115% of contract) | −20 per centihour |
| Steep overwork (beyond 115%) | −100 per centihour |

### 2. ML Demand Prediction

`app/core/schedule/ml/tier_predictor.py`

Before scheduling, staffing requirements per slot are predicted using **Random Forest classifiers** trained on real hotel rota and occupancy data. Separate models are trained for morning and afternoon shifts.

**Input features:** date, day of week, occupancy percentage, season, weekend flag, Hungarian public holidays, mean temperature

**Output:** staffing tier — `high`, `med`, or `low` — which maps to a required headcount per shift

Models are serialized to `models/` and loaded at server startup. Temperature defaults to seasonal averages for Budapest when not supplied.

### 3. Async Job Queue (Redis Streams)

`app/redis/`, `app/core/schedule/events/`

Schedule generation is offloaded to a dedicated worker process via **Redis Streams**:

1. `POST /schedule/generate` publishes a job and returns `{"job_id": "...", "status": "pending"}`
2. The solver worker picks up the job, runs the CP-SAT solver, and writes the result to a Redis result store
3. Clients poll `GET /schedule/jobs/{job_id}` or subscribe to `GET /schedule/events/{job_id}` (Server-Sent Events) for real-time progress

The worker handles graceful shutdown (SIGINT/SIGTERM), crash recovery (orphaned message reclaim), and explicit message acknowledgement.

### 4. Constraint System

`app/core/constraints/`

Labor rules are managed in two layers:
- **Constraint Rules**: global definitions (e.g., "Daily Work Limit", "Weekly Max Hours")
- **Talent Constraints**: links specific rules to individual talents, supporting per-contract configurations (part-time vs. full-time)

### 5. Talent & Shift Management

- **Talents**: full profiles with roles, skills, availability, and contracted hours
- **Shift Templates**: reusable shift patterns (e.g., "Morning", "Afternoon") instantiated across dates via shift periods
- **Staffing Requirements**: per-slot headcount requirements persisted to the database and returned with the schedule

### 6. Authentication & Security

`app/authentication/`

- **JWT / OAuth2**: stateless bearer-token authentication
- **Password hashing**: bcrypt via `passlib`
- **Invite-only registration**: new users are invited by superusers; self-signup is disabled

### 7. Database Architecture

`app/database/`

- **PostgreSQL**: primary data store (Supabase or local)
- **SQLAlchemy 2.0+**: modern ORM with type-safe models
- **Alembic**: versioned migrations (`alembic upgrade head`)
- **asyncpg**: async driver for high-throughput queries

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/Imani-Maua/slotmein.git
cd slotmein
```

### 2. Create a virtual environment

```bash
# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate

# Windows
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

Create a `.env` file in the project root:

```bash
# Database (Supabase recommended)
DATABASE_URL="postgresql://postgres.[your_id]:[password]@aws-0-region.pooler.supabase.com:5432/postgres?sslmode=require"
DB_HOST=db.xxxxxxxxxx.supabase.co
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=xxxxxxx

# Auth
KEY="your_super_secret_key"

# Email (invite flow)
RESEND_API_KEY="your_resend_api_key"

# Redis
REDIS_URL="redis://localhost:6379"
```

For local Postgres:

```bash
DATABASE_URL=postgresql://postgres:password@localhost/scheduler_db
```

### 5. Set up the database

```bash
alembic upgrade head
```

### 6. Start Redis

```bash
redis-server
```

### 7. Run the API server

```bash
uvicorn cmd.server.main:app --reload
```

The API will be available at `http://localhost:8000`.

### 8. Run the solver worker (separate terminal)

```bash
python -m cmd.solver_pipeline.main
```

The worker listens for schedule generation jobs from the Redis queue and processes them asynchronously.

### 9. Access the API documentation

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## Try Out SlotMeIn

**[slotmein.vercel.app](https://slotmein.vercel.app)** — test credentials above.

---

## Tech Stack

| Layer | Technology |
|---|---|
| API framework | FastAPI |
| Language | Python 3.12 |
| Solver | Google OR-Tools CP-SAT |
| ML | scikit-learn (Random Forest), joblib |
| Database | PostgreSQL |
| ORM / Migrations | SQLAlchemy 2.0+, Alembic |
| Async queue | Redis Streams |
| Logging | structlog |
| Auth | JWT, OAuth2, passlib (bcrypt) |
| Email | Resend |
| Testing | pytest |

---

### Developed by Maua Imani
