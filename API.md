# API Contract

## Purpose

This document defines the **public HTTPS API contracts** for Relays.

Relays exposes a unified notification API that allows clients to submit notification intents via HTTPS and query their delivery state.

This document specifies:

- Endpoints
- Request/response schemas
- Status codes
- Transport guarantees
- Explicit non-goals

It does **not** describe internal execution, retries, workers, or recovery.

<br>

## Design Principles

- API-first
- Asynchronous by default
- Channel-agnostic
- Extensible without breaking changes
- Minimal surface area for MVP

The API accepts _notification intent_, not delivery outcomes.

<br>

## Transport & Security

All API endpoints must be accessed over HTTPS.

```
https://api.relays.run
```

- Plain HTTP is not supported
- Requests over HTTP must be rejected or redirected at the load balancer / proxy layer
- TLS termination may occur at:
  - Reverse proxy (Caddy)
  - Cloud load balancer
  - API gateway

**_HTTPS is required to protect notification payloads, metadata, and future authentication credentials._**

<br>

## Base URL & Versioning

All endpoints are versioned under:

```
https://api.relays.run/v1
```

<br>

## Core Concepts

A notification represents a delivery intent submitted by a client.

- One notification targets **one recipient**
- One notification uses **one delivery channel**
- A notification progresses through a lifecycle asynchronously

## Request ID

Every error response includes a `request_id` field.

- Type: `UUID4`
- Generated per request
- Used for tracing, debugging, and support

Clients should log and surface this ID when reporting issues.

<br>

## API Endpoints

<br>

### 1. `POST` Notification Creation

<br>

#### Endpoint

<br>

```bash
POST https://api.relays.run/v1/notifications
```

<br>

#### Request Body

All channel-specific data (including recipient) is contained within the `payload`.

**Email Example**

```json
{
  "channel": "email",
  "payload": {
    "to": "user@example.com",
    "cc": [],
    "bcc": [],
    "subject": "Welcome",
    "body": "Hello! Welcome to Relays."
  },
  "metadata": {
    "source": "signup-service"
  }
}
```

---

**SMS Example**

```json
{
  "channel": "sms",
  "payload": {
    "to": "+919950649357",
    "message": "Hello! Welcome to Relays."
  },
  "metadata": {
    "source": "signup-service"
  }
}
```

---

**Webhook Example**

```json
{
  "channel": "webhook",
  "payload": {
    "url": "https://example.com/webhook",
    "body": {
      "event": "user.created"
    }
  }
}
```

<br>

#### Request Fields

| Field    | Type   | Required | Description                                  |
| -------- | ------ | -------- | -------------------------------------------- |
| channel  | string | yes      | Delivery channel (`email`, `sms`, `webhook`) |
| payload  | object | yes      | Channel-specific recipient and content       |
| metadata | object | no       | Optional client-provided metadata            |

#### Channel Payload Schemas

---

**Email Payload**

```json
{
  "to": "string",
  "cc": "string[]",
  "bcc": "string[]",
  "subject": "string",
  "body": "string"
}
```

**Validation Rules**

- `to`: required, valid email
- `cc`, `bcc`: optional arrays of valid emails
- `subject`: optional
- `body`: required, non-empty

---

**SMS Payload**

```json
{
  "to": "string",
  "message": "string"
}
```

**Validation Rules**

- `to`: required, valid E.164 phone number
- `message`: required, max length 160 characters

---

**Webhook Payload**

```json
{
  "url": "string",
  "body": "object"
}
```

**Validation Rules**

- `url`: required, valid HTTPS URL
- `body`: required JSON object

<br>

#### Response

---

**1. Success**

- Status Code

  ```bash
  201 Created
  ```

- Response Body

  ```json
  {
    "notification_id": "a3f5d9c8-1b2c-4d5f-9f77-0b1a2c3d4e5f",
    "state": "created",
    "created_at": "2026-04-11T05:48:52.592944Z"
  }
  ```

---

**2. Validation Error**

- Status Code

  ```bash
  400 Bad Request
  ```

- Response Body

  ```json
  {
    "error": {
      "code": "invalid_request",
      "message": "Invalid input",
      "request_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479"
    }
  }
  ```

---

**3. Server Error**

- Status Code

  ```bash
  500 Internal Server Error
  ```

- Response Body

  ```json
  {
    "error": {
      "code": "internal_error",
      "message": "Unexpected error",
      "request_id": "c9bf9e57-1685-4c89-bafb-ff5af830be8a"
    }
  }
  ```

---

### 2. `GET` Notification Status

#### Endpoint

```bash
GET https://api.relays.run/v1/notifications/{notification_id}
```

#### Path Parameters

| Name            | Type | Description             |
| --------------- | ---- | ----------------------- |
| notification_id | uuid | Notification identifier |

<br>

#### Response

---

**1. Success**

- Status Code

  ```bash
  200 OK
  ```

- Response Body

  ```json
  {
    "notification_id": "a3f5d9c8-1b2c-4d5f-9f77-0b1a2c3d4e5f",
    "channel": "email",
    "recipient": "user@example.com",
    "state": "processing",
    "attempt_count": 2,
    "max_attempts": 5,
    "created_at": "2026-01-10T14:00:00Z",
    "updated_at": "2026-01-10T14:20:00Z",
    "last_attempt_at": "2026-01-10T14:20:00Z",
    "sent_at": null,
    "last_error": "SMTP 421 Temporary service unavailable"
  }
  ```

<br>

**_Notes_**

- `200 OK` is returned for any existing notification regardless of lifecycle state
- `last_error` is a concise, human-readable failure summary
- Detailed provider responses belong in delivery_attempt logs

---

**2. Not Found**

- Status Code

  ```bash
  404 Not Found
  ```

- Response Body

  ```json
  {
    "error": {
      "code": "not_found",
      "message": "Notification not found",
      "request_id": "9a8b7c6d-1234-5678-9012-abcdefabcdef"
    }
  }
  ```

<br>

## Idempotency

- Not supported in MVP
- Duplicate requests may create duplicate notifications

## Authentication & Authorization

- Not implemented in MVP
- HTTPS ensures transport security only

## Rate Limiting

- Not implemented in MVP

## Delivery Guarantees

- At-least-once delivery
- Duplicate deliveries are possible
- No exactly-once guarantees

## Explicit Non-Goals (MVP)

- No synchronous delivery
- No bulk/multi-recipient notifications
- No scheduling API
- No cancellation API
- No provider selection

## Forward Compatibility Notes

The API is designed to support future additions:

- Multiple delivery channels
- API key authentication
- Rate limiting
- Billing and usage tracking
- Webhook callbacks

All future changes must preserve:

- Existing paths
- Required fields
- Response structure
