# Worker Execution Model

---

Side Note:

1. What is a Worker in Relays ?

   A worker is a background process that reads notification state from the DB and is responsible for attempting delivery, recording outcomes, and moving notifications through their lifecycle.

   A worker is the only component in the system allowed to perform Notification Delivery and transitions notification into their final states

2. What does a Worker recieve and why ?

   A worker recieves minimal job payload i.e. notification id because Redis Jobs are unreliable hints not trusted data. The worker must always fetch the full notifications from the DB which is the Source of Truth, to guard against stale, duplicated or replayed jobs.

3. What is the very first database interaction the worker must perform, and why must it happen before any side effects ?

   The First interaction a worker must perform is a read of the notification record from PostgresSQL to determine the current authoritative state before performing any state transition or side effects.

4. At what exact moment does the worker “claim” a notification, and how is that claim made durable ?
   A worker claims a notification by transitioning it's state from a non-terminal state to `processing` in the DB, making the claim durable and observable.

5. What is the irreversible side effect/action in the worker flow, and what conditions must be true before it's allowed to happen ?

   The irreversible side-effect is the external delivery attempt (sending notification via External Providers). Before permforming this action, the worker must have authoritatively claimed the notification by transitioning it to `processing` in the DB and verified that the notification is eligible for delivery

6. Why must every delivery attempt be recorded durably, even when the system intends to retry or ultimately fail the notification ?

   Every Delivery attempt must be recorded as an immutable event because attempts represent historical facts about what actually happened in the system and correctness, debugging and recovery depends on a complete and durable attempt history.

<br>

---

## Purpose

This document defines the **execution model**, **responsibilites** and **failure behaviour** of background workers in Relays.

Workers are responsible for fetching jobs, performing delivery, handling retries and updating notification lifecycle state

<br>

---

## Worker Responsibilites

Workers are the Authoritative executors of irreversible delivery side effects and the sole owners of notification lifecycle transitions, including all terminal states, with PostgresSQL as the source of truth

Workers are responsible for:

- Receive job reference (notification id) from the redis queue
- Load notification from db
- Validate eligibility (Must Pass the Guard Rails)
- Transition State to `processing`
- Attempting notification delivery
- Recording a row in delivery_attempts table in DB
- On Success: mark notification state as `sent` and write the `sent_at` value
- On Failure: incremet `attempt_count`, compute next_retry_at and either requeue or mark `failed` if exhausted
- Emit Metrics and structured logs

<br>

---

## Non-Responsibilities

- Workers do not own:
  - Validation
  - Authentication
  - Persistence of Initial Intent
- Workers do not store truth outside of db
- Workers do not decide quotas, pricing and customer-facing rules
- Workers do not accept user requests

<br>

---

## Guard Rails

A worker must refuse to process a job if any of the following conditions are true

- The notification does not exist
- The notification is already in the `processing` state
- The notification is already in a terminal state (sent/failed)
- The notification has exhausted it's maximum attempts
- A retry is scheduled for the future (now < next_retry_at)

---

## Worker Flow

After an attempt is made, the worker evaluates the outcome not the state. There are only **3 Meaningful Outcomes** of an Attempt:

1. Success

Meaning:

- The external provider accepted and completed the delivery
- No further attempts are needed or allowed

Required Actions:

- Transition notification state to `sent`
- Persist sent_at
- Do not enqueue further jobs

This is a **Terminal Decision**

2. Retryable Failure

Meaning:

- The Failure is transient
- Another attempt might succeed later
- Re-Enqueueing is only applicable for this outcome

Required Actions:

- Increment attempt_count
- Compute next retry time (Backoff)
- Persist retry intent (next_retry_at)
- Re-Enqueue a Job (Delayed)

This is a **Non-Terminal Decision**

3. Non-Retryable Failure

Meaning:

- Further Attempts are pointless or dangerous
- Retry limits are exhausted or
- Failure is permanent by nature

Examples:

- invalid email address
- authentication failure
- policy violation

Required Actions:

- Transition notification state to `failed`
- Persist Failure Reason
- Don not enqueue further jobs

This is a **Terminal Decision**

<br>

---

## Retry Intent vs Retry Mechanism

### Why Retry Intent must be stored in the DB ?

The DB is :

- Authoritative
- Durable
- Crash Resistant
- Queryable

By Storing Retry Intent in the DB

- Retries survive worker crashes
- Retries survives redis restarts
- Retries can be inspected and audited
- Retry limits are enforcable

That's why Database stores intent and queues execute intent

<br>

---

## Failure Scenarios

Below given are Failures at every critical point:

1. Failure before Delivery Attempt

   **Where the Failure Happens ?**
   - Job picked from redis
   - Notifications Loaded
   - Possibly transitioned to `processing` state
   - No email sent yet

   **System State**
   - No Delivery Attempt Recorded
   - Notification is Non-Terminal

   **Why this is Safe ?**
   - No irreversible action occured
   - Workers can retry safely
   - Duplicate Jobs cause no harm

   **Guarantees**

   At Least Once Excecution without duplicate side-effects

<br>

2. Failure After Delivery Attempt, Before DB Update

   **Where the Failure Happens ?**
   - Email Sent to Provider
   - Worker crashes before recording attempt or updating state

   **System State**
   - Email amy or may not have been delivered
   - DB does not reflect the delivery attempt yet

   **Why this is Acceptable ?**
   - Ambiguity is unavoidable in distributed systems
   - Retries may cause duplicate delivery
   - System explicitly allows at-least-once delivery

   **Guarantees**

   No Message Loss, but may have possible duplicates

3. Failure After Recording Attempt, Before Decision

   **Where the Failure Happens ?**
   - Delivery Attempt is recorded
   - No State Transition Yet

   **System State**
   - Historical Facts exists
   - Notification remains retryable

   **Why this is Safe ?**
   - Attempt History is Preserved
   - Worker can re-evaluate outcome
   - Retry Logic remains consistent

   **Guarantees**

   No unexplained State Transitions

<br>

4. Failure after Decision, Before Re-Enqueue

   Here decision can be
   - Success
   - Retryable Failure
   - Non-Retryable Failure

   **Where the Failure Happens ?**
   - The Worker has recorded the delivery attempt
   - Written the retry decision to db
   - Before the worker could enqueue a new job in redis, it crashes

   **System State**
   - Retry Intent exists in DB
   - No Execution Scheduled Yet

   **Why this is Safe ?**
   - Retry Intent is durable
   - Recovery logic can enqueue missing jobs

   **Guarantees**

   Retry Intent is never lost

<br>

5. Two Workers read the same notification before either writes `processing`

   **Where the Failure Happens ?**
   - Two Workers recieve duplicate jobs from Redis
   - Both Workers read the notification when it is in a non-terminal, non-processing state
   - Neither Worker has yet transitioned the state to `processing`

   **System State**
   - Both Workers believe that the notification is eligible
   - Both may attempt to transition state and attempt delivery

   **Why this is Acceptable ?**
   - Duplicate Delivery attempts may occur
   - At-least-once delivery semantics allow duplicate external deliveries in rare failure scenarios.

   **Guarantees**
   - This race condition is **explicitly allowed** under at-least-once delivery semantics
   - All Delivery Attempts are recorded durably
   - Only valid state transitions are persisted
   - No Notification state becomes corrupted

   **Design Trade-Offs**
   - This Scenario could be prevented by using database-level locking when reading notifications, ensuring that only one worker can claim a notification at a time
   - However this approach is intentionally not used because it reduces Throughput which limits parralelism and becomes a bottleneck under load
   - Increases Failure Coupling i.e. if a worker crashes while holding a lock, other workers are blocked thereby turning a single-worker failure into a system-wide slowdown

<br>

6. Redis Data Loss

   **Where the Failure Happens ?**
   - Redis loses jobs entirely

   **System State**
   - Notification intent and retry intent still exists in the DB

   **Why this is Safe ?**
   - Redis is Disposable
   - Jobs can be regenerated from the DB States

   **Guarantees**

   No Notification Loss

<br>

7. Worker Crashes and notification stays in processing forever

   **Where the Failure Happens ?**
   - Worker successfully transitions notification state to processing
   - Worker crashes before completing delivery and before transitioning to a terminal state
   - No Further Jobs are enqueued for this Notification

   **System State**
   - Notification stays in `processing`
   - Delivery Attempts may or may not have been recorded (depends on crash point)
   - No worker will pick this notification automatically

   **Why this is Dangerous ?**
   - The notification may never make forward progress
   - The System appears `stuck` for this notification
   - This is a liveness problem and not a correctness problem

   **Guarantees**
   - No Incorrect Deliveries Occur
   - No State Corruption occurs

   **Design Trade-Offs**
   - A notification may remain in the `processing` state if a worker crashes after claiming ownership but before completing delivery or transitioning to a terminal state.
   - This scenario represents a liveness concern rather than a correctness issue.
   - The system intentionally does not automatically override the `processing` state to avoid unsafe duplicate deliveries. Instead, eventual progress can be restored through a separate recovery mechanism (e.g., a reaper or watchdog process) that detects notifications stuck in `processing` beyond a defined timeout and safely re-enqueues them.
   - The Plan to add a Recovery Mechanism is Deferred Explicitly

**Correctness is preserved but eventual progress requires a Recovery Mechanism**
