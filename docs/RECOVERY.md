# Recovery & Reconciliation

---

# Purpose

This document defines the purpose, scope, and design principles of the Recovery & Reconciliation subsystem in Relays.

Unlike the Retry Engine, which handles expected temporary delivery failures, the Recovery subsystem is responsible for restoring the system after unexpected infrastructure or process failures.

Recovery exists to ensure that notifications never become permanently stranded because of failures outside the normal delivery lifecycle.

> **Current Status**
>
> The Recovery & Reconciliation subsystem has **not yet been implemented**.
>
> This document serves as a design specification for future development and should not be interpreted as describing current system behaviour.

---

# Why Recovery Exists

Distributed systems fail in ways that normal business logic cannot anticipate.

Examples include:

- Worker process crashes
- Container termination
- Host machine failure
- Redis outages
- Database connection loss
- Network partitions
- Deployment interruptions

These failures may interrupt notification processing after work has already begun.

Unlike normal provider failures, these situations are not delivery outcomes.

They are infrastructure failures.

Recovery exists to detect and safely restore notifications affected by these failures.

---

# Retry Engine vs Recovery

The Retry Engine and Recovery subsystem solve fundamentally different problems.

## Retry Engine

The Retry Engine handles expected delivery failures returned by providers.

Examples include:

- Network timeout
- HTTP 429
- HTTP 503
- Temporary provider outage

The provider successfully returns a delivery outcome.

The worker persists retry intent.

The Retry Scheduler later re-enqueues the notification.

This is part of the normal notification lifecycle.

---

## Recovery

Recovery handles failures where the worker never finishes its execution.

Examples include:

- Worker crashes while processing a notification.
- Process is terminated during delivery.
- Host machine loses power.
- Container is killed unexpectedly.

In these situations no delivery outcome may have been persisted.

Recovery exists to identify these interrupted notifications and determine whether execution should continue.

---

# Design Principles

The Recovery subsystem will follow the same architectural principles as the rest of Relays.

---

## PostgreSQL Remains the Source of Truth

Recovery will never rely on Redis.

Recovery decisions will always be based on persisted notification state stored in PostgreSQL.

Redis is treated purely as an execution transport.

---

## Recovery Must Be Safe

Recovery must never increase the risk of duplicate notification delivery.

Whenever uncertainty exists, Recovery should prefer preserving correctness over maximizing throughput.

---

## Recovery Must Be Idempotent

Running Recovery multiple times should never corrupt notification state.

Repeated recovery executions should produce the same final result.

---

## Recovery Must Be Autonomous

Recovery should operate independently of API requests.

Recovery is a background operational subsystem responsible for maintaining system health.

---

# Failure Classes

The Recovery subsystem is intended to address failures that occur outside the normal notification lifecycle.

Potential failure classes include:

- Abandoned notifications stuck in `processing`.
- Notifications stranded because of unexpected worker termination.
- Notifications interrupted during infrastructure failures.
- Notifications requiring reconciliation after Redis failures.
- Notifications affected by unexpected deployment interruptions.

The exact handling strategy for each failure class will be defined during implementation.

---

# Recovery Responsibilities

When implemented, Recovery will be responsible for:

- Detecting notifications that require reconciliation.
- Determining whether interrupted work should continue.
- Restoring notifications to an executable state when safe.
- Maintaining notification lifecycle consistency.
- Preserving delivery correctness.

Recovery is an operational subsystem.

It is not responsible for normal notification delivery.

---

# Recovery Non-Responsibilities

Recovery will not:

- Send notifications directly.
- Communicate with external providers.
- Execute retry policy.
- Perform request validation.
- Modify delivery attempt history.
- Replace the Retry Engine.

Notification delivery will remain the responsibility of workers.

---

# Relationship with Workers

Workers execute notifications.

Recovery restores execution when workers cannot complete it.

This separation keeps worker logic focused exclusively on delivery while allowing Recovery to concentrate on infrastructure resilience.

---

# Relationship with the Retry Engine

The Retry Engine is responsible for expected delivery failures.

Recovery is responsible for unexpected infrastructure failures.

The two subsystems complement one another but solve different problems.

A temporary provider failure should never invoke Recovery.

Likewise, a worker crash should never be handled by the Retry Engine.

---

# Correctness Goals

When implemented, the Recovery subsystem should preserve the following system guarantees.

## Notification Integrity

Notifications should never become permanently stranded because of infrastructure failures.

---

## Delivery Correctness

Recovery should never knowingly introduce duplicate deliveries.

---

## Durable State

Recovery decisions should always be derived from durable state stored in PostgreSQL.

---

## Operational Visibility

Recovery actions should be observable through structured logging and operational metrics.

---

# Future Implementation

The Recovery subsystem has intentionally been deferred until after completion of the Notification Engine.

Future implementation work is expected to include:

- Recovery workflow implementation.
- Reconciliation algorithms.
- Failure detection policies.
- Operational metrics.
- Recovery scheduling.
- Administrative tooling.
- Comprehensive recovery testing.

These implementation details will be documented once development begins.

---

# Summary

Recovery is a planned operational subsystem responsible for restoring notification processing after unexpected infrastructure failures.

Unlike the Retry Engine, which handles expected provider failures as part of the normal notification lifecycle, Recovery is intended to reconcile interrupted execution caused by worker crashes, infrastructure outages, or other operational failures.

At the time of writing, Recovery has not yet been implemented. This document records the intended design goals and architectural boundaries for future development while clearly distinguishing them from the currently implemented Notification Engine.
