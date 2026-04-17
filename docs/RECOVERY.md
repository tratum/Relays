# Recovery and Reconciliation Model

---

## Purpose

This document defines the recovery and reconciliation model for Relays.

Recovery is responsible for restoring **eventual progress (liveness)** in the system when execution is interrupted due to crashes, queue loss, or partial failures, **without violating correctness guarantees.**

Recovery does **not** deliver notifications or decide outcomes. It exists solely to ensure that **valid notification intents eventually re-enter execution.**

---

## Core Principle

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

- Mark a notification as `sent` or `failed`
- Delete or modify delivery attempts
- Rewrite historical facts
- Bypass worker guard rails
- Perform irreversible side effects (e.g., sending email)

### Recovery does not guarantee uniqueness

Recovery may enqueue duplicate execution jobs.

This is acceptable because:

- The system uses at-least-once delivery semantics
- Workers always re-validate notification state from the DB
- Invalid executions are safely refused by guard rails

Recovery prioritizes restoring progress over minimizing duplicate scheduling.

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

- Re-enqueue notification immediately (respect next_retry_at semantics)
- Preserve `attempt_count` and `next_retry_at`
- Emit metric `reaper.reenqueue.retry_intent_missing`

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

- Enqueue notification for first execution (idempotent by notification id)
- Emit metric `reaper.reenqueue.never_queued`

**Rationale**

The notification intent is valid and durable.
API likely crashed after persistence; recovery completes enqueueing.

<br>

### Case 4: Redis Data Loss

**Condition**

- Partial/total Redis wipe detected externally OR large queue-size discrepancy observed

**Nature of the Failure**

- Queue execution lost
- No authoritative data loss

**Recovery Action**

- No special-case handling; covered by scanning DB for the cases above
- Covered implicitly by Full Reconciiation DB-driven recovery scans

**Rationale**

Redis is disposable by design.
Recovery always derives execution from DB state.

---

## Configurable Controls (Default Values)

These Environment-Configurable values are the defaults for first deploy. Should be adjusted after observing behaviour

- `PROCESSING_TIMEOUT` = 15m — duration after which processing is considered stuck.
- `QUEUE_GRACE_PERIOD` = 1m — grace before enqueuing created notifications.
- `RECOVERY_INTERVAL` = 5m — how often the reaper runs a pass.
- `REAPER_BATCH_SIZE` = 1000 — number of notifications scanned/enqueued per pass per predicate.
- `MAX_REENQUEUE_PER_RUN` = 10000 — safety cap to avoid floods.
- `REENQUEUE_DELAY_ON_DUPLICATE` = 30s — backoff if re-enqueueing finds Redis already holds jobs (prevent thundering herd).
- `ADVISORY_LOCK_KEY` = 12345 — used to ensure a single active reaper (Postgres advisory lock recommended).
- `STUCK_ALERT_THRESHOLD` = 0.5% — proportion of stuck notifications that triggers alerting (example threshold).

---

## Recovery Execution Model

**Who Runs Recovery ?**

- A dedicated reaper process (long-running) OR a scheduled job (cron/scheduler).
- Use a single active reaper pattern (Postgres advisory lock) to avoid concurrent conflicting runs.

**_Characteristics_**:

- Runs independently of workers
- Performs no delivery
- Performs no state transitions to terminal states

### Execution Frequency

- Default: every `RECOVERY_INTERVAL` (5 minutes).
- Use jitter to avoid coincidence with other periodic jobs.

Rationale:

- Recovery prioritizes safety over speed
- Aggressive recovery increases duplicate execution risk

### Candidate Selection Strategy

Recovery selects candidates using explicit DB predicates, never Redis state.

Selection is `index-backed` and scoped to non-terminal notifications only.

Index-backed selection ensures recovery scans only relevant subsets of notifications and never performs full table scans.

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

## Safety Mechanisms

### Worker re-validation

- Every worker must fetch the notification from DB and run guard rails before acting. Reaper relies on that invariant.

### Idempotency

- Jobs are idempotent by notification id. Workers must be safe to attempt a notification multiple times.

### Throttling and rate-limits

- Reaper must respect MAX_REENQUEUE_PER_RUN and per-notification re-enqueue caps (e.g., do not re-enqueue a single notification more than once per PROCESSING_TIMEOUT window).

### Avoiding thundering herd

- If re-enqueueing many notifications at once, add small randomized delays per job or chunk re-enqueues across the run.

### Metric & alerting

Emit metrics for:

- `reaper.scans.count`
- `reaper.reenqueue.count` (by reason)
- `reaper.lock_acquired` / `reaper.lock_failed`
- `notifications.stuck.count` (gauge)
- `notifications.pending_retry.count` (gauge)

Alerting examples:

- High rate of stuck notifications (e.g., > `STUCK_ALERT_THRESHOLD` of recent creations)
- Reaper failing to acquire lock repeatedly
- Reaper crash rate > X/day

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
- Duplicates are visible in `delivery_attempts`; acceptable under at-least-once semantics.

**Result:** Safe under at-least-once semantics

<br>

### Scenario 2: Recovery Re-Enqueues an Already Queued Notification

- Redis may contain duplicate jobs
- Workers fetch DB state before acting
- Invalid executions are refused

**Result:** No state corruption

### Scenario 3: Recovery Process Crashes Mid-Scan

- No DB mutation was performed and No state changes have occurred
- The run is idempotent and next scheduled run resumes.

**Result:** No permanent impact
