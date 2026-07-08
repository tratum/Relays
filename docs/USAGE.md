# Usage

---

# Purpose

This document describes how Relays records, aggregates, and exposes customer resource consumption.

The Usage subsystem provides the accounting foundation used by subscription management, quota enforcement, billing, and customer dashboards. Its primary responsibility is to maintain accurate usage counters for billable platform resources while remaining independent from pricing, subscription logic, and payment processing.

Usage records **accepted platform work**, not delivery outcomes. Once Relays successfully accepts a notification for asynchronous processing, the corresponding resource consumption is permanently recorded regardless of the eventual delivery result.

This document defines:

- Usage accounting principles
- Usage ownership and responsibilities
- Resource accounting model
- Counter architecture
- Recording workflow
- Integration with other platform subsystems

It intentionally does **not** describe:

- Subscription plans
- Pricing models
- Payment processing
- Quota policies
- Database implementation

Those concerns are documented separately in `BILLING.md`, `DATA_MODEL.md`, and future subscription documentation.

---

# Design Principles

The Usage subsystem is designed around several core principles.

## Usage Measures Platform Resource Consumption

Usage represents the amount of platform resources successfully accepted for processing by Relays.

Usage is **not** based on provider success, delivery outcomes, or retry attempts.

Once Relays accepts responsibility for processing a notification, the corresponding resource consumption is permanently recorded.

---

## Notification Acceptance Defines Usage

Usage is recorded immediately after a notification has been successfully validated, persisted, and accepted for asynchronous processing.

Recording usage at acceptance provides deterministic accounting while remaining independent from provider availability and downstream delivery outcomes.

Retries never affect usage because they represent additional processing of an already accepted notification rather than additional customer requests.

---

## Counters Over Events

The Usage subsystem maintains aggregated counters rather than recording immutable usage events.

This approach provides:

- Constant-time usage lookups
- Simple accounting
- Low storage overhead
- Efficient quota enforcement

Historical auditability is provided by the Notifications and Delivery Attempts domains, which already record the complete lifecycle of every accepted notification.

---

## Derived, Not Authoritative

Usage counters are derived data rather than the primary source of truth.

The authoritative history of customer activity is stored within the Notifications domain.

If usage counters ever become inconsistent, they can be reconstructed by replaying accepted notifications for the corresponding billing period.

This separation keeps the Usage subsystem lightweight while avoiding duplication of historical business data.

---

## Subscription Independence

The Usage subsystem records consumption for a billing period but does not own the lifecycle of that billing period.

Billing periods are defined and managed by the Subscription domain.

Usage simply records resource consumption against the billing period supplied by the platform.

This separation allows subscription policies to evolve independently without requiring changes to the accounting model.

---

## Resource-Agnostic Accounting

Usage accounting is independent of any individual notification channel.

Resources are identified using the platform's notification channel model, allowing future channels to participate in the same accounting workflow without architectural changes.

Current supported resources include:

- Email
- SMS
- Webhooks

Additional notification channels may be introduced without changing the accounting architecture.

---

# Core Concepts

The Usage subsystem revolves around four core concepts.

## Usage

Usage represents the amount of billable platform resources consumed by a workspace during a billing period.

Usage is recorded when Relays successfully accepts responsibility for processing a notification.

It is independent from notification delivery outcomes, provider availability, and retry attempts.

---

## Usage Counter

A Usage Counter is an aggregated measurement of resource consumption for a single workspace, resource type, and billing period.

Rather than storing every individual usage event, Relays maintains counters that are incremented as notifications are accepted.

Counters provide efficient lookups for quota enforcement, billing calculations, and customer dashboards while remaining reconstructable from the Notifications domain if necessary.

---

## Billing Period

A Billing Period defines the time window over which usage is accumulated.

Billing periods are owned by the Subscription domain rather than the Usage subsystem.

The Usage subsystem records consumption against the active billing period but does not determine when billing periods begin, end, or reset.

---

## Resource Type

Usage is tracked independently for each supported notification channel.

The platform currently supports:

- Email
- SMS
- Webhooks

Each notification increments the counter corresponding to its channel.

Future notification channels automatically participate in the same accounting model without requiring architectural changes.

---

# Responsibilities

The Usage subsystem is responsible for:

- Recording resource consumption for accepted notifications.
- Maintaining aggregated usage counters.
- Providing efficient retrieval of usage information.
- Supporting quota enforcement through accurate accounting.
- Providing the accounting foundation for subscription management and billing.
- Exposing usage information to customer-facing dashboards and administrative tooling.

The Usage subsystem intentionally focuses only on recording factual resource consumption.

---

# Non-Responsibilities

The Usage subsystem is intentionally **not** responsible for:

- Determining subscription plans.
- Managing billing periods.
- Calculating pricing.
- Generating invoices.
- Processing payments.
- Enforcing quota policies.
- Making authorization decisions.
- Inspecting notification delivery outcomes.
- Tracking retry attempts.
- Determining provider-specific behavior.

Those responsibilities belong to other platform subsystems.

Maintaining this separation keeps the accounting model simple, deterministic, and reusable across the platform.

---

# Usage Lifecycle

Every accepted notification contributes exactly one unit of usage.

The Usage subsystem records resource consumption during notification submission before the notification is enqueued for asynchronous processing.

Once recorded, usage remains immutable regardless of the eventual delivery outcome.

The conceptual lifecycle is:

```text
Notification Request
        │
        ▼
Validation
        │
        ▼
Persist Notification
        │
        ▼
Increment Usage
        │
        ▼
Commit Transaction
        │
        ▼
Queue Notification
        │
        ▼
Asynchronous Delivery
```

Recording usage before queueing ensures that accepted work is always accounted for, even if asynchronous processing is delayed or workers become temporarily unavailable.

Retries, provider failures, and permanent delivery failures do not modify previously recorded usage.

---

# Recording Workflow

Usage recording is part of the notification acceptance workflow.

Conceptually, the workflow is:

```text
Client Request
      │
      ▼
Validate Request
      │
      ▼
Persist Notification
      │
      ▼
Increment Usage Counter
      │
      ▼
Commit Database Transaction
      │
      ▼
Enqueue Notification
```

Usage recording and notification persistence occur within the same database transaction.

This guarantees that:

- A notification can never exist without corresponding usage accounting.
- Usage can never be recorded for a notification that failed validation or persistence.
- Notification acceptance and usage accounting remain strongly consistent.

Notification queueing occurs only after the transaction has successfully committed, preserving PostgreSQL as the platform's source of truth.

---

# Counter Model

The Usage subsystem stores aggregated counters rather than individual usage events.

Conceptually, each counter represents:

```text
Workspace
        │
        ▼
Billing Period
        │
        ▼
Notification Channel
        │
        ▼
Usage Count
```

This model provides efficient reads for quota enforcement, billing calculations, and customer dashboards while avoiding unnecessary duplication of historical notification data.

Historical accounting information remains available through the Notifications domain, allowing usage counters to be reconstructed if necessary.

The Usage subsystem therefore functions as a derived accounting layer rather than an immutable event store.

---

# Integration with Other Platform Subsystems

The Usage subsystem acts as the accounting foundation for several other platform components.

It records resource consumption but delegates all business decisions to higher-level domains.

```text
                  Notification Submission
                           │
                           ▼
                    Usage Recording
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
 Subscription        Quota Enforcement     Billing
        │                  │                  │
        └──────────────────┼──────────────────┘
                           ▼
                     Customer Dashboard
```

Each subsystem consumes usage information for a different purpose while the Usage subsystem remains responsible only for recording factual resource consumption.

---

## Notifications

The Notifications domain is responsible for initiating usage recording.

When a notification has been successfully validated and accepted for asynchronous processing, the Notification Submission workflow records usage as part of the same database transaction.

The Notifications domain remains the authoritative history of customer activity.

---

## Subscription

The Subscription domain owns billing periods and determines which billing period is currently active for a workspace.

Usage records resource consumption against the supplied billing period but never manages billing period lifecycles itself.

---

## Billing

The Billing subsystem consumes usage counters to calculate customer invoices and determine billable resource consumption.

Usage itself has no knowledge of pricing models, subscription plans, or payment providers.

---

## Quota Enforcement

Quota enforcement consumes usage information to determine whether a workspace has exhausted its allocated resources.

Usage provides accounting information only and never decides whether requests should be accepted or rejected.

---

## Customer Dashboard

Customer-facing dashboards retrieve aggregated usage counters to display current resource consumption, historical trends, and remaining quota.

The dashboard consumes usage information without requiring access to the underlying notification history.

---

# Failure Scenarios

The Usage subsystem is designed to remain deterministic under both expected and unexpected failures.

## Notification Validation Failure

If request validation fails, the notification is never persisted.

No usage is recorded.

---

## Database Transaction Failure

Notification persistence and usage recording occur within the same database transaction.

If the transaction rolls back, neither the notification nor its corresponding usage counter is committed.

This guarantees strong consistency between notification acceptance and usage accounting.

---

## Queue Failure

Usage is recorded before notification queueing.

If queueing fails after the transaction commits, the notification remains durably stored and usage remains correctly accounted for.

Recovery mechanisms are responsible for re-enqueueing stranded notifications.

---

## Worker Failure

Worker failures do not affect usage accounting.

Usage has already been recorded before asynchronous processing begins.

Worker recovery is handled independently by the Recovery subsystem.

---

## Provider Failure

Provider failures do not modify previously recorded usage.

The customer requested work that Relays accepted, and the platform consumed resources attempting delivery.

Retries and eventual delivery outcomes therefore have no impact on accounting.

---

## Counter Reconstruction

Usage counters are derived data.

If counters become inconsistent due to corruption or operational errors, they can be reconstructed by replaying accepted notifications for the corresponding billing period.

The Notifications domain remains the authoritative source of truth.

---

# Architectural Invariants

The following invariants define the accounting guarantees provided by the Usage subsystem.

- Every accepted notification increments usage exactly once.
- Notification retries never affect usage.
- Provider success or failure never affects usage.
- Usage is recorded synchronously with notification acceptance.
- Usage counters are derived data and may be reconstructed from Notifications.
- Billing periods are owned by the Subscription subsystem.
- Usage records facts but never makes business decisions.

---

# Future Evolution

The Usage subsystem has been intentionally designed to support future platform growth.

Potential future capabilities include:

- Additional notification channels
- Organization-level usage aggregation
- Historical usage reporting
- Usage forecasting
- Overage billing
- Cost analytics
- Customer usage exports

These capabilities can be introduced without changing the fundamental accounting model described in this document.

---

# Summary

The Usage subsystem provides deterministic accounting for platform resource consumption.

It records one unit of usage for every notification successfully accepted by Relays while remaining independent from delivery outcomes, retry behavior, pricing, subscriptions, and payment processing.

Usage maintains aggregated counters rather than immutable usage events, allowing efficient quota enforcement and billing while relying on the Notifications domain as the authoritative audit history.

This separation of responsibilities keeps accounting simple, deterministic, and extensible as the platform evolves.
