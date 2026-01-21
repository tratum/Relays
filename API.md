# API Contract

---

## Purpose

This document defines the **public HTTPS API contracts** for Relays.

Relays exposes a unified notification API that allows clients to submit notification intents via HTTP and query their delivery state.

This document specifies:

- Endpoints
- Request/response schemas
- Status codes
- Transport guarantees
- Explicit non-goals

It does **not** describe internal execution, retries, workers, or recovery.

---

## Design Principles

- API-first
- Asynchronous by default
- Channel-agnostic
- Extensible without breaking changes
- Minimal surface area for MVP

The API accepts _notification intent_, not delivery outcomes.

---

## Transport & Security

All API endpoints must be accessed over HTTPS.

```
https://api.relays.run
```

- Plain HTTP is not supported
- Requests over HTTP must be rejected or redirected at the load balancer / proxy layer
- TLS termination may occur at:
  - Reverse proxy (e.g., Nginx, Caddy)
  - Cloud load balancer
  - API gateway

**_HTTPS is required to protect notification payloads, metadata, and future authentication credentials._**

---

## Base URL & Versioning

All endpoints are versioned under:

```
https://api.relays.run/v1
```

because This Structure allows:

- clean versioning
- backwards-compatible evolution

---

## Core Concepts

A notification represents a delivery intent submitted by a client.

- One notification targets one recipient
- One notification uses one delivery channel
- A notification progresses through a lifecycle asynchronously

---

## API Endpoints

<br>

### 1. Notification Creation

<br>

#### **Endpoint**

<br>

```bash
POST https://api.relays.run/v1/notifications
```

<br>

#### **Request Body**

```json
{
  "channel": "email",
  "to": "user@example.com",
  "payload": {
    "subject": "Welcome",
    "body": "Hello! Welcome to Relays."
  },
  "metadata": {
    "source": "signup-service"
  }
}
```

| Field    | Type   | Required | Description                                          |
| -------- | ------ | -------- | ---------------------------------------------------- |
| channel  | string | yes      | Type of Delivery Channel (email, sms, webhook, etc.) |
| to       | string | yes      | Channel-Specific recipient identifier                |
| payload  | object | yes      | Channel-Specific delivery content                    |
| metadata | object | no       | Optional client-provided metadata                    |

<br>

#### **Channel: email (MVP)**

**Email Payload Schema**

```json
{
  "subject": "string",
  "body": "string"
}
```

**Validation Rules**

- `subject`: optional
- `body`: required, non-empty
- `to`: must be a valid email address

<br>

#### **Response**

<br>

1. **Success**

<br>

- Status Code

  ```bash
  201 Created
  ```

- Response Body
  ```json
  {
    "notification_id": "a3f5d9c8-1b2c-4d5f-9f77-0b1a2c3d4e5f",
    "state": "created"
  }
  ```

<br>

2. **Validation Error**

<br>

- Status Code
  ```bash
  400 Bad Request
  ```
- Response Body
  ```json
  {
    "error": {
      "code": "invalid_request",
      "message": "Invalid email address"
    }
  }
  ```

<br>

3. **Server Error**

<br>

- Status Code
  ```bash
  500 Internal Server Error
  ```
- Response Body

  ```json
  {
    "error": {
      "code": "internal_error",
      "message": "Unexpected error"
    }
  }
  ```

  <br>
  <br>

### 2. Get Notification Status

<br>

#### **Endpoint**

<br>

```bash
GET https://api.relays.run/v1/notifications/{notification_id}
```

<br>

#### **Request Body**

```json
{
  "notification_id": "a3f5d9c8-1b2c-4d5f-9f77-0b1a2c3d4e5f",
  "channel": "email",
  "to": "user@example.com",
  "state": "processing",
  "attempt_count": 2,
  "max_attempts": 5,
  "created_at": "2026-01-10T14:00:00Z",
  "last_attempt_at": "2026-01-10T14:20:00Z",
  "sent_at": null,
  "last_error": "SMTP 421 Temporary service unavailable"
}
```

<br>

#### **Response**

<br>

1. **Success**

<br>

- Status Code

  ```bash
  200 OK
  ```

- Response Body
  ```json
  {
    "notification_id": "a3f5d9c8-1b2c-4d5f-9f77-0b1a2c3d4e5f",
    "channel": "email",
    "to": "user@example.com",
    "state": "processing",
    "attempt_count": 2,
    "max_attempts": 5,
    "created_at": "2026-01-10T14:00:00Z",
    "last_attempt_at": "2026-01-10T14:20:00Z",
    "sent_at": null,
    "last_error": "SMTP 421 Temporary service unavailable"
  }
  ```

<br>

- Notes
  - **_200 OK is returned for any existing notification regardless of its lifecycle state_** ( created, queued, processing, sent or failed).
  - `last_error` is a concise, human-friendly summary of the most recent relevant failure. It should contain what you reliably know from the provider (never invent).
  - Full provider responses or large blobs belong in the delivery_attempts event log (see suggestion below), not in the main GET payload, to avoid bloat and leaking internals.

<br>

2. **Not Found**

<br>

- Status Code

  ```bash
  404 NOT FOUND
  ```

- Response Body
  ```json
  {
    "error": {
      "code": "not_found",
      "message": "Notification not found"
    }
  }
  ```

<br>

---

#### **Idempotency**

- Not supported in MVP.
- Duplicate HTTPS requests may create duplicate notifications.

#### **Authentication & Authorization**

- Currently Not implemented in MVP.
- HTTPS ensures transport security only, not identity.

#### **Rate Limiting**

- Currently Not implemented in MVP.
- Delivery Guarantees

#### **At-least-once delivery**

- Duplicate deliveries are possible
- No exactly-once guarantees

#### **Explicit Non-Goals (MVP)**

- No synchronous delivery
- No bulk notifications
- No scheduling API
- No cancellation API
- No provider selection

---

### Forward Compatibility Notes

The HTTPS API is intentionally designed to support:

- Multiple delivery channels
- API keys and auth headers
- Rate limiting
- Billing and usage tracking
- Webhook callbacks

All future changes must preserve:

- Existing paths
- Existing required fields
- Existing response shapes
