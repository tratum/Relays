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

A workspace is created as part of the customer provisioning workflow after the customer has selected a subscription plan and completed the required registration flow.

_**Lifecycle Workflow**_

```text
Select plan
    │
    ├── Free ───────────────┐
    │                       │
    └── Paid → payment ─────┤
                            ▼
                    Registration
                            │
                            ▼
                  BEGIN TRANSACTION
                    ├── User
                    ├── Workspace
                    ├── Membership
                    ├── Subscription
                    └── Billing Period
                            │
                        COMMIT
```

For free plans, no persistent customer resources are created when the customer merely selects a plan. Workspace creation occurs only after registration is successfully completed.

For paid plans, workspace creation occurs only after the required payment has been successfully confirmed by the Billing module.

Once the customer is eligible for provisioning, the provisioning workflow performs the following operations within a single database transaction:

1. Create the user.
2. Create the workspace.
3. Create the workspace membership.
4. Assign the OWNER role.
5. Create the subscription.
6. Create the initial billing period.

The transaction guarantees that the user, workspace, membership, subscription, and initial billing period are created as one consistent unit.

If registration is abandoned, payment fails, or payment is not completed when required, no workspace or subscription is created.

Future versions of Relays may introduce additional lifecycle operations such as workspace suspension, transfer of ownership, and deletion.

---

# Subscription Plan Provisioning

## Cross-Module Integration

The Subscription module owns subscription state, plan entitlements, and billing-period lifecycle. It does not own customer registration, payment processing, or workspace lifecycle.

Subscription provisioning is orchestrated by an application-level provisioning workflow that coordinates the Workspace, Auth/Registration, Subscription, and Billing modules.

The provisioning workflow is responsible for coordinating these independent domains while preserving their individual ownership boundaries.

### Plan Selection

Subscription plan selection occurs before customer account and workspace creation.

The customer first selects a subscription plan. The selected plan is resolved by the backend and validated against the available plan catalog.

The customer does not become provisioned merely by selecting a plan.

Plan selection determines the subscription that will be created if registration and, where required, payment are successfully completed.

### Free Plan Provisioning

For a free plan, no payment or pre-registration billing state is required.

Selecting a free plan alone does not create any persistent customer resources.

The customer must complete registration before provisioning begins.

Upon successful registration, the provisioning workflow atomically creates:

1. User
2. Workspace
3. Workspace membership
4. OWNER role assignment
5. Subscription
6. Initial billing period

If the customer abandons registration, no workspace, subscription, or billing period is created.

### Paid Plan Provisioning

Paid plan provisioning depends on the Billing module.

The expected flow is:

```text
Customer selects plan
→ Resolve and validate plan
→ Billing creates payment session
→ Customer completes payment
→ Payment provider sends webhook
→ Billing verifies payment
→ Provisioning workflow is triggered
→ Registration + Workspace + Subscription + Billing Period are created atomically
```

The Subscription module does not process payments or communicate directly with the payment provider.

Billing remains responsible for payment-provider integration and for determining whether the payment requirement has been successfully satisfied.

### Provisioning Transaction

Once the customer is eligible for provisioning, the provisioning workflow creates the customer resources within a single PostgreSQL transaction.

```text
BEGIN
   │
   ├── Create User
   ├── Create Workspace
   ├── Create Workspace Membership
   ├── Assign OWNER role
   ├── Create Subscription
   └── Create Initial Billing Period
   │
COMMIT
```

No external payment-provider operation occurs inside this database transaction.

This ensures that a successfully provisioned customer cannot be left with only a partially-created workspace, subscription, or billing period.

### Deferred Integration Work

The following work is intentionally deferred until the relevant modules and application-level workflow exist:

- Define the customer plan-selection flow before authentication/registration.
- Define how the selected plan is carried into the registration/provisioning workflow.
- Implement paid-plan payment session creation in Billing.
- Implement payment-provider webhook handling and verification.
- Implement durable correlation between a paid registration and its payment.
- Implement registration flow for unauthenticated customers.
- Implement the application-level provisioning workflow.
- Integrate User creation with the provisioning workflow.
- Integrate Workspace creation with Subscription provisioning.
- Integrate Workspace membership and OWNER assignment with provisioning.
- Trigger provisioning after successful paid payment.
- Add idempotent provisioning and recovery for failed post-payment provisioning.
- Ensure the free-plan registration flow does not create persistent resources until registration is successfully completed.

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
