# Product Requirements Document

---

## 1. Problem Statement

Developers often need to send notifications (starting with email) reliably without blocking their primary application flow.

Relays provides a simple HTTP API that accepts notification requests, persists them durably, and delivers them asynchronously while exposing delivery state and failure information.

---

## 2. Goals

The MVP must:

- Accept email notification requests via HTTP APIs
- Notification requests must persist and be stored in the db before delivery to ensure it is not lost in case of failures
- Process delivery asynchronously using background workers
- Track and expose notification delivery status and attempt metadata
- Retry failed deliveries with backoff
- Record failure reasons for inspection and debugging

## 2.1 Notification Lifecycle (Conceptual)

Each notification progresses through a well-defined lifecycle:

- created (persisted in a db)
- queued (enqueued for background processing)
- processing (picked up by a worker)
- sent
- failed

Retries and delivery attempts are considered internal reliability mechanisms and do not affect usage accounting.

This lifecycle forms the core state machine of the system.

---

## 3. Non-Goals

The MVP will currently not:

- Support SMS or webhooks
- Provide a frontend UI or dashboard
- Enforce authentication or billing
- Support multiple regions or horizontal scaling
- Guarantee exactly-once delivery semantics
- Abstract multiple email providers

---

## 4. User Stories

### As a Developer:
- I want to submit an email notification request and get an immediate acknowledgment
- I want to query the status of a notification
- I want failed notifications to be retried automatically
- I want to know why a notification failed if it does

---

## 5. Functional Requirements

### Notification Submission
- Accept recipient, subject, body
- Validate input synchronously
- Persist request before enqueueing
- Return a notification ID immediately

### Asynchronous Processing
- Workers consume queued jobs
- Delivery attempts are recorded
- Retries use exponential backoff
- Max retry attempts are capped
- A notification must only transition to `sent` or `failed` after a corresponding delivery attempt is recorded

### Status Tracking
- Each notification has a lifecycle state derived from it's delivery attempt
- States must be queryable via API
- Failure metadata is persisted

---

## 6. Out-of-Scope (Deferred Explicitly)

- API key authentication
- Rate limiting
- Usage tracking
- Subscription plans
- Payment processing
