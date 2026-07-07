# Retry Engine

---

# Purpose

This document defines the architecture, execution model, guarantees, and design principles of the Retry Engine in Relays.

The Retry Engine is responsible for automatically retrying notification deliveries that fail due to temporary, recoverable conditions.

Unlike workers, which execute notification delivery, the Retry Engine determines **when** a notification becomes eligible for another delivery attempt and orchestrates its re-execution.

The Retry Engine is intentionally designed as a separate subsystem from notification delivery to improve durability, scalability, and fault tolerance.

---

# Current Status

The Retry Engine is fully implemented.

Current capabilities include:

- Durable retry scheduling
- Exponential backoff
- Automatic retry discovery
- Stateless retry execution
- Provider-independent retry handling
- Persistent retry intent stored in PostgreSQL

Future improvements are documented at the end of this document.

---

# Why a Retry Engine Exists

Notification delivery interacts with external systems that are outside the control of Relays.

Temporary failures are therefore expected rather than exceptional.

Examples include:

- Network interruptions
- Provider timeouts
- HTTP 429 (Rate Limited)
- HTTP 503 (Service Unavailable)
- Temporary DNS failures
- Transient infrastructure outages

Retrying these failures immediately is often ineffective.

Instead, notifications should be retried after an appropriate delay.

The Retry Engine exists to automate this process while ensuring retries remain durable across worker crashes, process restarts, infrastructure failures, and Redis outages.

---

# Retry Engine Goals

The Retry Engine is designed around several core goals.

## Durable Retry Intent

Retry decisions must survive application restarts and infrastructure failures.

Retry intent is therefore persisted in PostgreSQL rather than being maintained in worker memory.

---

## Automatic Retry Execution

Clients should never need to manually trigger retries.

Once a notification has been accepted by Relays, temporary delivery failures are retried automatically until either:

- delivery succeeds
- maximum retry attempts are exhausted
- a permanent failure occurs

---

## Provider Independence

Retry behaviour should be identical regardless of the delivery provider.

Providers communicate delivery outcomes through a common `ProviderResult`.

The Retry Engine makes retry decisions without requiring provider-specific logic.

---

## Stateless Workers

Workers should execute delivery attempts without managing retry timers.

This keeps workers lightweight, horizontally scalable, and easy to replace.

---

## Deterministic Behaviour

Given identical notification state, the Retry Engine should always produce the same retry decision.

Retry scheduling is therefore derived entirely from persisted notification state rather than transient worker state.

---

# Non-Goals

The Retry Engine intentionally does not provide:

- Exactly-once delivery
- Notification recovery after worker crashes
- Dead-letter queue processing
- Provider reconciliation
- Scheduled notifications
- Manual retry management

These responsibilities either belong to other subsystems or are planned future features.

---

# Architecture Overview

The Retry Engine consists of four major components.

```text
Notification Worker
        │
        ▼
Temporary Failure
        │
        ▼
Persist Retry Intent
(PostgreSQL)
        │
        ▼
Celery Beat
        │
        ▼
Retry Scheduler
        │
        ▼
Claim Retryable Notifications
        │
        ▼
Notification Queue
        │
        ▼
Notification Worker
```

Each component owns a single responsibility.

The worker determines that a retry is required.

The database persists retry intent.

The scheduler discovers eligible notifications.

Workers execute the retry as a normal notification delivery.

No component performs more than one responsibility.

---

# Retry Lifecycle

The lifecycle of a retry begins when a provider reports a temporary delivery failure.

```text
Notification Worker
        │
        ▼
ProviderResult
(TEMPORARY_FAILURE)
        │
        ▼
Persist Retry Intent
        │
        ▼
Notification State → queued
        │
        ▼
Wait Until next_retry_at
        │
        ▼
Retry Scheduler
        │
        ▼
Notification Queue
        │
        ▼
Worker Executes Notification
```

The worker does not remain active while waiting for the retry interval.

Instead, it persists retry intent and immediately completes execution.

Retry execution becomes the responsibility of the Retry Scheduler.

---

# Retry Scheduling

Retry scheduling begins when a provider reports a temporary delivery failure.

Providers never schedule retries directly. Instead, they communicate the delivery outcome by returning a `ProviderResult` with a status of `TEMPORARY_FAILURE`.

The Notification Worker then becomes responsible for determining whether another delivery attempt should be made.

If the notification has remaining retry attempts:

1. `attempt_count` is incremented.
2. The delivery attempt is recorded.
3. The next retry time is calculated.
4. Retry intent is persisted.
5. Worker execution ends.

No waiting occurs inside the worker.

The notification simply becomes eligible for future execution.

---

## Retry Backoff Policy

Relays currently uses exponential backoff.

The retry delay increases after each failed delivery attempt.

Example:

| Attempt |      Delay |
| ------: | ---------: |
|       1 |   1 second |
|       2 |  2 seconds |
|       3 |  4 seconds |
|       4 |  8 seconds |
|       5 | 16 seconds |

The retry policy is deterministic.

Given the same notification state, the calculated retry time will always be identical.

Future versions may introduce:

- configurable retry policies
- jitter
- provider-specific retry strategies
- workspace-specific retry policies

---

# Persisting Retry Intent

A retry is represented entirely by notification state stored in PostgreSQL.

When a retry is scheduled, the notification is updated with:

- `state = queued`
- `next_retry_at`
- updated timestamps

No retry information is stored inside:

- Celery
- Redis
- worker memory
- provider implementations

This makes PostgreSQL the single source of truth for retry scheduling.

---

# Retry Discovery

Retry discovery is performed periodically by the Retry Scheduler.

The scheduler itself performs no delivery.

Its responsibility is limited to discovering notifications that have become eligible for execution.

Eligibility is determined using:

- notification state
- retry timestamp

A notification is considered retryable when:

- state is `queued`
- `next_retry_at` is not NULL
- `next_retry_at <= now()`

Notifications that satisfy these conditions are claimed atomically before being re-enqueued for processing.

---

## Atomic Claiming

Retry discovery uses row-level locking to ensure that multiple scheduler workers cannot claim the same notification simultaneously.

The implementation relies on:

```sql
FOR UPDATE SKIP LOCKED
```

This allows multiple scheduler workers to operate concurrently without introducing duplicate retry execution.

Each notification can only be claimed once for a given retry cycle.

---

# Retry Execution

Once retryable notifications have been claimed, they are placed back onto the normal notification queue.

From this point onward, retries are indistinguishable from an initial notification delivery.

The Notification Worker performs the same execution flow regardless of whether the notification represents:

- the first delivery attempt
- a retry

Workers therefore contain no retry-specific execution logic.

They simply process the notification's current state.

---

# Retry State Machine

Successful notification delivery:

```text
created
   │
   ▼
queued
   │
   ▼
processing
   │
   ▼
sent
```

Retry flow:

```text
processing
   │
   ▼
temporary failure
   │
   ▼
queued
   │
   ▼
processing
   │
   ▼
temporary failure
   │
   ▼
queued
   │
   ▼
processing
   │
   ├──────────────► sent
   │
   └──────────────► failed
```

The notification continues cycling until one of the terminal states is reached.

---

# Retry Guarantees

The Retry Engine provides the following guarantees.

## Durable Retry Scheduling

Retry intent is stored in PostgreSQL.

A process restart does not lose pending retries.

---

## Stateless Execution

Workers never maintain retry timers.

Worker crashes therefore cannot leave retry state stranded inside process memory.

---

## Provider Independence

Retry behaviour is identical regardless of delivery provider.

Providers only report delivery outcomes.

They never schedule retries.

---

## At-Least-Once Delivery

Notifications may be executed more than once.

Clients should therefore design downstream systems to tolerate duplicate deliveries where necessary.

Relays intentionally prioritizes reliable delivery over exactly-once execution.

---

## Observable State

Every retry attempt is observable.

Clients can inspect:

- notification state
- attempt count
- delivery attempt history

to understand the complete delivery lifecycle.

---

# Retry Ownership

Each component in the retry pipeline owns exactly one responsibility.

| Component           | Responsibility                               |
| ------------------- | -------------------------------------------- |
| Provider            | Report delivery outcome                      |
| Notification Worker | Persist delivery result and schedule retries |
| PostgreSQL          | Persist retry intent                         |
| Celery Beat         | Trigger periodic retry discovery             |
| Retry Scheduler     | Discover eligible notifications              |
| Notification Queue  | Transport execution requests                 |
| Notification Worker | Execute the next delivery attempt            |

No component is responsible for more than one stage of the retry lifecycle.

---

# Failure Scenarios

## Worker Crash

If a worker crashes before persisting a retry decision, the notification remains in its previous durable state.

Future recovery mechanisms will reconcile these notifications.

---

## Redis Restart

Redis is used only as a transport mechanism.

Retry intent remains safely persisted in PostgreSQL.

Pending retries are therefore delayed but not lost.

---

## Scheduler Downtime

If the Retry Scheduler stops running, retry execution pauses.

Once scheduling resumes, all notifications whose retry time has already passed become eligible for execution.

---

## PostgreSQL Restart

Retry intent remains durable.

Once PostgreSQL becomes available again, retry scheduling resumes without requiring any reconstruction of notification state.

---

# Design Decisions

The Retry Engine is built around a small number of architectural principles that influence every part of its implementation.

---

## Why Not Celery Retries?

Celery provides a built-in retry mechanism that allows workers to reschedule failed tasks.

Relays intentionally does not use this mechanism.

Celery retries make the task queue responsible for retry scheduling, causing retry state to exist outside the application's domain model.

Instead, Relays stores retry intent in PostgreSQL.

This provides several advantages:

- retry state is durable
- retry state is observable
- retry state survives worker crashes
- retry behaviour is provider-independent
- retry scheduling becomes deterministic

The application, rather than the task queue, owns notification delivery semantics.

---

## Why PostgreSQL Owns Retry Intent?

Notification state already resides in PostgreSQL.

Persisting retry intent alongside notification state ensures that all information required to continue delivery exists in a single authoritative location.

Every retry decision is therefore durable and queryable.

This greatly simplifies:

- debugging
- operational visibility
- future recovery
- reconciliation
- auditing

PostgreSQL becomes the source of truth for notification execution.

---

## Why Not Redis Delayed Queues?

Redis supports delayed execution patterns through sorted sets or third-party queue implementations.

Relays intentionally avoids using Redis to persist retry schedules.

Redis is treated as an execution transport rather than durable storage.

Using Redis for retry scheduling would introduce several drawbacks:

- retry intent could be lost during Redis failures
- retry state would become difficult to inspect
- retry information would be split across multiple systems
- recovery would require reconstructing queue state

Instead, Redis is only responsible for transporting execution requests.

Retry scheduling remains entirely within PostgreSQL.

---

## Why Workers Never Sleep

After scheduling a retry, a worker exits immediately.

Workers never wait for retry delays.

Sleeping workers unnecessarily consume:

- worker processes
- memory
- concurrency

Instead, workers persist retry intent and return to the queue.

This allows worker capacity to be used for active notification processing rather than idle waiting.

---

## Why Celery Beat?

The Retry Scheduler requires a mechanism for periodically discovering notifications whose retry time has arrived.

Celery Beat performs this role.

Its responsibility is intentionally minimal.

It simply triggers periodic execution of the Retry Scheduler.

Beat does not:

- determine retry policy
- persist retry intent
- track notification state

Those responsibilities remain within the application.

---

## Why Separate Scheduling from Execution?

Retry scheduling and notification execution solve different problems.

Scheduling determines **when** work should occur.

Execution performs **how** the work is carried out.

Separating these concerns allows:

- simpler workers
- reusable execution logic
- independent scheduler scaling
- cleaner architecture

Workers never contain retry timing logic.

The Retry Scheduler never performs delivery.

Each component has a single responsibility.

---

## Why Retry Through the Normal Queue?

Retries are placed back onto the same notification queue used for initial delivery.

The worker therefore executes retries using exactly the same code path as the first delivery attempt.

This eliminates duplicated execution logic and ensures that every delivery attempt follows identical processing rules.

Workers do not distinguish between:

- an initial delivery
- a retry

They simply process the notification's current state.

---

## Why Providers Never Schedule Retries?

Providers are responsible only for communicating delivery outcomes.

A provider may report:

- success
- temporary failure
- permanent failure

The provider never decides:

- when to retry
- whether to retry
- how many retries should occur

Those decisions belong to the Retry Engine.

This keeps providers simple and ensures retry behaviour remains consistent across all providers.

---

## Why Retry State Lives on Notifications?

Retry information is stored directly on the Notification rather than in a separate Retry table.

A notification already represents the complete lifecycle of a delivery.

Keeping retry metadata alongside notification state avoids maintaining multiple synchronized records.

The notification itself always answers:

- current state
- current attempt count
- next retry time
- maximum retry attempts

Historical execution details remain in the immutable `delivery_attempts` table.

This separation provides both efficient scheduling and complete execution history.

---

## Why Delivery Attempts Are Immutable

Every provider execution creates a new Delivery Attempt record.

Existing attempts are never modified.

This provides:

- complete audit history
- deterministic debugging
- accurate operational metrics
- historical provider responses

The notification stores only the current lifecycle state.

Historical execution remains append-only.

---

## Why the Retry Engine Does Not Perform Recovery

The Retry Engine assumes notification state is already internally consistent.

Its responsibility begins only after retry intent has been persisted.

Recovering notifications that were interrupted before retry intent could be recorded is a different problem.

That responsibility belongs to the Recovery Engine.

Separating these responsibilities keeps both systems simpler and allows each subsystem to evolve independently.

---

# Future Improvements

The Retry Engine provides the foundation for additional capabilities planned for future releases.

Potential improvements include:

- configurable retry policies
- exponential backoff with jitter
- provider-specific retry strategies
- dead-letter queues
- retry metrics
- retry dashboards
- manual retry APIs
- priority-aware retry scheduling

These features build upon the existing retry architecture without requiring changes to its core execution model.

---

# Summary

The Retry Engine enables reliable, durable, and provider-independent retry execution.

Retry intent is persisted in PostgreSQL, discovered by the Retry Scheduler, and executed through the existing Notification Worker pipeline.

By separating retry scheduling from notification execution, Relays achieves a retry model that is resilient to worker crashes, Redis failures, and process restarts while remaining simple to reason about and extend.
