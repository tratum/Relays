# Relays

---

## Overview

Relays is an **API-first Notification Delivery Service** built for backend systems that require reliable, asynchronous communication.

It provides a unified API for submitting notifications while managing asynchronous delivery through durable background workers.

Relays treats notification delivery as a stateful workflow rather than a single network request. Every notification progresses through an explicit lifecycle, every delivery attempt is recorded, and temporary failures are retried automatically using a durable retry engine.

The platform is designed around correctness, observability, fault tolerance, and provider independence.

> **Current Scope:** Email delivery (first implemented channel)

---

## Project Status

### Implemented

- Email Notifications
- Notification Engine
- Retry Engine
- Worker Architecture
- API Key Authentication
- JWT Authentication
- Workspace Management
- Idempotency
- OTP Authentication
- Sliding-window Rate Limiting

### In Progress

- Billing & Subscriptions

### Planned

- Integrating Email Sending for Email OTP
- Notification Rate Limiting
- Billing & Subscriptions
- Usage Tracking
- SMS
- Webhooks
- Dashboard

---

## Why Relays Exists

Most applications need to send notifications, but:

- synchronous delivery introduces latency and failure coupling
- retry logic is often inconsistent or duplicated across services
- delivery state is rarely tracked in a reliable, queryable way

Relays addresses these problems by acting as a **dedicated notification backend**:

```
Application
      │
      ▼
 Relays API
      │
      ▼
 PostgreSQL
      │
      ▼
 Notification Queue
      │
      ▼
 Background Worker
      │
      ▼
 Provider
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
created
   ↓
queued
   ↓
processing
   ├──────────────► sent
   │
   ├──────────────► failed
   │
   ▼
temporary failure
   │
   ▼
queued
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

- Unified API for asynchronous notifications
- Durable notification persistence
- Background worker execution
- Automatic retry scheduling
- Immutable delivery attempt history
- Explicit notification lifecycle
- Provider-independent delivery architecture
- API key authentication
- At-least-once delivery guarantees

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
   │
   ▼
FastAPI
   │
   ▼
Notification Submission
   │
   ▼
PostgreSQL
   │
   ▼
Notification Queue
   │
   ▼
Redis
   │
   ▼
Channel Worker
   │
   ▼
Provider Registry
   │
   ▼
Email Provider

```

---

## Notification Lifecycle

```

created
   │
   ▼
queued
   │
   ▼
processing
   ├──────────────► sent
   │
   ├──────────────► failed
   │
   ▼
temporary failure
   │
   ▼
queued

```

Each transition is persisted and queryable.

---

## Tech Stack

- **Backend:** FastAPI
- **Database:** PostgreSQL (asyncpg)
- **Queue & Cache:** Redis
- **Workers:** Celery + Celery Beat
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
- [Retry Engine] (docs/RETRY_ENGINE.md)
- [Providers] (docs/PROVIDERS.md)

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
ENABLE_DOCS=True
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/relays
JWT_ALGORITHM="HS256"
# JWT signing secret. Generate with:
# python -c "import secrets; print(secrets.token_urlsafe(64))"
JWT_SECRET=xxxx-xxxxx_xxxxx-xxxxxx # Cryptographically Secure random url-friendly string with 64 bytes (512 bits) of entropy
```

#### 3. Prepare pgAdmin Data Directory

Required for rootless Podman so pgAdmin can write to its data volume.

```bash
mkdir -p ./data/pgadmin
podman unshare chown -R 5050:5050 ./data/pgadmin
```

#### 4. Start Services

```bash
podman compose up -d --build
```

#### 5. Access Services

- API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- pgAdmin: [http://localhost:8080](http://localhost:8080)
- Redis Insight: [http://localhost:5540](http://localhost:5540)

#### 6. View Logs

```bash
podman compose logs -f api
podman compose logs -f worker
```

#### 7. Stop Services

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
ENABLE_DOCS=True
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/relays
JWT_ALGORITHM="HS256"
# JWT signing secret. Generate with:
# python -c "import secrets; print(secrets.token_urlsafe(64))"
JWT_SECRET=xxxx-xxxxx_xxxxx-xxxxxx # Cryptographically Secure random url-friendly string with 64 bytes (512 bits) of entropy
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
uv run celery -A app.infra.workers.celery.celery_conn worker -Q email -l info -E
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
    "subject": "Hello",
    "html_body": "<h1>Hello</h1>"
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

- Email is the only supported delivery channel.
- Recovery & reconciliation subsystem not yet implemented.
- Dead-letter queues not yet implemented.
- Scheduled notifications not yet implemented.

---

## Roadmap

- SMS notifications
- Webhook notifications
- Scheduled notifications
- Dead-letter queues
- Recovery & reconciliation engine
- Usage-based billing
- Provider routing
- Delivery webhooks
- Dashboard

---

## Design Notes

- PostgreSQL is the authoritative source of notification state.
- Redis acts solely as an execution transport.
- Workers remain stateless and always reload notification state before execution.
- Retry intent is stored durably in PostgreSQL.
- Delivery attempts are immutable and append-only.
- Providers never modify notification state directly.
- Schema is initialized automatically during application startup.
- Lightweight SQL migrations are used instead of a migration framework.

---

## License

Not decided yet

---

## Final Note

Relays is built as a **production-minded backend system**, focusing on:

- correctness over shortcuts
- clarity over abstraction
- reliability over convenience
