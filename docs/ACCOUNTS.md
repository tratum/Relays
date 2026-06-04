# Account Design

---

# 1. Purpose

This document defines the account, workspace, authentication, authorization, onboarding, and tenancy architecture for Relays.

The objective is to provide:

- Simple onboarding
- Secure authentication
- Team collaboration support
- Workspace-based tenancy
- Clear ownership model
- Minimal MVP complexity
- Future scalability

---

# 2. Design Principles

Relays is a developer-focused notification infrastructure platform.

The account system should:

- Minimize onboarding friction
- Avoid password management complexity
- Support future team collaboration
- Support future billing and subscriptions
- Keep the MVP implementation simple
- Remain extensible for future requirements

---

# 3. Core Concepts

## User

A User represents an individual identity.

Examples:

- Founder
- Developer
- DevOps Engineer
- Team Member

Users authenticate using email OTP.

---

## Workspace

A Workspace represents the customer account and tenant boundary.

All platform resources belong to a Workspace.

Examples:

- API Keys
- Notifications
- Usage Counters
- Subscription
- Team Members

Workspace is the primary tenant entity in Relays.

---

## Membership

A Membership connects a User to a Workspace and defines their role.

Supported Roles:

- OWNER
- MEMBER

---

# 4. Tenant Model

## Decision

Relays uses:

- Shared Database
- Shared Schema
- Workspace-Based Multi-Tenancy

All tenant-owned resources contain:

- workspace_id

for data isolation.

---

## Tenant Hierarchy

Workspace
├── Members
├── Subscription
├── API Keys
├── Notifications
├── Usage Counters
└── Future Resources

---

# 5. Authentication

## Authentication Method

Relays uses:

Email One-Time Password (OTP)

The following are not included in MVP:

- Google Login
- GitHub Login
- SAML SSO
- OIDC SSO
- Password Authentication

---

## OTP Requirements

OTP Length

- 6 Digits

OTP Expiry

- 10 Minutes

Maximum Verification Attempts

- 5

OTP Storage

- Redis

OTP Persistence

- Temporary Only

Expired OTPs are automatically removed using Redis TTL.

---

## OTP Redis Structure

Key

otp:<email>

Example

otp:srawat@example.com

Value

{
"code_hash": "...",
"attempts": 0
}

TTL

600 Seconds

---

# 6. Session Management

## Access Token

Purpose

Authenticate API requests.

Lifetime

- 1 Hour

---

## Refresh Token

Purpose

Generate new access tokens without requiring OTP login.

Lifetime

- 30 Days

---

## Session Flow

1. User logs in via OTP.
2. Access token issued.
3. Refresh token issued.
4. Access token expires.
5. Refresh token used to obtain new access token.
6. User remains logged in.

After refresh token expiration:

- OTP verification is required again.

---

# 7. User Onboarding

## Step 1

User enters email address.

---

## Step 2

OTP is generated and emailed.

---

## Step 3

User verifies OTP.

---

## Step 4

User completes onboarding.

Required Fields:

- Name
- Workspace Name

Example:

Name

S. Rawat

Workspace Name

Acme

---

## Workspace Name Default

The workspace name field should be pre-filled with:

<User Name>'s Workspace

Example:

S. Rawat's Workspace

The user may change this value before workspace creation.

---

## Step 5

System creates:

- User
- Workspace
- Membership (OWNER)
- Free Subscription

---

## Step 6

Access token and refresh token are issued.

---

## Step 7

User is redirected to dashboard.

---

# 8. Workspace Ownership

The creator of a workspace becomes:

OWNER

Responsibilities:

- Workspace administration
- Team management
- Subscription management
- API key management

Each workspace has exactly one OWNER during MVP.

---

# 9. Authorization Model

Relays uses Role-Based Access Control (RBAC).

Supported roles:

- OWNER
- MEMBER

No additional roles are included in MVP.

---

# 10. OWNER Permissions

Workspace

- Rename workspace
- Update workspace settings

Members

- Invite members
- Remove members
- View members

API Keys

- Create API keys
- Revoke API keys
- View API keys

Usage

- View usage
- View quotas
- View logs

Billing

- Upgrade plan
- Downgrade plan
- Manage subscription

Future Features

- Configure domains
- Configure webhooks
- Configure integrations

OWNER has full workspace control.

---

# 11. MEMBER Permissions

Workspace

- View workspace information

Members

- View workspace members

API Keys

- View API key metadata

Usage

- View usage
- View quotas
- View logs

Restrictions

- Cannot invite members
- Cannot remove members
- Cannot create API keys
- Cannot revoke API keys
- Cannot manage billing
- Cannot rename workspace

MEMBER has operational access but no administrative control.

---

# 12. Workspace Restrictions

## MVP Rules

A user may belong to only one workspace.

Workspace switching is not supported.

Workspace ownership transfer is not supported.

Multiple workspace creation is not supported.

---

## Team Support

A workspace may contain multiple users.

Example

Workspace
├── OWNER
├── MEMBER
└── MEMBER

---

# 13. Abuse Prevention

The platform should implement:

- OTP request rate limiting
- Login rate limiting
- Disposable email detection
- Cloudflare Turnstile during signup

Purpose:

- Prevent automated signups
- Reduce free-tier abuse
- Protect email infrastructure

---

# 14. Data Model

## Users

Represents an authenticated user.

| Column      | Type         | Nullable | Default           | Notes                          |
| ----------- | ------------ | -------- | ----------------- | ------------------------------ |
| id          | UUID         | No       | gen_random_uuid() | Primary Key                    |
| email       | VARCHAR(255) | No       | -                 | Unique                         |
| name        | VARCHAR(255) | No       | -                 | Display Name                   |
| is_verified | BOOLEAN      | No       | TRUE              | Created after OTP verification |
| created_at  | TIMESTAMPTZ  | No       | now()             | Creation Timestamp             |
| updated_at  | TIMESTAMPTZ  | No       | now()             | Update Timestamp               |

Indexes

- UNIQUE(email)

---

## Workspaces

Represents a tenant boundary.

| Column     | Type         | Nullable | Default           | Notes              |
| ---------- | ------------ | -------- | ----------------- | ------------------ |
| id         | UUID         | No       | gen_random_uuid() | Primary Key        |
| name       | VARCHAR(255) | No       | -                 | Workspace Name     |
| created_at | TIMESTAMPTZ  | No       | now()             | Creation Timestamp |
| updated_at | TIMESTAMPTZ  | No       | now()             | Update Timestamp   |

---

## Workspace Members

Maps users to workspaces.

| Column       | Type        | Nullable | Default | Notes                |
| ------------ | ----------- | -------- | ------- | -------------------- |
| workspace_id | UUID        | No       | -       | FK → workspaces.id   |
| user_id      | UUID        | No       | -       | FK → users.id        |
| role         | VARCHAR(20) | No       | MEMBER  | OWNER, MEMBER        |
| joined_at    | TIMESTAMPTZ | No       | now()   | Membership Timestamp |

Primary Key

(workspace_id, user_id)

Indexes

- INDEX(workspace_id)
- INDEX(user_id)

---

## Refresh Tokens

Stores long-lived user sessions.

Refresh tokens are stored as hashes.

| Column     | Type         | Nullable | Default           | Notes                |
| ---------- | ------------ | -------- | ----------------- | -------------------- |
| id         | UUID         | No       | gen_random_uuid() | Primary Key          |
| user_id    | UUID         | No       | -                 | FK → users.id        |
| token_hash | VARCHAR(255) | No       | -                 | Hashed Refresh Token |
| expires_at | TIMESTAMPTZ  | No       | -                 | Expiration Timestamp |
| revoked_at | TIMESTAMPTZ  | Yes      | NULL              | Revocation Timestamp |
| created_at | TIMESTAMPTZ  | No       | now()             | Creation Timestamp   |

---

## Plans

Defines available subscription plans.

| Column              | Type        | Nullable | Default           | Notes                 |
| ------------------- | ----------- | -------- | ----------------- | --------------------- |
| id                  | UUID        | No       | gen_random_uuid() | Primary Key           |
| name                | VARCHAR(50) | No       | -                 | Free, Standard, Pro   |
| monthly_price_cents | INTEGER     | No       | 0                 | Price Stored In Cents |
| monthly_quota       | INTEGER     | No       | 0                 | Included Emails       |
| grace_quota         | INTEGER     | No       | 0                 | Soft Quota Limit      |
| rps_limit           | INTEGER     | No       | 0                 | Requests Per Second   |
| is_active           | BOOLEAN     | No       | TRUE              | Availability Flag     |
| created_at          | TIMESTAMPTZ | No       | now()             | Creation Timestamp    |

---

## Subscriptions

Represents a workspace's active plan.

| Column               | Type        | Nullable | Default           | Notes                |
| -------------------- | ----------- | -------- | ----------------- | -------------------- |
| id                   | UUID        | No       | gen_random_uuid() | Primary Key          |
| workspace_id         | UUID        | No       | -                 | FK → workspaces.id   |
| plan_id              | UUID        | No       | -                 | FK → plans.id        |
| status               | VARCHAR(30) | No       | ACTIVE            | Subscription Status  |
| current_period_start | TIMESTAMPTZ | No       | now()             | Billing Period Start |
| current_period_end   | TIMESTAMPTZ | No       | -                 | Billing Period End   |
| created_at           | TIMESTAMPTZ | No       | now()             | Creation Timestamp   |
| updated_at           | TIMESTAMPTZ | No       | now()             | Update Timestamp     |

---

## Usage Counters

Tracks monthly email usage.

| Column           | Type        | Nullable | Default | Notes              |
| ---------------- | ----------- | -------- | ------- | ------------------ |
| workspace_id     | UUID        | No       | -       | FK → workspaces.id |
| billing_period   | DATE        | No       | -       | Month Identifier   |
| emails_processed | BIGINT      | No       | 0       | Accepted Emails    |
| created_at       | TIMESTAMPTZ | No       | now()   | Creation Timestamp |
| updated_at       | TIMESTAMPTZ | No       | now()   | Update Timestamp   |

Primary Key

(workspace_id, billing_period)

---

# 15. Future Enhancements

Authentication

- Google Login
- GitHub Login
- Enterprise SSO

Authorization

- ADMIN Role
- VIEWER Role
- BILLING_ADMIN Role

Workspace Management

- Ownership Transfer
- Multiple Workspaces Per User

Security

- MFA
- Session Management UI
- Audit Logs

---

# 16. Final Decisions

Authentication

- Email OTP

OTP Storage

- Redis

OTP TTL

- 10 Minutes

Access Token

- 1 Hour

Refresh Token

- 30 Days

Tenant Entity

- Workspace

Workspace Creation

- Automatic After OTP Verification

Onboarding Fields

- Name
- Workspace Name

Roles

- OWNER
- MEMBER

Multiple Workspaces

- Not Supported

Team Members

- Supported

Database Model

- Shared Database
- Shared Schema
- Workspace-Based Multi-Tenancy
