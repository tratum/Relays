# Worker Execution Model

---

# Purpose

This document defines the execution model, responsibilities, guarantees, and failure semantics of background workers in Relays.

Workers are responsible for executing notification delivery after a notification has been accepted by the API.

A worker is the only component in the system permitted to perform irreversible delivery side effects (sending notifications through external providers) and is therefore the sole owner of notification lifecycle transitions after submission.

This document intentionally focuses only on worker execution.

Retry scheduling is documented separately in **RETRY_ENGINE.md**.

Crash recovery and reconciliation are documented separately in **RECOVERY.md**.

---

# Core Design Principles

The worker architecture follows a small number of non-negotiable design principles.

These principles are more important than any individual implementation detail because they determine the correctness of the entire notification engine.

---

## 1. PostgreSQL is the Source of Truth

Workers never trust Redis.

Redis exists only to transport execution requests.

Every authoritative decision is derived from PostgreSQL.

This includes:

- Notification state
- Retry intent
- Delivery history
- Attempt counts
- Provider selection
- Notification payload

Even if Redis delivers duplicate jobs or loses queued jobs, PostgreSQL remains the authoritative representation of the notification lifecycle.

---

## 2. Workers Execute Intent

Workers never create notification intent.

That responsibility belongs to the Notification Submission workflow.

Workers execute notification intent that already exists.

The lifecycle therefore becomes:

```
Client

↓

Notification Submission

↓

Persist Notification

↓

Queue Notification

↓

Worker Execution
```

---

## 3. Workers Own Irreversible Side Effects

Sending a notification is an irreversible operation.

Once an external provider accepts delivery, the system can never "unsend" the notification.

Because of this, workers are the only component allowed to communicate with external providers.

No API endpoint, scheduler or recovery process is permitted to perform delivery.

---

## 4. Workers Own Lifecycle Transitions

Once a notification has been persisted, only workers are allowed to transition notification state.

Workers are responsible for moving notifications through their lifecycle.

```
created

↓

queued

↓

processing

↓

sent
```

OR

```
processing

↓

queued (retry)

↓

processing

↓

failed
```

No other subsystem may directly transition a notification into a terminal state.

---

## 5. Every Delivery Attempt is Immutable

Every attempt represents a historical fact.

Historical facts must never be rewritten.

Whether an attempt succeeds, fails permanently, or fails temporarily, a corresponding row is written to the `delivery_attempts` table.

This guarantees:

- Complete audit history
- Accurate debugging
- Operational visibility
- Reliable retry accounting

Workers append history.

They never rewrite history.

---

## 6. Providers Return Outcomes

Providers never modify notification state.

Providers communicate only one thing:

> The outcome of a delivery attempt.

Every provider returns a `ProviderResult`.

Workers interpret that result and decide what state transition should occur.

This separation ensures:

- Providers remain stateless.
- Retry policy remains provider-independent.
- Notification lifecycle remains centralized.

---

# Worker Responsibilities

Workers are responsible for:

- Receiving notification execution requests.
- Loading notification state from PostgreSQL.
- Validating delivery eligibility.
- Executing notification delivery.
- Recording immutable delivery attempts.
- Transitioning notification lifecycle state.
- Scheduling future retries when appropriate.
- Persisting delivery metadata.
- Emitting structured logs and operational metrics.

Workers own every state transition after notification submission.

---

# Worker Non-Responsibilities

Workers deliberately do **not** perform the following responsibilities.

## Authentication

Authentication is completed before notification persistence.

Workers never authenticate users or API keys.

---

## Request Validation

Workers never validate HTTP requests.

Notification payload validation has already been completed by the API layer.

Workers assume persisted notifications are structurally valid.

---

## Persistence of Notification Intent

Workers never create notifications.

Workers only execute notifications that already exist.

---

## Business Rules

Workers do not decide:

- Billing
- Quotas
- Rate limits
- Subscription plans
- Customer permissions

Those concerns belong to higher application layers.

---

## Recovery

Workers do not recover abandoned notifications.

Recovery is handled by the Recovery & Reconciliation subsystem.

Workers execute notifications.

Recovery restores execution.

---

# Worker Architecture

The execution pipeline is intentionally simple.

```
                PostgreSQL
                      ▲
                      │
                      │
                Notification
                 Submission
                      │
                      ▼
             NotificationQueue
                      │
                      ▼
                   Redis
                      │
                      ▼
              Channel Queue
                      │
                      ▼
              Celery Worker
                      │
                      ▼
           Notification Workflow
                      │
                      ▼
             Provider Registry
                      │
        ┌─────────────┴─────────────┐
        │                           │
        ▼                           ▼
 MailRelay Provider          Fake Provider
        │                           │
        └─────────────┬─────────────┘
                      ▼
               ProviderResult
                      │
                      ▼
        Persist Delivery Attempt
                      │
                      ▼
          Notification State Update
```

Every component has exactly one responsibility.

No component owns more than one concern.

---

# Worker Execution Flow

Each worker executes the following sequence.

## Step 1 — Receive Notification ID

Workers receive only a notification identifier.

Example:

```
Notification ID

↓

550e8400-e29b-41d4-a716-446655440000
```

The queue intentionally contains minimal information.

Workers never trust queue payloads.

---

## Why only the Notification ID?

Redis is treated as a best-effort execution mechanism.

Queue messages may be:

- duplicated
- delayed
- reordered
- replayed
- lost

Embedding notification state inside Redis would allow stale execution.

Instead, workers always reload the complete notification from PostgreSQL.

This guarantees every execution uses authoritative state.

---

## Step 2 — Load Notification

The worker loads the notification from PostgreSQL.

At this point the database becomes the only source consulted during execution.

No delivery decision is made using queue contents.

---

## Step 3 — Validate Delivery Eligibility

Before performing any irreversible action, the worker verifies that the notification may still be delivered.

Examples include:

- Notification exists.
- Notification is not already sent.
- Notification is not already failed.
- Retry limit has not been exceeded.
- Notification is eligible for execution.

If validation fails, execution stops immediately.

No external provider is contacted.

---

## Step 4 — Execute Provider

The worker selects the provider registered for the notification.

The provider performs the external delivery attempt.

Providers never update notification state.

Instead they return a `ProviderResult`.

```
Provider

↓

ProviderResult
```

This separation allows every provider to share the same execution model regardless of implementation.

---

# ProviderResult Contract

Workers never interpret provider-specific exceptions, HTTP status codes, or SDK responses directly.

Every provider is responsible for translating provider-specific behaviour into a common `ProviderResult`.

This allows the notification engine to remain completely provider-agnostic.

Every provider must return exactly one of three delivery outcomes.

```
SUCCESS

TEMPORARY_FAILURE

PERMANENT_FAILURE
```

Workers make all lifecycle decisions exclusively from these outcomes.

---

# Delivery Outcomes

Every delivery attempt produces one and only one outcome.

---

## Success

Meaning

The external provider successfully accepted the notification for delivery.

A successful attempt is terminal.

Required Actions

- Record a delivery attempt.
- Increment `attempt_count`.
- Transition notification state to `sent`.
- Persist `sent_at`.
- Do not schedule further retries.

Result

```
processing

↓

sent
```

---

## Temporary Failure

Meaning

The delivery failed for a reason that may succeed if attempted again later.

Examples include:

- Network timeout
- Connection failure
- Provider unavailable
- HTTP 429
- HTTP 503
- Temporary infrastructure failure

Required Actions

- Record a delivery attempt.
- Increment `attempt_count`.
- Compute the next retry time.
- Persist retry intent.
- Transition notification back to `queued`.

Result

```
processing

↓

queued

↓

(next_retry_at)
```

Temporary failures are non-terminal.

---

## Permanent Failure

Meaning

The notification can never succeed by retrying.

Examples include:

- Invalid recipient
- Unsupported payload
- Authentication failure
- Provider validation error

Required Actions

- Record a delivery attempt.
- Increment `attempt_count`.
- Persist failure reason.
- Transition notification to `failed`.

Result

```
processing

↓

failed
```

Permanent failures are terminal.

---

# Notification State Machine

Workers own every lifecycle transition after notification submission.

The complete state machine is shown below.

```
created

↓

queued

↓

processing

├──────────────┬──────────────────────┐
│              │                      │
│              │                      │
▼              ▼                      ▼

sent      queued (retry)          failed
               │
               ▼
          processing
```

The worker never skips intermediate states.

Every transition is explicitly persisted.

---

# Delivery Attempt Recording

Every execution attempt is durably recorded before the notification reaches a terminal or retry state.

Workers never modify previous attempts.

Each attempt becomes a permanent historical record.

A delivery attempt contains information such as:

- Notification ID
- Attempt number
- Provider
- Delivery status
- Provider message ID
- Provider error code
- Error message
- Raw provider response

The delivery history therefore represents the complete execution history of a notification.

Example

```
Attempt 1

↓

TEMPORARY_FAILURE

↓

Attempt 2

↓

TEMPORARY_FAILURE

↓

Attempt 3

↓

SUCCESS
```

Results in

```
delivery_attempts

1 → temporary_failure

2 → temporary_failure

3 → success
```

No rows are updated.

New rows are appended.

---

# Retry Scheduling

Workers do not perform delayed retries.

Instead, workers persist retry intent.

Retry scheduling consists of three steps.

```
ProviderResult

↓

TEMPORARY_FAILURE

↓

Compute next_retry_at

↓

Persist next_retry_at

↓

Transition state → queued
```

At this point the worker has completed its responsibility.

Execution ends.

A separate retry scheduler is responsible for re-enqueueing notifications once `next_retry_at` has been reached.

Separating retry scheduling from worker execution ensures that retries survive:

- Worker crashes
- Redis restarts
- Process restarts
- Container recreation

Retry intent is durable because it is stored inside PostgreSQL.

---

# Why Workers Never Sleep

Workers intentionally never wait for retry intervals.

This means workers never execute logic similar to:

```
sleep(60)

↓

retry()
```

Sleeping workers waste compute resources and prevent efficient scaling.

Instead, workers immediately persist retry intent and exit.

Later, the Retry Scheduler observes that retry time has arrived and creates a new execution request.

This keeps workers stateless and highly scalable.

---

# Worker Guard Rails

Before attempting delivery, every worker verifies that execution is still valid.

A worker must refuse execution if:

- Notification does not exist.
- Notification has already been sent.
- Notification has already failed.
- Maximum retry attempts have been exhausted.

These guard rails ensure duplicate queue messages cannot produce duplicate deliveries.

Because every worker revalidates state from PostgreSQL, duplicate Redis jobs are harmless.

---

# Concurrency Model

Multiple workers may execute concurrently.

Correctness is achieved by treating PostgreSQL as the authoritative execution coordinator.

Workers never coordinate through Redis.

Workers coordinate exclusively through persisted notification state.

This allows workers to scale horizontally without introducing distributed locking for normal execution.

Retry scheduling additionally uses row-level locking (`FOR UPDATE SKIP LOCKED`) to ensure retryable notifications are claimed by only one scheduler transaction.

---

# Provider Independence

Workers are intentionally unaware of provider-specific implementations.

The execution workflow remains identical regardless of provider.

```
Worker

↓

Provider

↓

ProviderResult

↓

Persist Result

↓

State Transition
```

Whether the provider is:

- MailRelay
- Amazon SES
- SendGrid
- SMTP
- Fake Provider

the worker executes exactly the same algorithm.

Adding a new provider therefore requires no changes to the worker execution model.

Only a new provider implementation is required.

---

# Worker Guarantees

Workers provide the following guarantees.

## Durable Execution History

Every delivery attempt is permanently recorded.

No attempt history is lost.

---

## Deterministic State Transitions

Notifications progress through a well-defined lifecycle.

Workers never perform implicit state transitions.

---

## Provider Independence

Workers execute providers through a common interface.

Provider-specific behaviour never leaks into worker logic.

---

## Retry Durability

Retry intent is persisted before execution completes.

Retries therefore survive infrastructure failures.

---

## At-Least-Once Delivery

Workers guarantee at-least-once execution.

Duplicate execution requests may occur.

Duplicate irreversible side effects are prevented through worker validation and persisted notification state.

Exactly-once delivery is intentionally not guaranteed.

---

# Summary

Workers are the execution engine of Relays.

They perform the only irreversible operation in the system: notification delivery.

Workers own notification lifecycle transitions, record immutable delivery history, persist retry intent, and execute providers through a provider-independent abstraction.

By separating execution from retry scheduling and treating PostgreSQL as the source of truth, workers remain stateless, horizontally scalable, and resilient to infrastructure failures.
