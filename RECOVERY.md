# Recovery and Reconciliation Model

## Purpose

This document defines the recovery and reconciliation model for Relays.

Recovery is responsible for restoring **eventual progress (liveness)** in the system when execution is interrupted due to crashes, queue loss, or partial failures, **without violating correctness guarantees.**

Recovery does **not** deliver notifications or decide outcomes. It exists solely to ensure that **valid notification intents eventually re-enter execution.**

---

## Core Principal

    PostgreSQL is the source of truth for both execution intent and recovery.

Redis is treated as a **best-effort execution mechanism**. Recovery is a **DB-driven reconciliation process** that restores execution when Redis or workers fails.

---

## Recovery Contract (Non-Negotiable Invariants)

Recovery logic MUST obey the following rules:

### **Recovery is allowed to:**

- Re-enqueue execution jobs
- Restore forward progress
- Reconcile DB intent with missing execution

### **Recovery is NOT allowed to:**

- Mark a notification as sent
- Mark a notification as failed
- Delete or modify delivery attempts
- Rewrite historical facts
- Bypass worker guard rails
- Perform irreversible side effects (e.g., sending email)

      **Recovery restores execution, not outcomes.**

All irreversible actions remain exclusively owned by workers.

---

## Recovery Trigger Conditions

Recovery is required when execution diverges from persisted intent.

The following states are considered _recoverable system failures_.

<br>

### Case 1: Notification Stuck in `processing`

**Condition**

- state = processing
- updated_at < now() - PROCESSING_TIMEOUT
- Notification is non-terminal

**Cause**

- Worker crashed after claiming the notification
- No further jobs exist for this notification

**Nature of the Failure**

- Liveness failure
- Correctness is preserved
- Progress is blocked

**Recovery Action**

- Re-enqueue the notification for execution
- Do not modify attempt history
- Worker will re-evaluate eligibility and retry safely

**Rationale**

The system intentionally avoids auto-resetting processing state during normal execution to prevent unsafe duplicate deliveries.
Recovery reintroduces execution only after sufficient time has passed to assume worker failure.

<br>

### Case 2: Retry Intent Exists but No Execution Job

**Condition**

- `state` is non-terminal
- `next_retry_at <= now()`
- Notification has no active job in Redis

**Cause**

- Worker crashed after persisting retry intent
- Redis lost delayed job
- Redis restart or data loss

**Nature of the Failure**

- _Execution loss_
- Intent is safely persisted

**Recovery Action**

- Re-enqueue notification immediately
- Preserve `attempt_count` and `next_retry_at`

**Rationale**

Retry intent is durable and authoritative in the DB.
Redis is only responsible for executing intent, not storing it.

<br>

### Case 3: Notification Created but Never Queued

**Condition**

- state = created
- `queued_at` IS NULL
- `created_at` < now() - QUEUE_GRACE_PERIOD

**Cause**

- API crashed after DB persistence
- Enqueue step never completed

**Nature of the Failure**

- Partial write failure
- No delivery attempt occurred

**Recovery Action**

- Enqueue notification for first execution
- Idempotent by notification ID

**Rationale**

The notification intent is valid and durable.
Recovery completes the missing execution step.

<br>

### Case 4: Redis Data Loss

**Condition**

- Redis queue is partially or fully wiped

**Nature of the Failure**

- Queue execution lost
- No authoritative data loss

**Recovery Action**

- No special-case handling required
- Covered implicitly by DB-driven recovery scans

**Rationale**

Redis is disposable by design.
Recovery always derives execution from DB state.

---

## Recovery Execution Model

**Who Runs Recovery ?**

Recovery is executed by a dedicated background recovery process (reaper).

**_Characteristics_**:

- Runs independently of workers
- Performs no delivery
- Performs no state transitions to terminal states

### Execution Frequency

- Periodic execution (e.g., every N minutes)
- Non-real-time by design

Rationale:

- Recovery prioritizes safety over speed
- Aggressive recovery increases duplicate execution risk

### Candidate Selection Strategy

Recovery selects candidates using explicit DB predicates, never Redis state.

Selection is `index-backed` and scoped to non-terminal notifications only.

Examples:

- Stuck processing older than timeout
- Retry-eligible notifications without execution
- Created notifications never queued

**_This reinforces the DB as the single source of truth._**

### Allowed Recovery Actions

For all recovery cases:

- Enqueue notification ID into Redis
- Do not modify lifecycle state directly
- Do not record delivery attempts

Workers remain responsible for:

- Guard rail validation
- State transitions
- Delivery execution
- Retry decisions

---

## Safety Guarantees & Trade-Offs

<br>

### Duplicate Execution Is Acceptable

Recovery may re-enqueue notifications that are already in-flight.

This is acceptable because:

- The system explicitly uses **at-least-once delivery semantics.**
- Workers enforce guard rails
- All attempts are recorded durably

<br>

### Why Recovery Does Not Corrupt State

- Recovery does not bypass worker validation
- Recovery does not write terminal states
- Recovery does not rewrite history
- Workers re-check eligibility on every execution

**_This Way Correctness is preserved even under duplicate scheduling._**

<br>

### Correctness vs Liveness Trade-Off

Relays intentionally prioritizes:

- **Correctness over liveness in real time**
- **Liveness over perfection eventually**

\*\*_This Way A notification may be delayed, but it will not be silently lost or incorrectly marked._

---

## Failure Scenarios

### Scenario 1: Recovery Runs While a Worker Is Processing

- Recovery may enqueue a duplicate job
- Worker guard rails prevent invalid state transitions
- Duplicate delivery attempts are possible
- All attempts are recorded

**Result:** Safe under at-least-once semantics

<br>

### Scenario 2: Recovery Re-Enqueues an Already Queued Notification

- Redis may contain duplicate jobs
- Workers fetch DB state before acting
- Invalid executions are refused

**Result:** No state corruption

### Scenario 3: Recovery Process Crashes Mid-Scan

- No state changes have occurred
- Recovery will resume in the next run

**Result:** No permanent impact
