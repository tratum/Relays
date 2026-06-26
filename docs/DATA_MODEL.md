# Data Model

---

# 1. Purpose

The Data Model defines the persistent data architecture of **Relays**.

It describes every durable business entity, its ownership, lifecycle, relationships, and the rationale behind the database design.

This document serves as the authoritative reference for how application data is organized within PostgreSQL.

It intentionally focuses on **data**, not implementation.

Topics such as API contracts, authentication workflows, worker execution, and deployment architecture are documented separately.

Related documents:

- `ARCHITECTURE.md`
- `AUTH.md`
- `API.md`
- `WORKERS.md`
- `RECOVERY.md`

---

# 2. Design Principles

The Relays database has been designed around a small number of architectural principles that guide every schema decision.

---

## PostgreSQL is the Source of Truth

PostgreSQL stores every piece of durable business data.

Examples include:

- Users
- Workspaces
- Sessions
- API Keys
- Notifications
- Delivery Attempts

If Redis were completely flushed, no business data should be permanently lost.

Redis is used only for infrastructure concerns such as queues and rate limiting.

---

## Business Domains Own Their Data

The schema is organized around business domains rather than technical concerns.

Each domain owns the lifecycle and validation rules for its entities.

Current domains include:

- Workspace
- Authentication
- API Keys
- Notifications
- Infrastructure

This ownership model mirrors the application modules and simplifies future service decomposition.

---

## Normalize Before Optimizing

The database favors normalization over premature denormalization.

Relationships are represented explicitly using foreign keys rather than duplicated data.

Additional denormalized structures should only be introduced after measurable performance requirements justify them.

---

## Database Constraints Protect Integrity

Business invariants should never rely solely on application code.

Whenever possible, PostgreSQL enforces correctness using:

- Primary Keys
- Foreign Keys
- Unique Constraints
- Check Constraints
- Partial Indexes

Application validation complements these constraints rather than replacing them.

---

## Immutable Where Practical

Many entities become immutable once created.

Examples include:

- Delivery Attempts
- Idempotency Records

Other entities evolve throughout their lifecycle.

Examples include:

- Notifications
- Sessions
- API Keys

Only mutable entities contain fields that change during normal operation.

---

## Auditability

Security-sensitive entities preserve historical information whenever practical.

Examples include:

- `consumed_at`
- `revoked_at`

These timestamps provide better traceability than immediately deleting records.

Temporary entities may still be removed later through scheduled cleanup processes.

---

# 3. Business Domains

The database is divided into independent business domains.

Each domain represents a distinct capability of the platform.

```text
Workspace
│
├── users
├── workspaces
└── workspace_members

Authentication
│
├── registration_otp
├── login_otp
└── sessions

API Keys
│
└── api_keys

Notifications
│
├── notifications
└── delivery_attempts

Infrastructure
│
├── idempotency_keys
└── schema_version
```

This organization mirrors the modular monolith architecture implemented by the application.

Each domain is responsible for the lifecycle of its own entities.

---

# 4. Entity Relationship Overview

The primary relationships between business entities are shown below.

```text
                              User
                                │
                                │
                   ┌────────────┴────────────┐
                   │                         │
                   ▼                         ▼
            Login OTP                   Sessions
                   │
                   │
                   ▼
          Workspace Membership
                   │
                   ▼
              Workspace
              │        │
              │        │
              ▼        ▼
         API Keys   Notifications
                           │
                           ▼
                  Delivery Attempts
```

Authentication entities remain isolated from business entities.

Notification ownership is established through the Workspace rather than individual users, ensuring that all billable resources remain tenant-scoped.

Infrastructure tables such as `idempotency_keys` and `schema_version` operate independently of business ownership.

---

# 5. Design Philosophy

The schema intentionally separates long-lived business entities from temporary operational entities.

Long-lived entities include:

- Users
- Workspaces
- Workspace Members
- API Keys
- Notifications

Temporary entities include:

- Registration OTP
- Login OTP
- Sessions
- Idempotency Records

This separation simplifies maintenance while allowing infrastructure data to evolve independently from customer-owned business data.

Similarly, ownership always follows business boundaries.

For example:

- Notifications belong to Workspaces.
- API Keys belong to Workspaces.
- Sessions belong to Users.
- OTPs belong to the Authentication domain.

This prevents unrelated modules from becoming tightly coupled and supports future extraction into independent services.

---

# 6. Workspace Domain

The Workspace domain defines the multi-tenant foundation of Relays.

Every customer resource ultimately belongs to a workspace. This ensures ownership, authorization, billing, and future collaboration features remain tenant-scoped rather than user-scoped.

During the current MVP, each user belongs to exactly one workspace.

```text
Users
   │
   ▼
Workspace Members
   │
   ▼
Workspaces
```

---

# Users

Represents an authenticated user within Relays.

| Property        | Value            |
| --------------- | ---------------- |
| **Domain**      | Workspace        |
| **Owner**       | Workspace Module |
| **Lifecycle**   | Long-lived       |
| **Primary Key** | `id (UUID)`      |

## Schema

| Column      | Type         | Nullable | Description               |
| ----------- | ------------ | -------- | ------------------------- |
| id          | UUID         | ❌       | Primary key               |
| email       | VARCHAR(255) | ❌       | Unique email address      |
| name        | VARCHAR(255) | ❌       | Display name              |
| is_verified | BOOLEAN      | ❌       | Email verification status |
| created_at  | TIMESTAMPTZ  | ❌       | User creation timestamp   |
| updated_at  | TIMESTAMPTZ  | ❌       | Last profile update       |

## Constraints

- Primary Key (`id`)
- Unique (`email`)

## Indexes

| Index            | Purpose                |
| ---------------- | ---------------------- |
| `uq_users_email` | Authentication lookups |

## Relationships

### Referenced By

- `login_otp.user_id`
- `sessions.user_id`
- `workspace_members.user_id`

## Design Notes

- Stores only user identity.
- Authentication state is stored separately.
- Workspace ownership is represented through `workspace_members`.
- Supports future multi-workspace users without schema changes.

---

# Workspaces

Represents a tenant within Relays.

Every customer account owns exactly one workspace. Business resources such as API Keys and Notifications belong to the workspace rather than individual users.

| Property        | Value            |
| --------------- | ---------------- |
| **Domain**      | Workspace        |
| **Owner**       | Workspace Module |
| **Lifecycle**   | Long-lived       |
| **Primary Key** | `id (UUID)`      |

## Schema

| Column     | Type               | Nullable | Description            |
| ---------- | ------------------ | -------- | ---------------------- |
| id         | UUID               | ❌       | Primary key            |
| name       | VARCHAR(255)       | ❌       | Workspace display name |
| slug       | VARCHAR(255)       | ❌       | Globally unique slug   |
| status     | `workspace_status` | ❌       | Workspace status       |
| created_at | TIMESTAMPTZ        | ❌       | Creation timestamp     |
| updated_at | TIMESTAMPTZ        | ❌       | Last update timestamp  |

## Constraints

- Primary Key (`id`)
- Unique (`slug`)

## Indexes

| Index                | Purpose                  |
| -------------------- | ------------------------ |
| `uq_workspaces_slug` | Workspace lookup by slug |

## Relationships

### Referenced By

- `workspace_members.workspace_id`
- `api_keys.workspace_id`

### Owns

- API Keys
- Notifications (logical ownership)

## Design Notes

- Defines the tenancy boundary of Relays.
- All billable resources belong to a workspace.
- Enables future support for teams, billing, organizations, and RBAC.

---

# Workspace Members

Associates users with workspaces.

This table models membership independently rather than embedding workspace ownership directly into the Users table.

| Property        | Value                     |
| --------------- | ------------------------- |
| **Domain**      | Workspace                 |
| **Owner**       | Workspace Module          |
| **Lifecycle**   | Long-lived                |
| **Primary Key** | `(workspace_id, user_id)` |

## Schema

| Column       | Type                    | Nullable | Description                   |
| ------------ | ----------------------- | -------- | ----------------------------- |
| workspace_id | UUID                    | ❌       | Referenced workspace          |
| user_id      | UUID                    | ❌       | Referenced user               |
| role         | `workspace_member_role` | ❌       | Member role                   |
| joined_at    | TIMESTAMPTZ             | ❌       | Membership creation timestamp |

## Constraints

- Composite Primary Key (`workspace_id`, `user_id`)
- One Owner per Workspace (`uq_workspace_single_owner`)

## Indexes

| Index                       | Purpose                                 |
| --------------------------- | --------------------------------------- |
| `idx_user_id`               | Lookup workspace for authenticated user |
| `uq_workspace_single_owner` | Ensures a single owner per workspace    |

## Relationships

### References

- `users.id`
- `workspaces.id`

## Design Notes

- Uses an association table instead of embedding `workspace_id` into `users`.
- Current MVP supports one workspace per user.
- Already supports future collaboration features with minimal schema changes.
- The partial unique index guarantees exactly one OWNER exists per workspace.

---

# 7. Authentication Domain

The Authentication domain is responsible for user authentication and session management.

Unlike the Workspace domain, these entities are operational rather than business entities. Most records are temporary and exist only for the duration of an authentication workflow.

```text
Registration OTP

Login OTP

Sessions
```

Authentication data is intentionally isolated from user identity. This separation simplifies future extraction into an independent Authentication Service.

---

# Registration OTP

Stores temporary OTPs used during the account registration process.

A registration OTP proves ownership of an email address before a user account is created.

| Property        | Value                 |
| --------------- | --------------------- |
| **Domain**      | Authentication        |
| **Owner**       | Authentication Module |
| **Lifecycle**   | Temporary             |
| **Primary Key** | `id (UUID)`           |

## Schema

| Column      | Type         | Nullable | Description             |
| ----------- | ------------ | -------- | ----------------------- |
| id          | UUID         | ❌       | Primary key             |
| email       | VARCHAR(255) | ❌       | Email being verified    |
| otp_hash    | TEXT         | ❌       | SHA-512 hash of the OTP |
| expires_at  | TIMESTAMPTZ  | ❌       | OTP expiration time     |
| consumed_at | TIMESTAMPTZ  | ✅       | Verification timestamp  |
| created_at  | TIMESTAMPTZ  | ❌       | Creation timestamp      |

## Constraints

- Primary Key (`id`)
- Unique (`email`)
- `expires_at > created_at`
- `consumed_at >= created_at`

## Indexes

| Index                         | Purpose                    |
| ----------------------------- | -------------------------- |
| `idx_registration_otp_active` | Lookup active OTP by email |

## Relationships

None.

Registration occurs before a User exists.

## Design Notes

- Stores only the OTP hash.
- One active registration OTP per email.
- Successful verification sets `consumed_at`.
- Expired and consumed OTPs are cleaned up periodically.

---

# Login OTP

Stores temporary OTPs used during user authentication.

Unlike Registration OTPs, Login OTPs reference an existing user.

| Property        | Value                 |
| --------------- | --------------------- |
| **Domain**      | Authentication        |
| **Owner**       | Authentication Module |
| **Lifecycle**   | Temporary             |
| **Primary Key** | `id (UUID)`           |

## Schema

| Column      | Type        | Nullable | Description                         |
| ----------- | ----------- | -------- | ----------------------------------- |
| id          | UUID        | ❌       | Primary key                         |
| user_id     | UUID        | ❌       | Referenced user                     |
| otp_hash    | TEXT        | ❌       | SHA-512 hash of the OTP             |
| expires_at  | TIMESTAMPTZ | ❌       | OTP expiration time                 |
| consumed_at | TIMESTAMPTZ | ✅       | Successful authentication timestamp |
| created_at  | TIMESTAMPTZ | ❌       | Creation timestamp                  |

## Constraints

- Primary Key (`id`)
- Unique (`user_id`)
- `expires_at > created_at`
- `consumed_at >= created_at`

## Indexes

| Index                  | Purpose                 |
| ---------------------- | ----------------------- |
| `idx_login_otp_active` | Lookup active login OTP |

## Relationships

### References

- `users.id`

## Design Notes

- Stores only the OTP hash.
- One active login OTP per user.
- OTPs are single-use.
- Successful authentication consumes the OTP before issuing tokens.

---

# Sessions

Represents authenticated user sessions backed by refresh tokens.

A session is created after successful login or registration and remains valid until expiration or revocation.

| Property        | Value                 |
| --------------- | --------------------- |
| **Domain**      | Authentication        |
| **Owner**       | Authentication Module |
| **Lifecycle**   | Revocable             |
| **Primary Key** | `id (UUID)`           |

## Schema

| Column             | Type        | Nullable | Description                   |
| ------------------ | ----------- | -------- | ----------------------------- |
| id                 | UUID        | ❌       | Primary key                   |
| user_id            | UUID        | ❌       | Session owner                 |
| refresh_token_hash | TEXT        | ❌       | SHA-512 hash of refresh token |
| expires_at         | TIMESTAMPTZ | ❌       | Session expiry                |
| revoked_at         | TIMESTAMPTZ | ✅       | Revocation timestamp          |
| created_at         | TIMESTAMPTZ | ❌       | Session creation timestamp    |

## Constraints

- Primary Key (`id`)
- Unique (`refresh_token_hash`)
- `expires_at > created_at`
- `revoked_at >= created_at`

## Indexes

| Index                       | Purpose                           |
| --------------------------- | --------------------------------- |
| `idx_sessions_active_users` | Lookup active sessions for a user |
| `idx_sessions_expiry`       | Cleanup expired sessions          |

## Relationships

### References

- `users.id`

## Design Notes

- Refresh tokens are never stored in plaintext.
- Only the cryptographic hash of the refresh token is persisted.
- Supports multiple concurrent sessions per user.
- Refresh token rotation updates the stored hash after every successful refresh.
- Sessions can be revoked independently without affecting other active sessions.
- Access tokens remain stateless and are therefore not stored in the database.

---

# 8. API Key Domain

The API Key domain enables machine-to-machine authentication.

Unlike user authentication, API Keys are intended for servers, applications, and automated systems interacting with the Relays API.

Each API Key belongs to exactly one workspace and inherits that workspace's permissions and ownership.

```text
Workspace
     │
     ▼
 API Keys
```

---

# API Keys

Represents an authentication credential for programmatic access to the Relays API.

| Property        | Value                 |
| --------------- | --------------------- |
| **Domain**      | API Keys              |
| **Owner**       | API Key Module        |
| **Lifecycle**   | Long-lived, Revocable |
| **Primary Key** | `id (UUID)`           |

## Schema

| Column       | Type             | Nullable | Description             |
| ------------ | ---------------- | -------- | ----------------------- |
| id           | UUID             | ❌       | Primary key             |
| workspace_id | UUID             | ❌       | Owning workspace        |
| name         | VARCHAR(100)     | ❌       | User-defined key name   |
| key_prefix   | VARCHAR(12)      | ❌       | Public identifier       |
| key_hash     | TEXT             | ❌       | SHA-512 hash of API key |
| status       | `api_key_status` | ❌       | Current key status      |
| expires_at   | TIMESTAMPTZ      | ✅       | Optional expiration     |
| last_used_at | TIMESTAMPTZ      | ✅       | Last successful usage   |
| revoked_at   | TIMESTAMPTZ      | ✅       | Revocation timestamp    |
| created_at   | TIMESTAMPTZ      | ❌       | Creation timestamp      |

## Constraints

- Primary Key (`id`)
- Unique (`key_prefix`)
- Unique (`workspace_id`, `name`)

## Indexes

| Index                           | Purpose                     |
| ------------------------------- | --------------------------- |
| `idx_api_keys_workspace`        | Lookup keys for a workspace |
| `idx_api_keys_workspace_active` | Lookup active keys only     |

## Relationships

### References

- `workspaces.id`

## Design Notes

- API Keys authenticate applications, not users.
- Only the key hash is stored in the database.
- The key prefix allows efficient lookup without exposing the secret.
- Keys may be revoked or expire independently.
- Multiple API Keys may exist per workspace.

---

# 9. Notification Domain

The Notification domain represents the core business capability of Relays.

Notifications describe delivery requests submitted by customers, while Delivery Attempts record each provider interaction performed by background workers.

```text
Notification
      │
      ▼
Delivery Attempts
```

---

# Notifications

Represents a notification submitted for asynchronous delivery.

A notification describes the intent to deliver a message rather than the outcome of delivery.

| Property        | Value               |
| --------------- | ------------------- |
| **Domain**      | Notifications       |
| **Owner**       | Notification Module |
| **Lifecycle**   | Long-lived          |
| **Primary Key** | `id (UUID)`         |

## Schema

| Column          | Type                 | Nullable | Description                   |
| --------------- | -------------------- | -------- | ----------------------------- |
| id              | UUID                 | ❌       | Primary key                   |
| channel         | TEXT                 | ❌       | Notification channel          |
| recipient       | TEXT                 | ❌       | Destination address           |
| payload         | JSONB                | ❌       | Channel payload               |
| metadata        | JSONB                | ❌       | Internal metadata             |
| state           | `notification_state` | ❌       | Current processing state      |
| attempt_count   | INTEGER              | ❌       | Number of delivery attempts   |
| max_attempts    | INTEGER              | ❌       | Maximum retry count           |
| next_retry_at   | TIMESTAMPTZ          | ✅       | Scheduled retry time          |
| queued_at       | TIMESTAMPTZ          | ✅       | Queue timestamp               |
| last_attempt_at | TIMESTAMPTZ          | ✅       | Last delivery attempt         |
| last_error      | TEXT                 | ✅       | Last provider error           |
| sent_at         | TIMESTAMPTZ          | ✅       | Successful delivery timestamp |
| created_at      | TIMESTAMPTZ          | ❌       | Creation timestamp            |
| updated_at      | TIMESTAMPTZ          | ❌       | Last update timestamp         |

## Constraints

- Primary Key (`id`)
- Various state validation constraints

## Indexes

| Index                      | Purpose               |
| -------------------------- | --------------------- |
| `idx_notification_channel` | Filter by channel     |
| `idx_notification_state`   | Worker processing     |
| `idx_notification_retry`   | Retry scheduling      |
| `idx_notification_created` | Chronological queries |

## Relationships

### Referenced By

- `delivery_attempts.notification_id`

## Design Notes

- PostgreSQL is the source of truth for notification state.
- Workers always reload notifications from PostgreSQL before processing.
- Retry scheduling is driven by `next_retry_at`.
- State transitions occur atomically within database transactions.
- Notification payloads are stored as JSONB to support multiple channels.

---

# Delivery Attempts

Records every provider delivery attempt performed for a notification.

A notification may produce multiple delivery attempts due to retries.

Delivery Attempts are append-only and provide a complete audit trail of delivery activity.

| Property        | Value               |
| --------------- | ------------------- |
| **Domain**      | Notifications       |
| **Owner**       | Notification Module |
| **Lifecycle**   | Append-only         |
| **Primary Key** | `id (UUID)`         |

## Schema

| Column            | Type              | Nullable | Description               |
| ----------------- | ----------------- | -------- | ------------------------- |
| id                | UUID              | ❌       | Primary key               |
| notification_id   | UUID              | ❌       | Parent notification       |
| attempt_number    | INTEGER           | ❌       | Sequential attempt number |
| status            | `delivery_status` | ❌       | Attempt outcome           |
| error_message     | TEXT              | ✅       | Provider error            |
| provider_response | JSONB             | ✅       | Raw provider response     |
| created_at        | TIMESTAMPTZ       | ❌       | Attempt timestamp         |

## Constraints

- Primary Key (`id`)
- Unique (`notification_id`, `attempt_number`)
- `attempt_number >= 1`

## Indexes

| Index                                | Purpose                            |
| ------------------------------------ | ---------------------------------- |
| `idx_delivery_attempts_notification` | Lookup attempts for a notification |

## Relationships

### References

- `notifications.id`

## Design Notes

- Delivery Attempts are immutable after creation.
- Every retry creates a new record.
- Historical attempts are never overwritten.
- Provider responses are preserved for debugging and auditing.
- Attempt numbering is guaranteed to be unique per notification.

---

# 10. Infrastructure Domain

The Infrastructure domain contains entities that support platform behavior but do not directly represent customer-owned business resources.

Unlike the other domains, these tables exist to improve reliability, consistency, and operational safety.

```text
Infrastructure
│
├── idempotency_keys
└── schema_version
```

---

# Idempotency Keys

Stores the execution state of idempotent API requests.

Idempotency ensures that retrying the same request produces the same result instead of executing the operation multiple times.

| Property        | Value               |
| --------------- | ------------------- |
| **Domain**      | Infrastructure      |
| **Owner**       | Core Infrastructure |
| **Lifecycle**   | Temporary           |
| **Primary Key** | `id (BIGINT)`       |

## Schema

| Column          | Type        | Nullable | Description            |
| --------------- | ----------- | -------- | ---------------------- |
| id              | BIGINT      | ❌       | Primary key            |
| idempotency_key | TEXT        | ❌       | Client supplied key    |
| request_hash    | TEXT        | ❌       | Canonical request hash |
| api_key_id      | BIGINT      | ❌       | Calling API Key        |
| method          | TEXT        | ❌       | HTTP method            |
| path            | TEXT        | ❌       | Request path           |
| notification_id | UUID        | ✅       | Created notification   |
| status          | TEXT        | ❌       | Processing state       |
| created_at      | TIMESTAMPTZ | ❌       | Creation timestamp     |
| expires_at      | TIMESTAMPTZ | ❌       | Expiration timestamp   |

## Constraints

- Primary Key (`id`)
- Unique (`api_key_id`, `method`, `path`, `idempotency_key`)
- Status limited to:

  - `processing`
  - `completed`
  - `failed`

## Indexes

| Index                    | Purpose                 |
| ------------------------ | ----------------------- |
| `idx_idempotency_lookup` | Fast request lookup     |
| `idx_idempotency_expiry` | Cleanup expired records |

## Relationships

### References

- `api_keys.id`

### References (Optional)

- `notifications.id`

## Design Notes

- Prevents duplicate execution of API requests.
- Stores a canonical request hash to detect payload mismatches.
- Processing state allows safe concurrent request handling.
- Expired records are periodically removed.

---

# Schema Version

Tracks applied database schema migrations.

This table is used exclusively by the migration runner during application startup.

| Property        | Value            |
| --------------- | ---------------- |
| **Domain**      | Infrastructure   |
| **Owner**       | Migration System |
| **Lifecycle**   | Permanent        |
| **Primary Key** | `version`        |

## Schema

| Column     | Type        | Nullable | Description               |
| ---------- | ----------- | -------- | ------------------------- |
| version    | INTEGER     | ❌       | Applied migration version |
| applied_at | TIMESTAMPTZ | ❌       | Migration timestamp       |

## Constraints

- Primary Key (`version`)

## Relationships

None.

## Design Notes

- Tracks which migrations have been successfully applied.
- Prevents duplicate migration execution.
- Used only during application startup.

---

# 11. Indexing Strategy

Indexes are created around application access patterns rather than every column.

The goal is to optimize the most frequently executed queries while minimizing unnecessary write overhead.

## Primary Keys

Every table uses a primary key index for efficient record retrieval.

---

## Unique Indexes

Unique indexes enforce business invariants such as:

- User email uniqueness
- Workspace slug uniqueness
- Refresh token uniqueness
- API Key prefix uniqueness
- API Key name uniqueness within a workspace
- One registration OTP per email
- One login OTP per user
- One owner per workspace
- One delivery attempt number per notification

---

## Partial Indexes

Several tables use partial indexes to optimize lookups on active records.

Examples include:

| Index                           | Predicate                     |
| ------------------------------- | ----------------------------- |
| `idx_login_otp_active`          | `consumed_at IS NULL`         |
| `idx_registration_otp_active`   | `consumed_at IS NULL`         |
| `idx_sessions_active_users`     | `revoked_at IS NULL`          |
| `idx_api_keys_workspace_active` | `status = 'ACTIVE'`           |
| `idx_notification_retry`        | Retryable notification states |

Partial indexes reduce index size while improving query performance.

---

## Lookup Indexes

Lookup indexes support high-frequency application queries.

Examples include:

| Index                                | Usage                  |
| ------------------------------------ | ---------------------- |
| `uq_users_email`                     | User authentication    |
| `idx_user_id`                        | Workspace lookup       |
| `idx_notification_state`             | Worker processing      |
| `idx_notification_channel`           | Channel filtering      |
| `idx_delivery_attempts_notification` | Delivery history       |
| `idx_idempotency_lookup`             | Idempotency validation |

---

# 12. Data Integrity

Relays relies on PostgreSQL to enforce data correctness wherever possible.

Application validation alone is insufficient to guarantee consistency under concurrent workloads.

The schema therefore uses multiple layers of protection:

- Primary Keys
- Foreign Keys
- Unique Constraints
- Check Constraints
- Partial Unique Indexes

Business workflows complement these guarantees but never replace them.

---

# 13. Future Schema Evolution

The current schema is intentionally conservative and designed to support future platform growth.

Potential additions include:

## Workspace

- Workspace invitations
- Team management
- Organization hierarchy
- Custom roles

## Authentication

- Multi-factor authentication
- Session metadata
- Trusted devices
- OAuth providers

## Notifications

- Scheduled notifications
- Notification templates
- Provider routing rules
- Delivery webhooks

## Billing

- Subscription plans
- Usage records
- Invoices
- Payment history

## Audit

- Audit logs
- Security events
- Activity history

The existing domain boundaries have been designed to accommodate these additions with minimal schema changes while preserving clear ownership and separation of concerns.
