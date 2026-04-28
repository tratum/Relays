# Relays

---

## Overview

Relays is an **API-first Notification Delivery Service** designed for backend systems that require reliable and asynchronous communication.

It allows applications to submit notification requests via HTTP APIs and delivers them asynchronously with robust status tracking, retry mechanisms, and failure handling.

Relays is built as a backend platform component with a strong focus on **correctness, durability, and explicit state management**.

> **Current Scope:** Email delivery (first implemented channel)

---

## Target Users

Relays is intended for:

- Backend engineers building internal services and distributed systems
- Small teams needing a simple, reliable notification backend
- Developers integrating asynchronous email delivery into their applications

> This system is **not intended for end users or non-technical customers**.

---

## Philosophy

Relays follows a set of core design principles:

- **API-first**
  All functionality is exposed through clear and consistent HTTP APIs.

- **Minimal abstractions**
  Avoids unnecessary layers to maintain simplicity and predictability.

- **Explicit state transitions**
  Every notification moves through well-defined and observable states.

- **Failures as first-class citizens**
  Errors are expected, tracked, and handled systematically rather than hidden.

---

## Channel-Agnostic Design

Relays is designed as a **channel-agnostic notification system**, even though the current implementation supports **email only**.

Notifications are modeled as a generic delivery intent with a `channel` and `payload`, allowing the same pipeline to support multiple delivery mechanisms (e.g. email, SMS, webhooks).

The system ensures that:

- Core processing (queueing, retries, state transitions) is **independent of channel**
- Channel-specific logic is isolated and can be extended without changing core components

> Email is the first implemented channel, not a special case.

---

## Key Capabilities

- Asynchronous notification processing
- Durable persistence before execution
- Retry handling with backoff
- Delivery attempt tracking
- Explicit lifecycle state management
- At-least-once delivery guarantees

---

## High-Level Flow

1. Client sends notification request via API
2. API validates and persists notification in PostgreSQL
3. Job is enqueued in Redis
4. Worker processes notification asynchronously
5. Delivery attempts are recorded
6. Notification transitions to `sent` or `failed`

---

## Documentation

Detailed system design and behavior are documented separately:

- [API Contract](docs/API.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Data Model](docs/DATA_MODEL.md)
- [Worker Model](docs/WORKERS.md)
- [Recovery Model](docs/RECOVERY.md)
- [Product Requirements](docs/PRD.md)

---

## Setup

### 1. Install `uv`

```bash
curl -Ls https://astral.sh/uv/install.sh | sh
```

### 2. Clone the Repository

```bash
git clone https://github.com/tratum/Relays.git
cd relays
```

### 3. Configure Environment

Create a `.env` file in the root directory:

```env
ENV=dev
VERSION=v1
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/relays
REDIS_URL=redis://localhost:6379/0
```

### 4. Install Dependencies

```bash
uv sync
```

### 5. Run Celery Workers

```bash
celery -A app.workers.celery.celery_conn worker --loglevel=info -Q email
```

### 6. Run the Application

```bash
uv run uvicorn app.main:app --reload
```

---

## Roadmap (Post-MVP)

- API key authentication
- Rate limiting and abuse protection
- Usage tracking and billing
- Additional channels (SMS, webhooks)
- Webhook callbacks for delivery status

---

## License

Not Decided Yet
