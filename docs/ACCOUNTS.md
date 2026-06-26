# Accounts

---

# Purpose

This document describes how Relays models customers, users, workspaces, and ownership.

It defines the tenancy model used throughout the platform and explains how customer resources are organized and isolated.

Authentication, sessions, JWTs, refresh tokens, and OTP workflows are documented separately in `AUTH.md`.

---

# Design Principles

The Accounts domain is designed around several core principles.

- **Workspace-first ownership** – Customer resources belong to workspaces rather than individual users.
- **Explicit membership** – Users belong to workspaces through a membership relationship.
- **Tenant isolation** – Workspaces form the primary isolation boundary throughout the platform.
- **Future extensibility** – The data model supports future collaboration features without requiring schema redesign.
- **Authentication independence** – User identity is independent from authentication mechanisms.

---

# Core Concepts

The Accounts domain consists of three primary entities.

```text
Users
   │
   ▼
Workspace Members
   │
   ▼
Workspaces
```

Each entity has a single responsibility.

| Entity            | Responsibility                                           |
| ----------------- | -------------------------------------------------------- |
| Users             | Represents an authenticated person.                      |
| Workspaces        | Represents a customer (tenant).                          |
| Workspace Members | Associates users with workspaces and defines their role. |

---

# Tenant Model

Relays follows a **workspace-based multi-tenant architecture**.

Every customer account is represented by a workspace.

Business resources are owned by workspaces rather than individual users.

Examples include:

- API Keys
- Notifications
- Future billing resources

This ownership model provides a consistent foundation for permissions, billing, and future collaboration features.

---

# User Model

A User represents a human identity within Relays.

A User is responsible for:

- Email address
- Display name
- Identity

A User is **not** responsible for:

- Authentication sessions
- API Keys
- Notifications
- Billing

Those concerns belong to other domains.

Authentication details are documented in `AUTH.md`.

---

# Workspace Model

A Workspace represents a customer account.

Every workspace has:

- A unique identifier
- A display name
- A globally unique slug
- A lifecycle status

The workspace is the primary ownership boundary within the platform.

Resources created by customers belong to the workspace rather than individual users.

---

# Membership Model

Users become members of workspaces through the `workspace_members` table.

This explicit relationship provides flexibility while avoiding tight coupling between users and workspaces.

Current MVP behavior:

- One user belongs to one workspace.
- Every workspace contains exactly one owner.

The schema intentionally supports future expansion to multiple members per workspace.

---

# Roles

Workspace membership determines a user's role.

Current roles include:

| Role   | Description                                     |
| ------ | ----------------------------------------------- |
| OWNER  | Full administrative control over the workspace. |
| MEMBER | Standard workspace member.                      |

Additional roles may be introduced as the authorization model evolves.

---

# Ownership

Relays consistently associates business resources with workspaces.

```text
Workspace
│
├── API Keys
├── Notifications
└── Future Billing Resources
```

This ensures:

- Consistent authorization
- Tenant isolation
- Workspace-level billing
- Simplified collaboration

Users interact with these resources through their membership within the workspace.

---

# Workspace Lifecycle

A workspace is automatically created during user registration.

The registration workflow performs the following operations within a single database transaction:

1. Create the user.
2. Create the workspace.
3. Create the workspace membership.
4. Assign the OWNER role.

This guarantees that partially-created customer accounts cannot exist.

Future versions of Relays may introduce additional lifecycle operations such as workspace suspension, transfer of ownership, and deletion.

---

# Future Evolution

The current Accounts model has been intentionally designed to support future capabilities without requiring fundamental schema changes.

Planned extensions may include:

- Multiple members per workspace
- Workspace invitations
- Organization support
- Custom roles
- Role-based access control (RBAC)
- Workspace ownership transfer
- Workspace deletion
- Account recovery

Because membership is modeled explicitly rather than embedding ownership directly into the Users table, these capabilities can be introduced incrementally while preserving the existing data model.
