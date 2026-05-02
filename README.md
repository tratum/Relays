# Relays

---

## Overview

Relays is an **API-first Notification Delivery Service** built for backend systems that require reliable, asynchronous communication.

It provides a unified API to submit notifications and handles delivery through a durable, observable, and retry-aware pipeline. The system is designed to prioritize **correctness, failure handling, and explicit state management** over convenience abstractions.

> **Current Scope:** Email delivery (first implemented channel)

---

## Why Relays Exists

Most applications need to send notifications, but:

- synchronous delivery introduces latency and failure coupling
- retry logic is often inconsistent or duplicated across services
- delivery state is rarely tracked in a reliable, queryable way

Relays addresses these problems by acting as a **dedicated notification backend**:

```
Application → Relays API → Queue → Worker → Provider
```

---

## Target Users

Relays is designed for:

- Backend engineers building distributed systems
- Teams needing a reliable notification pipeline
- Developers who want asynchronous delivery without building it from scratch

> This system is intentionally **backend-only and API-driven**.

---

## Core Design Principles

### API-first

All functionality is exposed through well-defined HTTP APIs.

### Explicit state transitions

Every notification progresses through a clear lifecycle:

```
created → queued → processing → sent / failed
```

### Durability before execution

Notifications are persisted before being processed, ensuring reliability.

### Failures as first-class citizens

Failures are tracked, retried, and stored—not hidden.

### Minimal abstractions

The system avoids unnecessary layers to remain predictable and debuggable.

---

## Channel-Agnostic Architecture

Relays is designed to support multiple delivery channels, even though only **email** is currently implemented.

Each notification is modeled as:

```
channel + payload + metadata
```

This allows:

- consistent processing pipeline
- pluggable delivery providers
- easy extension to SMS, webhooks, etc.

---

## Key Capabilities

- Asynchronous notification processing
- Durable persistence using PostgreSQL
- Retry handling with exponential backoff (Celery-managed)
- Delivery attempt tracking
- Explicit lifecycle state management
  At-least-once delivery guarantees

---

## System Architecture

1. Client sends notification request via API
2. API validates and persists notification in PostgreSQL
3. Job is enqueued in Redis
4. Worker processes notification asynchronously
5. Delivery attempts are recorded
6. Notification transitions to `sent` or `failed`

```
Client
  ↓
FastAPI (API Layer)
  ↓
PostgreSQL (Source of Truth)
  ↓
Redis (Queue)
  ↓
Celery Workers
  ↓
Provider (Email)
```

---

## Notification Lifecycle

```
created
  → queued
  → processing
  → sent
       OR
  → failed
```

Each transition is persisted and queryable.

---

## Tech Stack

- **Backend:** FastAPI
- **Database:** PostgreSQL (asyncpg)
- **Queue & Cache:** Redis
- **Workers:** Celery
- **Containerization:** Podman
- **Package Management:** uv

---

## Documentation

- [API Contract](docs/API.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Data Model](docs/DATA_MODEL.md)
- [Worker Model](docs/WORKERS.md)
- [Recovery Model](docs/RECOVERY.md)
- [Product Requirements](docs/PRD.md)

---

## Setup

Relays supports two modes:

- **Docker (recommended)**
- **Manual (local development)**

---

### Option 1 — Docker (Recommended)

#### 1. Clone

```bash
git clone https://github.com/tratum/Relays.git
cd relays
```

#### 2. Create Environment File

Create a `.env.podman` file:

```env
ENV=dev
VERSION=v1
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/relays
REDIS_URL=redis://redis:6379/0
```

#### 3. Start Services

```bash
podman compose up -d --build
```

#### 4. Access Services

- API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- pgAdmin: [http://localhost:8080](http://localhost:8080)
- Redis Insight: [http://localhost:5540](http://localhost:5540)

#### 5. View Logs

```bash
podman compose logs -f api
podman compose logs -f worker
```

#### 6. Stop Services

```bash
podman compose down
```

---

### Option 2 — Manual Setup

#### 1. Install uv

```bash
curl -Ls https://astral.sh/uv/install.sh | sh
```

#### 2. Create Environment File

```env
ENV=dev
VERSION=v1
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/relays
REDIS_URL=redis://localhost:6379/0
```

#### 3. Install Dependencies

```bash
uv sync
```

#### 4. Start Dependencies

Ensure:

- PostgreSQL running on port 5432
- Redis running on port 6379

#### 5. Run Worker

```bash
uv run celery -A app.workers.celery.celery_conn worker -Q email -l info -E
```

#### 6. Run API

```bash
uv run uvicorn app.main:app --reload
```

---

## Example API Usage

### Create Notification

```http
POST /v1/notifications
Content-Type: application/json
```

```json
{
  "channel": "email",
  "payload": {
    "to": "user@example.com",
    "cc": [],
    "bcc": [],
    "subject": "Hello",
    "body": "Test message"
  },
  "metadata": {}
}
```

---

### Get Notification Status

```http
GET /v1/notifications/{notification_id}
```

---

## Current Limitations (MVP Scope)

- No authentication (API keys planned)
- Single-region deployment
- No rate limiting yet
- No billing/usage tracking
- No webhook callbacks

---

## Roadmap

- API key authentication
- Rate limiting and abuse protection
- Usage tracking and billing (Stripe)
- Additional channels (SMS, webhooks)
- Delivery status webhooks
- Optional dashboard

---

## Design Notes

- Retry scheduling is handled by **Celery**, not the database
- Database serves as **state and observability layer**
- Schema is initialized automatically at startup
- Lightweight migration system implemented (no Alembic)

---

## License

Not decided yet

---

## Final Note

Relays is built as a **production-minded backend system**, focusing on:

- correctness over shortcuts
- clarity over abstraction
- reliability over convenience
