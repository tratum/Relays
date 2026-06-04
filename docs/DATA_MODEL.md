# Data Model

---

This Document defines the Persistent Data Model for ***Relays***.

**PostgresSQL is the Source of Truth** for all notification states

The DB consists of Two core tables:

* **notifications** — current state and scheduling summary (the entity)

* **delivery_attempts** — append-only history of attempts (the events)

## Notifications Table

### **Purpose**

  - Stores Notifications and their lifecycle state
  - Stores Retry Count and Scheduling Information

### **Columns**

<br>

| Column          | Type                                            | Default / Nullable | Description                                          |
| --------------- | ----------------------------------------------- | ------------------ | ---------------------------------------------------- |
| id              | uuid                                            | NOT NULL           | Primary key for the notification                     |
| channel         | text                                            | NOT NULL           | Delivery channel (`email`, `sms`, `webhook`)         |
| recipient       | text                                            | NOT NULL           | Channel-specific recipient identifier                |
| payload         | jsonb                                           | NOT NULL           | Channel-specific delivery content                    |
| state           | enum(created, queued, processing, sent, failed) | created            | Current lifecycle state                              |
| attempt_count   | integer                                         | 0                  | Number of delivery attempts made                     |
| max_attempts    | integer                                         | 5                  | Maximum allowed delivery attempts                    |
| next_retry_at   | timestamptz                                     | NULL               | Time when next retry should occur                    |
| queued_at       | timestamptz                                     | NULL               | Time when job was enqueued in Redis                  |
| last_attempt_at | timestamptz                                     | NULL               | Time of the most recent delivery attempt             |
| last_error      | text                                            | NULL               | Last failure reason (human-readable)                 |
| sent_at         | timestamptz                                     | NULL               | Time when delivery succeeded                         |
| created_at      | timestamptz                                     | now()              | Notification creation time                           |
| updated_at      | timestamptz                                     | now()              | Timestamp of the most recent modification to the row |
| metadata        | jsonb                                           | NULL               | Optional extensible metadata                         |

<br>

### **State Transitions**:

```
- created (API accepted intent)  --->  queued (work is scheduled)

- queued  --->  processing (worker picks it up)

- processing  --->  sent  or  processing  ---> failed

- processing  --->  processing (retry)
```

What does `created` means ?

* The API has validated the request
* The notification record has been written in DB
* Redis may or may not have a corresponding job yet

What does `queued` mean ?

* The system has scheduled work
* No worker has claimed responsibility yet

What does `processing` mean ?

* A worker has authoritatively claimed the notification
* Work is in progress
* This claim is durable

### **Ownership**:

* **API**

  * Creates notification
  * Enqueues first job

* **Worker**

  * Updates lifecycle state
  * Attempts retry and Increments attempt count
  * Calculates backoff and retry scheduling
  * Writes terminal states (Terminal States are SENT and FAILED)

<br>

### ***Sample Data***

| Column          | Value                                                    |
| --------------- | -------------------------------------------------------- |
| id              | a3f5d9c8-1b2c-4d5f-9f77-0b1a2c3d4e5f                     |
| channel         | email                                                    |
| recipient       | [user@example.com](mailto:user@example.com)              |
| payload         | {"subject":"Welcome","body":"Hello! Welcome to Relays."} |
| state           | processing                                               |
| attempt_count   | 2                                                        |
| max_attempts    | 5                                                        |
| next_retry_at   | 2026-01-10T15:30:00+05:30                                |
| queued_at       | 2026-01-10T14:10:00+05:30                                |
| last_attempt_at | 2026-01-10T14:20:00+05:30                                |
| last_error      | SMTP 421 Temporary service unavailable                   |
| sent_at         | NULL                                                     |
| created_at      | 2026-01-10T14:00:00+05:30                                |
| updated_at      | 2026-01-10T14:20:00+05:30                                |
| metadata        | {"source":"signup-service"}                              |

<br>

## Delivery Attempts Table

### **Purpose**

  - Stores immutable records of delivery attempt
  - Stores failure metadata and success/failure lifecycle states

### **Columns**

<br>

| Column            | Type                                                | Default / Nullable | Description                                 |
| ----------------- | --------------------------------------------------- | ------------------ | ------------------------------------------- |
| id                | uuid                                                | NOT NULL           | Primary key for the delivery_attempts table |
| notification_id   | uuid                                                | NOT NULL           | Foreign key to notifications.id             |
| attempt_number    | integer                                             | NOT NULL           | Sequential attempt number (1-based)         |
| status            | enum(success, temporary_failure, permanent_failure) | NOT NULL           | Outcome of attempt                          |
| error_message     | text                                                | NULL               | Failure reason                              |
| provider_response | jsonb                                               | NULL               | Raw provider response                       |
| created_at        | timestamptz                                         | NOT NULL, now()              | Time when attempt occurred                  |

<br>

### **Characteristics**:

- Append Only
- Never Updated after insert

<br>

### ***Sample Data***

**Attempt 1**

<br>

| Column            | Value                                |
| ----------------- | ------------------------------------ |
| id                | 11111111-2222-3333-4444-555555555555 |
| notification_id   | a3f5d9c8-1b2c-4d5f-9f77-0b1a2c3d4e5f |
| attempt_number    | 1                                    |
| status            | temporary_failure                    |
| error_message     | Timeout connecting to provider       |
| provider_response | {"timeout_ms":30000}                 |
| created_at        | 2026-01-10T14:05:00+05:30            |

<br>

**Attempt 2**

<br>

| Column            | Value                                  |
| ----------------- | -------------------------------------- |
| id                | 66666666-7777-8888-9999-000000000000   |
| notification_id   | a3f5d9c8-1b2c-4d5f-9f77-0b1a2c3d4e5f   |
| attempt_number    | 2                                      |
| status            | temporary_failure                      |
| error_message     | SMTP 421 Temporary service unavailable |
| provider_response | {"smtp_code":421}                      |
| created_at        | 2026-01-10T14:20:00+05:30              |

<br>

## **Indexes & Constraints**

- `notifications.id` - PRIMARY KEY
- `delivery_attempts.id` - PRIMARY KEY
- FOREIGN KEY `delivery_attempts.notification_id` REFERENCES `notifications.id` and ON DELETE RESTRICT is selected to preserve delivery history (meaning we can't delete a notification if it has delivery attempts left).
- `delivery_attempts.notification_id` and `delivery_attempts.attempt_number` should be UNIQUE
- INDEX on `notifications.state`
- INDEX on `notifications.channel`
- PARTIAL INDEX on `notifications.next_retry_at` (Create Index on next_retry_at where state is created queued or processing as sent or failed doesn't need retries)
- INDEX on `delivery_attempts.notification_id`
- INDEX on `notifications.created_at` (optional, can be used for listing)
- CONSTRAINTS:

  - CHECK (attempt_count >= 0)
  - CHECK (max_attempts >= 0)
  - CHECK (attempt_number >= 1) on delivery_attempts

<br>

---
