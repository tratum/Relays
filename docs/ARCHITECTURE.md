# System Architecture

---

# 1. Purpose

This document defines the overall system architecture of **Relays**.

It describes the major architectural decisions, system boundaries, component responsibilities, infrastructure, execution flow, and long-term evolution strategy.

The goal of this document is **not** to describe individual APIs or database schemas. Instead, it explains **how the entire platform is structured** and **why specific architectural decisions were made**.

Detailed implementation documents are maintained separately:

- `AUTH.md`
- `DATA_MODEL.md`
- `API.md`
- `WORKERS.md`
- `RECOVERY.md`
- `BILLING.md`

---

# 2. Design Principles

Relays is designed as an **API-first notification infrastructure platform**.

Every architectural decision follows a small set of core principles.

## API First

Everything exposed by the platform is designed around stable, versioned HTTP APIs.

Internal implementations may change, but API contracts should remain backward compatible whenever possible.

---

## Modular Monolith

Relays is implemented as a **Modular Monolith**.

The application is divided into independent business modules with clear ownership boundaries while sharing a single deployment and database.

Current modules include:

- Authentication
- Workspaces
- API Keys
- Notifications

This architecture minimizes operational complexity while allowing individual modules to be extracted into independent services in the future.

---

## PostgreSQL is the Source of Truth

Persistent business state always resides in PostgreSQL.

Examples include:

- Users
- Workspaces
- API Keys
- Sessions
- Notifications
- Delivery Attempts

Redis is never treated as the source of truth.

---

## Redis is Infrastructure

Redis provides infrastructure capabilities rather than persistent storage.

Current responsibilities include:

- Celery message broker
- OTP rate limiting

Future responsibilities may include:

- API key rate limiting
- Notification rate limiting
- Webhook rate limiting
- Read-through caching

Redis data should always be considered disposable.

---

## Asynchronous by Default

Notification delivery is inherently asynchronous.

API requests should complete quickly after validation and persistence.

Actual delivery is delegated to background workers.

This provides:

- Lower API latency
- Better reliability
- Automatic retries
- Provider isolation

---

## Explicit Business Workflows

Business operations are implemented as explicit workflows.

Examples include:

- Registration
- Login
- Notification Submission
- Notification Delivery

Workflows coordinate multiple database operations and infrastructure components while keeping business logic centralized.

---

## Thin API Layer

Route handlers are intentionally minimal.

Their responsibilities are limited to:

- Request validation
- Invoking workflows
- Returning responses

Business logic never lives inside API routes.

---

## Infrastructure Isolation

Infrastructure concerns are separated from business logic.

Examples include:

- PostgreSQL
- Redis
- JWT
- Celery
- Mail Providers

Business modules depend on abstractions rather than implementation details wherever practical.

---

# 3. High-Level Architecture

The system architecture can be represented as:

```text
                           Clients
                              │
                              ▼
                      HTTPS REST API
                              │
                              ▼
                        FastAPI Server
                              │
      ┌───────────────┬───────────────┬───────────────┐
      │               │               │               │
      ▼               ▼               ▼               ▼
 Authentication   Notifications   API Keys    Workspaces
      │               │               │               │
      └───────────────┴───────┬───────┴───────────────┘
                              ▼
                          Workflows
                 ┌────────────┼────────────┐
                 ▼            ▼            ▼
           PostgreSQL      Redis       Celery
                 │                          │
                 │                          ▼
                 │                  Background Workers
                 │                          │
                 └──────────────────────────▼
                     Notification Providers
```

Every incoming request ultimately passes through a workflow before interacting with infrastructure.

Business modules never communicate directly with one another through HTTP.

![Relays Architecture](docs/digrams/Architecture.png)

---

# 4. Component Overview

## FastAPI

FastAPI exposes the public HTTP interface of Relays.

Responsibilities:

- Request validation
- Authentication
- Response serialization
- OpenAPI generation

FastAPI does not implement business rules.

---

## PostgreSQL

PostgreSQL stores all durable platform state.

Examples include:

- Users
- Workspaces
- API Keys
- Sessions
- Notifications
- Delivery Attempts

Every business operation ultimately persists data to PostgreSQL.

---

## Redis

Redis provides low-latency infrastructure services.

Current usage:

- Celery broker
- Sliding-window rate limiting

Redis may be safely cleared without permanent data loss.

---

## Celery

Celery executes asynchronous jobs.

Current responsibilities:

- Email delivery

Future responsibilities may include:

- SMS delivery
- Webhook delivery
- Scheduled tasks
- Usage aggregation

---

## Notification Providers

Providers integrate with external delivery services.

Current provider implementations include:

- Deterministic fake provider
- Mailrelay

Additional providers can be introduced without modifying higher-level workflows.

---

# 5. Request Lifecycle

A typical API request follows the same execution path.

```text
HTTP Request
      │
      ▼
FastAPI Route
      │
      ▼
Validation
      │
      ▼
Workflow
      │
      ▼
Database
      │
      ▼
Response
```

For asynchronous operations:

```text
HTTP Request
      │
      ▼
FastAPI Route
      │
      ▼
Workflow
      │
      ▼
Persist Notification
      │
      ▼
Publish Celery Task
      │
      ▼
Return 201 Created
                     │
                     ▼
             Background Worker
                     │
                     ▼
          External Notification Provider
```

This separation ensures API responsiveness regardless of provider latency.

---

# 6. Module Architecture

Each business capability is implemented as an independent module.

A module owns:

- Routes
- Schemas
- Workflows
- Database queries
- Security components
- Constants

A typical module structure is:

```text
module/
├── api/
├── db/
├── schemas/
├── workflows/
├── security/
└── constants.py
```

This organization keeps related functionality together while minimizing coupling between modules.

---

# 7. Infrastructure Components

Infrastructure code is isolated under the `infra` package.

Responsibilities include:

- PostgreSQL connection management
- Redis client management
- Celery configuration
- Middleware
- Authentication guards
- Background worker runtime

Infrastructure components should not contain business rules.

They provide reusable services consumed by workflows.

---

# 8. Data Ownership

Each business entity has a single owner.

| Entity            | Owner               |
| ----------------- | ------------------- |
| Users             | Authentication      |
| Sessions          | Authentication      |
| Registration OTP  | Authentication      |
| Login OTP         | Authentication      |
| Workspaces        | Workspace Module    |
| Workspace Members | Workspace Module    |
| API Keys          | API Key Module      |
| Notifications     | Notification Module |
| Delivery Attempts | Notification Module |

Ownership defines which module is responsible for creating, updating, and validating each entity.

---

# 9. Asynchronous Processing

Notification delivery is intentionally decoupled from request processing.

The API accepts a notification request by:

1. Validating the payload.
2. Persisting the notification.
3. Publishing a worker task.
4. Returning immediately.

Delivery occurs independently in the background.

This architecture enables retries, provider failover, and resilience without impacting client latency.

---

# 10. Authentication Architecture

Authentication is implemented as an independent subsystem.

Major capabilities include:

- Email OTP registration
- Email OTP login
- JWT access tokens
- Refresh tokens
- Session management
- Refresh token rotation
- Logout
- Current user retrieval
- OTP rate limiting

Authentication details are documented in `AUTH.md`.

---

# 11. Failure Isolation

Relays is designed so failures remain localized whenever possible.

Examples include:

- Email provider outages do not prevent notification submission.
- Worker failures do not terminate API requests.
- Redis failures do not corrupt PostgreSQL state.
- Individual notification failures do not affect unrelated notifications.

This isolation improves reliability and simplifies recovery.

---

# 12. Scalability Strategy

Relays is designed to scale incrementally.

Horizontal scaling can be achieved independently for:

- API servers
- Celery workers
- PostgreSQL
- Redis

The modular architecture also allows business modules to be extracted into independent services as requirements evolve.

---

# 13. Future Evolution

The current Modular Monolith is intentionally designed to support future decomposition.

Potential future services include:

```text
Authentication Service

Workspace Service

Notification Service

Billing Service

Provider Service
```

Because business logic is already isolated into modules, migration to independently deployable services can occur with relatively small architectural changes.

---

# 14. Non-Goals

This document intentionally does not describe:

- Individual API endpoints
- Database schema definitions
- Worker retry algorithms
- Authentication implementation details
- Provider-specific integrations
- Billing logic

These concerns are documented separately in their respective design documents.
