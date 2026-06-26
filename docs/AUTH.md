# Authentication & Session Architecture

## 1. Purpose

This document defines the complete authentication, authorization, session management, and identity architecture of Relays.

Authentication is responsible for proving the identity of a user, establishing trusted sessions, and protecting access to workspace resources.

The objectives of the authentication system are:

- Passwordless authentication with minimal onboarding friction.
- Secure long-lived sessions using refresh tokens.
- Stateless API authentication using JWT access tokens.
- Workspace-aware authentication for multi-tenant isolation.
- Strong protection against replay attacks and credential theft.
- Extensible architecture that supports future authentication providers without redesigning the existing system.

This document describes:

- Registration workflow
- Login workflow
- Session lifecycle
- Access token architecture
- Refresh token architecture
- Registration token architecture
- OTP lifecycle
- JWT authentication
- Session persistence
- Logout
- Current user authentication
- OTP rate limiting
- Security decisions
- Failure scenarios
- Future evolution

This document does **not** describe:

- API Key authentication
- Workspace authorization rules
- Notification submission
- Billing
- Worker execution

Those topics are documented separately.

<br>

# 2. Design Principles

The authentication system is designed around a small number of architectural principles.

## Passwordless Authentication

Relays intentionally avoids password-based authentication during the MVP.

Instead, users authenticate using one-time passwords (OTP) delivered to their verified email address.

Benefits include:

- Eliminates password management.
- Eliminates password reset flows.
- Reduces credential stuffing attacks.
- Simplifies onboarding.
- Provides a better developer experience.

Future authentication providers (Google, GitHub, SAML, OIDC, etc.) can be introduced without changing the remainder of the authentication architecture.

---

## Stateless Authentication

Authenticated API requests use short-lived JWT access tokens.

The server never stores access tokens.

Each request can be authenticated independently by verifying the JWT signature and validating the associated workspace session.

Benefits:

- Horizontal scalability.
- No shared session cache.
- No database lookup required for token validation.
- Simple load balancing.

---

## Stateful Sessions

Although access tokens are stateless, user sessions are stateful.

Every successful login creates a persistent session stored in PostgreSQL.

Each session owns exactly one refresh token.

Benefits:

- Immediate session revocation.
- Refresh token rotation.
- Multiple device support in the future.
- Session auditing.
- Logout support.

---

## Layered Authentication

Authentication is intentionally divided into multiple stages.

```
Email Ownership
        │
        ▼
Registration OTP
        │
        ▼
Registration Token
        │
        ▼
Account Creation
        │
        ▼
Access Token
        │
        ▼
Refresh Token
        │
        ▼
Authenticated Session
```

Each stage has a single responsibility.

Compromising one stage does not compromise the others.

---

## Security by Default

Authentication favors secure defaults over implementation convenience.

Examples include:

- OTPs are never stored in plaintext.
- Refresh tokens are stored only as hashes.
- Registration tokens are short-lived.
- Access tokens expire automatically.
- Refresh tokens rotate after every successful refresh.
- Sessions can be revoked immediately.
- OTP requests are rate limited.
- JWTs include explicit token types.
- Every token contains an expiration time.
- Authentication failures never disclose unnecessary information.

<br>

# 3. Core Concepts

The authentication subsystem revolves around several core concepts.

Understanding these concepts makes the remaining sections significantly easier to follow.

## User

A User represents a human identity within Relays.

Each user has:

- One verified email address.
- One display name.
- Membership in exactly one workspace during the MVP.

Users authenticate using email OTP.

Users never authenticate using passwords.

---

## Workspace

A Workspace represents the tenant boundary of the platform.

Authentication always resolves to a user within a workspace.

Every authenticated API request ultimately executes in the context of exactly one workspace.

---

## Session

A Session represents an authenticated login.

Sessions are persisted in PostgreSQL.

Each session contains:

- Session identifier.
- User identifier.
- Refresh token hash.
- Expiration timestamp.
- Revocation timestamp.

Sessions are the source of truth for long-lived authentication.

---

## One-Time Password (OTP)

An OTP proves temporary ownership of an email address.

Two independent OTP flows exist:

- Registration OTP
- Login OTP

Both flows use:

- Six-digit numeric codes.
- Limited lifetime.
- Secure hashing.
- One-time consumption.

An OTP can never be reused after successful verification.

---

## Registration Token

A Registration Token is a short-lived JWT issued after successful email verification during registration.

Its purpose is to prove that:

- the email address has been verified, and
- account creation is authorized.

The registration token is only valid during the onboarding flow.

It cannot authenticate API requests.

---

## Access Token

An Access Token is a short-lived JWT used to authenticate API requests.

Characteristics:

- Stateless.
- Signed by the server.
- Contains the authenticated user identifier.
- Expires automatically.
- Never stored by the server.

Access tokens are presented in the HTTP Authorization header using the Bearer authentication scheme.

---

## Refresh Token

A Refresh Token represents a long-lived authenticated session.

Unlike access tokens, refresh tokens are opaque random values.

Characteristics:

- Randomly generated.
- Stored only as hashes.
- Persisted in PostgreSQL.
- Rotated after every successful refresh.
- Revocable at any time.

Refresh tokens are never JWTs.

They exist solely to obtain new access tokens without requiring the user to perform OTP authentication again.

# Authentication & Session Architecture

## 1. Purpose

This document defines the complete authentication, authorization, session management, and identity architecture of Relays.

Authentication is responsible for proving the identity of a user, establishing trusted sessions, and protecting access to workspace resources.

The objectives of the authentication system are:

- Passwordless authentication with minimal onboarding friction.
- Secure long-lived sessions using refresh tokens.
- Stateless API authentication using JWT access tokens.
- Workspace-aware authentication for multi-tenant isolation.
- Strong protection against replay attacks and credential theft.
- Extensible architecture that supports future authentication providers without redesigning the existing system.

This document describes:

- Registration workflow
- Login workflow
- Session lifecycle
- Access token architecture
- Refresh token architecture
- Registration token architecture
- OTP lifecycle
- JWT authentication
- Session persistence
- Logout
- Current user authentication
- OTP rate limiting
- Security decisions
- Failure scenarios
- Future evolution

This document does **not** describe:

- API Key authentication
- Workspace authorization rules
- Notification submission
- Billing
- Worker execution

Those topics are documented separately.

<br>

# 2. Design Principles

The authentication system is designed around a small number of architectural principles.

## Passwordless Authentication

Relays intentionally avoids password-based authentication during the MVP.

Instead, users authenticate using one-time passwords (OTP) delivered to their verified email address.

Benefits include:

- Eliminates password management.
- Eliminates password reset flows.
- Reduces credential stuffing attacks.
- Simplifies onboarding.
- Provides a better developer experience.

Future authentication providers (Google, GitHub, SAML, OIDC, etc.) can be introduced without changing the remainder of the authentication architecture.

---

## Stateless Authentication

Authenticated API requests use short-lived JWT access tokens.

The server never stores access tokens.

Each request can be authenticated independently by verifying the JWT signature and validating the associated workspace session.

Benefits:

- Horizontal scalability.
- No shared session cache.
- No database lookup required for token validation.
- Simple load balancing.

---

## Stateful Sessions

Although access tokens are stateless, user sessions are stateful.

Every successful login creates a persistent session stored in PostgreSQL.

Each session owns exactly one refresh token.

Benefits:

- Immediate session revocation.
- Refresh token rotation.
- Multiple device support in the future.
- Session auditing.
- Logout support.

---

## Layered Authentication

Authentication is intentionally divided into multiple stages.

```
Email Ownership
        │
        ▼
Registration OTP
        │
        ▼
Registration Token
        │
        ▼
Account Creation
        │
        ▼
Access Token
        │
        ▼
Refresh Token
        │
        ▼
Authenticated Session
```

Each stage has a single responsibility.

Compromising one stage does not compromise the others.

---

## Security by Default

Authentication favors secure defaults over implementation convenience.

Examples include:

- OTPs are never stored in plaintext.
- Refresh tokens are stored only as hashes.
- Registration tokens are short-lived.
- Access tokens expire automatically.
- Refresh tokens rotate after every successful refresh.
- Sessions can be revoked immediately.
- OTP requests are rate limited.
- JWTs include explicit token types.
- Every token contains an expiration time.
- Authentication failures never disclose unnecessary information.

<br>

# 3. Core Concepts

The authentication subsystem revolves around several core concepts.

Understanding these concepts makes the remaining sections significantly easier to follow.

## User

A User represents a human identity within Relays.

Each user has:

- One verified email address.
- One display name.
- Membership in exactly one workspace during the MVP.

Users authenticate using email OTP.

Users never authenticate using passwords.

---

## Workspace

A Workspace represents the tenant boundary of the platform.

Authentication always resolves to a user within a workspace.

Every authenticated API request ultimately executes in the context of exactly one workspace.

---

## Session

A Session represents an authenticated login.

Sessions are persisted in PostgreSQL.

Each session contains:

- Session identifier.
- User identifier.
- Refresh token hash.
- Expiration timestamp.
- Revocation timestamp.

Sessions are the source of truth for long-lived authentication.

---

## One-Time Password (OTP)

An OTP proves temporary ownership of an email address.

Two independent OTP flows exist:

- Registration OTP
- Login OTP

Both flows use:

- Six-digit numeric codes.
- Limited lifetime.
- Secure hashing.
- One-time consumption.

An OTP can never be reused after successful verification.

---

## Registration Token

A Registration Token is a short-lived JWT issued after successful email verification during registration.

Its purpose is to prove that:

- the email address has been verified, and
- account creation is authorized.

The registration token is only valid during the onboarding flow.

It cannot authenticate API requests.

---

## Access Token

An Access Token is a short-lived JWT used to authenticate API requests.

Characteristics:

- Stateless.
- Signed by the server.
- Contains the authenticated user identifier.
- Expires automatically.
- Never stored by the server.

Access tokens are presented in the HTTP Authorization header using the Bearer authentication scheme.

---

## Refresh Token

A Refresh Token represents a long-lived authenticated session.

Unlike access tokens, refresh tokens are opaque random values.

Characteristics:

- Randomly generated.
- Stored only as hashes.
- Persisted in PostgreSQL.
- Rotated after every successful refresh.
- Revocable at any time.

Refresh tokens are never JWTs.

They exist solely to obtain new access tokens without requiring the user to perform OTP authentication again.

<br>

# 4. Authentication Architecture

Authentication in Relays is intentionally separated into multiple independent components.

Each component has a single responsibility.

```text
                          User
                            │
                            ▼
                  Request Registration OTP
                            │
                            ▼
                registration_otp (PostgreSQL)
                            │
                            ▼
                 Verify Registration OTP
                            │
                            ▼
                  Registration Token (JWT)
                            │
                            ▼
                     Create Account
                            │
          ┌─────────────────┴─────────────────┐
          ▼                                   ▼
      Access Token                    Refresh Token
       (JWT, 1 Hour)                 (Opaque Random Token)
          │                                   │
          │                            SHA-512 Hash
          │                                   │
          ▼                                   ▼
 Protected APIs                     sessions (PostgreSQL)
          │                                   │
          └────────────── Refresh ────────────┘
```

The architecture separates identity verification from long-lived session management.

Each authentication artifact exists for a specific purpose.

| Component          | Responsibility                             |
| ------------------ | ------------------------------------------ |
| Registration OTP   | Verify ownership of an email address       |
| Registration Token | Authorize account creation                 |
| Access Token       | Authenticate API requests                  |
| Refresh Token      | Maintain long-lived authenticated sessions |
| Session            | Persist authenticated logins               |

No authentication artifact serves multiple purposes.

---

# 5. Registration Flow

Registration is intentionally divided into three independent stages.

```text
Request OTP
      │
      ▼
Verify OTP
      │
      ▼
Registration Token
      │
      ▼
Create Account
      │
      ▼
Access Token
+
Refresh Token
```

Splitting registration into multiple stages improves security while keeping the user experience simple.

---

## Step 1 — Request Registration OTP

The user begins registration by submitting an email address.

```http
POST /auth/register/request-otp
```

Workflow:

```text
Client
    │
    ▼
Validate Request
    │
    ▼
Check OTP Rate Limit
    │
    ▼
Verify Email Is Not Registered
    │
    ▼
Generate OTP
    │
    ▼
Hash OTP
    │
    ▼
Store Hash In PostgreSQL
    │
    ▼
Queue Email
    │
    ▼
202 Accepted
```

### Responsibilities

This endpoint is responsible for:

- validating the email address
- enforcing OTP rate limits
- ensuring the email is eligible for registration
- generating a secure OTP
- hashing the OTP
- storing the hash
- queueing the delivery email

It is **not** responsible for:

- creating users
- creating workspaces
- issuing access tokens

---

## OTP Storage

Registration OTPs are stored in PostgreSQL.

Only the hash is persisted.

```text
registration_otp
├── email
├── otp_hash
├── expires_at
├── consumed_at
└── created_at
```

The original OTP is never stored.

If an attacker gains read-only database access, they cannot recover valid OTPs.

---

## Existing Registration OTP

Only one active registration OTP may exist per email address.

Requesting another OTP replaces the previous one.

Benefits:

- Prevents multiple valid OTPs.
- Simplifies verification.
- Eliminates ambiguity.

---

## OTP Lifetime

Registration OTPs are short-lived.

Expired OTPs are considered invalid regardless of their value.

Expired OTPs are removed during verification and replaced when a new OTP is requested.

---

## Step 2 — Verify Registration OTP

After receiving the verification code, the user submits:

- email
- OTP

```http
POST /auth/register/verify-otp
```

Workflow:

```text
Client
    │
    ▼
Lookup OTP
    │
    ▼
Expired?
 ┌──┴──┐
 │     │
Yes    No
 │      │
Delete  Verify Hash
 │      │
 │      ▼
 │   Invalid?
 │   ┌──┴──┐
 │   │     │
 │  Yes    No
 │   │      │
 │   ▼      ▼
 │ Reject Consume OTP
 │           │
 └──────────►│
             ▼
 Generate Registration Token
             │
             ▼
       200 OK
```

---

## OTP Verification

Verification consists of four steps.

1. Load the stored OTP hash.
2. Ensure the OTP has not expired.
3. Compare the submitted OTP hash with the stored hash.
4. Consume the OTP.

If any step fails, verification fails.

---

## OTP Consumption

A successfully verified OTP is immediately consumed.

Consumption marks the OTP as used.

A consumed OTP can never be used again.

This protects against replay attacks.

Even if an attacker obtains the OTP immediately after successful verification, it is already invalid.

---

## Registration Token

Successful verification returns a Registration Token.

The token is a signed JWT.

It contains:

- issuer
- email
- token type
- issued-at timestamp
- expiration timestamp

The token **does not** contain:

- user id
- workspace id
- roles
- permissions

No account exists yet.

The registration token exists solely to authorize account creation.

---

## Registration Token Lifetime

Registration tokens are intentionally short-lived.

Their only purpose is bridging the gap between email verification and account creation.

Once expired, the user must verify their email again.

---

## Step 3 — Create Account

The final registration step creates the Relays account.

```http
POST /auth/register
```

Required input:

- Registration Token
- User Name
- Workspace Name

Workflow:

```text
Validate Registration Token
           │
           ▼
Verify Email Not Registered
           │
           ▼
Create User
           │
           ▼
Create Workspace
           │
           ▼
Create Workspace Membership
           │
           ▼
Create Session
           │
           ▼
Issue Access Token
           │
           ▼
Generate Refresh Token
           │
           ▼
201 Created
```

All database operations execute inside a single transaction.

If any step fails, the transaction is rolled back.

No partial account can ever exist.

---

## Initial Workspace

Every new user automatically receives exactly one workspace.

The registering user becomes the OWNER of that workspace.

This establishes the tenant boundary used throughout the platform.

Future resources such as:

- API Keys
- Notifications
- Usage
- Billing

are owned by this workspace.

---

## Initial Session

Account creation automatically authenticates the user.

The server creates:

- Access Token
- Refresh Token
- Session

The user does not need to perform a second login after registration.

This reduces onboarding friction while maintaining security guarantees.

<br>

# 6. Login Flow

Unlike registration, login assumes the user already owns a verified Relays account.

Authentication therefore focuses on proving ownership of the registered email address and establishing a new authenticated session.

```text
Request OTP
      │
      ▼
Verify OTP
      │
      ▼
Create Session
      │
      ▼
Issue Access Token
+
Issue Refresh Token
```

---

## Step 1 — Request Login OTP

A user initiates authentication by submitting their email address.

```http
POST /auth/login/request-otp
```

Workflow:

```text
Client
    │
    ▼
Validate Request
    │
    ▼
Check OTP Rate Limit
    │
    ▼
Lookup User
    │
    ▼
Generate OTP
    │
    ▼
Hash OTP
    │
    ▼
Store Hash
    │
    ▼
Queue Email
    │
    ▼
202 Accepted
```

---

## Existing Accounts

Unlike registration, login only succeeds for existing accounts.

If the email address does not belong to a registered user:

- no OTP is generated
- no database record is created
- the client still receives a generic success response

```http
202 Accepted
```

This prevents user enumeration attacks.

Attackers cannot determine whether an email address exists by observing API responses.

---

## Login OTP Storage

Login OTPs are stored independently from registration OTPs.

```text
login_otp
├── user_id
├── otp_hash
├── expires_at
├── consumed_at
└── created_at
```

Separating registration and login OTPs simplifies each workflow and avoids mixing unrelated authentication state.

---

## OTP Replacement

Only one active login OTP exists per user.

Requesting another login OTP invalidates the previous one.

This prevents multiple valid login codes from existing simultaneously.

---

## Step 2 — Authenticate User

The user submits:

- email
- OTP

```http
POST /auth/login
```

Workflow:

```text
Lookup User
      │
      ▼
Lookup Login OTP
      │
      ▼
Expired?
 ┌────┴────┐
 │         │
Yes        No
 │          │
Delete   Verify Hash
 │          │
 │      Invalid?
 │      ┌───┴────┐
 │      │        │
 │     Yes       No
 │      │         │
 │      ▼         ▼
 │   Reject   Consume OTP
 │                │
 └────────────────►
                  ▼
        Verify Workspace Context
                  │
                  ▼
           Create Session
                  │
                  ▼
         Issue Access Token
                  │
                  ▼
       Generate Refresh Token
                  │
                  ▼
             200 OK
```

---

## Workspace Validation

Successful OTP verification alone is insufficient.

Before authentication succeeds, the system verifies that:

- the user exists
- the workspace membership exists

A valid authenticated session must always belong to a valid workspace.

---

## Session Creation

Every successful login creates a new session.

The session is persisted in PostgreSQL.

```text
sessions
├── id
├── user_id
├── refresh_token_hash
├── expires_at
├── revoked_at
└── created_at
```

A refresh token hash is stored instead of the refresh token itself.

---

## Login Response

Successful authentication returns:

- Access Token
- Refresh Token
- Token Type

Example:

```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "Bearer"
}
```

---

# 7. Session Management

Relays separates authentication into two independent concepts.

```text
Short-Lived Authentication
            │
            ▼
      Access Token
            │
            ▼
API Authentication

──────────────────────────────

Long-Lived Authentication
            │
            ▼
     Refresh Token
            │
            ▼
        Session
```

This separation provides strong security while maintaining a good user experience.

---

## Why Sessions Exist

Access tokens are intentionally short-lived.

Without refresh tokens, users would need to complete OTP authentication every hour.

Instead, Relays stores authenticated sessions.

A session represents an authenticated login that may survive multiple access token expirations.

---

## Session Lifecycle

```text
OTP Login
    │
    ▼
Create Session
    │
    ▼
Issue Access Token
    │
    ▼
Access Token Expires
    │
    ▼
Refresh Token Used
    │
    ▼
Rotate Session
    │
    ▼
Issue New Tokens
    │
    ▼
Continue Session
```

The session remains valid until:

- expiration
- logout
- administrative revocation

---

## Access Tokens

Access tokens are JWTs.

Characteristics:

- signed
- stateless
- short-lived
- self-contained

They contain:

- issuer
- user identifier
- token type
- token version
- issued-at timestamp
- expiration timestamp

They do not contain:

- workspace information
- permissions
- refresh token
- session identifier

Authorization data is always obtained from the database.

---

## Refresh Tokens

Refresh tokens are opaque random values.

They are **not JWTs**.

Characteristics:

- cryptographically random
- unguessable
- stored only as hashes
- long-lived
- rotated after every successful refresh

A refresh token has exactly one purpose:

Generate a new access token.

It cannot authenticate API requests.

---

## Session Persistence

Sessions are stored in PostgreSQL instead of Redis.

Reasons:

- durability across restarts
- transactional consistency
- easy revocation
- future auditing
- future device management

PostgreSQL is the source of truth for authenticated sessions.

---

## Session Expiration

Every session has an expiration timestamp.

Expired sessions are considered invalid regardless of whether the refresh token is presented.

Expired sessions require the user to authenticate using OTP again.

---

## Session Revocation

A session may be revoked before expiration.

Revocation marks the session as inactive.

Once revoked:

- refresh token becomes invalid
- future refresh attempts fail
- user must authenticate again

Revocation never affects already issued access tokens.

Access tokens naturally expire after their configured lifetime.

---

## Multiple Sessions

The current architecture supports multiple simultaneous sessions for a user.

Examples:

- Desktop
- Laptop
- Mobile
- Tablet

Each device receives an independent refresh token.

Each refresh token maps to a different session.

Revoking one session does not affect the others.

Although the MVP does not expose device management, the underlying session model fully supports it.

---

# 8. Refresh Token Rotation

Refresh token rotation is performed every time a refresh request succeeds.

Instead of reusing refresh tokens indefinitely, Relays issues a completely new refresh token after each successful refresh.

Workflow:

```text
Receive Refresh Token
          │
          ▼
Hash Token
          │
          ▼
Lookup Session
          │
          ▼
Validate Session
          │
          ▼
Generate New Refresh Token
          │
          ▼
Hash New Token
          │
          ▼
Rotate Stored Hash
          │
          ▼
Issue New Access Token
          │
          ▼
Return New Tokens
```

The previous refresh token immediately becomes invalid.

This significantly reduces the impact of refresh token theft.

If an attacker steals an older refresh token after rotation has already occurred, the stolen token can no longer be used.

Refresh token rotation therefore limits replay attacks to a single refresh window instead of the entire session lifetime.

<br>

# 9. JWT Authentication

All protected Relays APIs require authentication using a JWT access token.

The client supplies the access token using the HTTP Authorization header.

```http
Authorization: Bearer <access_token>
```

The JWT is validated before the request reaches any protected workflow.

---

## Authentication Guard

Every protected endpoint passes through the JWT authentication guard.

The guard is responsible for:

- validating the Authorization header
- decoding the JWT
- validating JWT claims
- verifying the authenticated workspace context
- attaching authenticated user information to the request

The guard is **not** responsible for:

- authorization
- role validation
- business rules
- permission checks

Those responsibilities belong to individual modules.

---

## Authentication Flow

```text
Incoming Request
        │
        ▼
Authorization Header Present?
        │
   ┌────┴────┐
   │         │
  No        Yes
   │         │
401      Validate Scheme
             │
             ▼
      Decode JWT
             │
             ▼
      Validate Claims
             │
             ▼
 Verify Workspace Context
             │
             ▼
 Attach User Context
             │
             ▼
 Execute Endpoint
```

Only fully authenticated requests reach the application logic.

---

## JWT Validation

Every access token undergoes multiple validation steps.

The server validates:

- signature
- issuer
- expiration
- issued-at timestamp
- token type
- token version
- user identifier

Any validation failure immediately rejects the request.

---

## Workspace Validation

A valid JWT alone is insufficient.

After decoding the JWT, Relays verifies that the authenticated user still belongs to a valid workspace.

```text
JWT
 │
 ▼
Decode
 │
 ▼
Workspace Exists?
 │
 ├── No ──► Reject
 │
 └── Yes ─► Continue
```

This guarantees that every authenticated request executes inside a valid tenant.

---

## Authenticated Request Context

After successful authentication, the guard attaches the authenticated context to the request.

Current context includes:

- user_id
- workspace_id

Future versions may additionally expose:

- role
- session_id
- subscription information

The request context becomes the trusted identity for downstream workflows.

---

# 10. Current User Endpoint

The authenticated user endpoint allows clients to retrieve the currently authenticated identity.

```http
GET /auth/me
```

Authentication is required.

---

## Workflow

```text
Client
   │
   ▼
JWT Authentication Guard
   │
   ▼
Authenticated Context
   │
   ▼
Load User Context
   │
   ▼
Return User
```

The endpoint does not decode JWT claims directly.

Instead, it relies entirely on the authenticated request context established by the JWT guard.

This ensures a single authentication path throughout the application.

---

## Returned Information

The endpoint returns:

- user identifier
- workspace identifier
- user name
- email
- workspace name

No sensitive authentication information is returned.

Specifically, the response never includes:

- access tokens
- refresh tokens
- session identifiers
- internal authentication state

---

# 11. Logout Flow

Logout terminates an authenticated session.

Unlike access tokens, refresh tokens are stateful and therefore can be revoked immediately.

```http
POST /auth/logout
```

Authentication requires a valid refresh token.

---

## Workflow

```text
Receive Refresh Token
          │
          ▼
Hash Token
          │
          ▼
Lookup Session
          │
          ▼
Session Exists?
      ┌───┴────┐
      │        │
     No       Yes
      │        │
     401   Revoke Session
               │
               ▼
           204 No Content
```

---

## Session Revocation

Logout marks the session as revoked.

The refresh token immediately becomes unusable.

Subsequent refresh attempts fail.

No database records are deleted.

Keeping revoked sessions provides:

- auditability
- future security investigations
- device history
- session analytics

---

## Access Token Behaviour

Logging out does not invalidate already-issued access tokens.

Access tokens remain valid until their expiration time.

This is an intentional trade-off.

Immediate JWT revocation would require maintaining a distributed blacklist, increasing operational complexity and introducing additional infrastructure dependencies.

Instead, Relays uses:

- short-lived access tokens
- long-lived revocable refresh tokens

This provides strong security while keeping API authentication stateless.

---

# 12. OTP Rate Limiting

OTP generation endpoints are protected by Redis-based sliding-window rate limiting.

The objective is to:

- prevent automated abuse
- reduce email provider costs
- mitigate brute-force attacks
- protect infrastructure resources

Rate limiting occurs before any OTP is generated.

Requests exceeding the configured limits are rejected immediately.

---

## Rate Limiting Policy

Both registration and login maintain independent limits.

Current limits are:

| Window     |       Limit |
| ---------- | ----------: |
| 60 seconds |   1 request |
| 1 hour     |  5 requests |
| 24 hours   | 20 requests |

Registration limits never affect login limits.

Likewise, login requests never consume registration quotas.

---

## Sliding Window Algorithm

Relays uses a Redis Sorted Set (ZSET) to implement sliding-window rate limiting.

Each successful request inserts the current timestamp into the sorted set.

Before evaluating a request:

1. Expired timestamps are removed.
2. Remaining requests inside the active window are counted.
3. If the limit has been reached, the request is rejected.
4. Otherwise, the current request is recorded.

```text
Request
   │
   ▼
Remove Expired Entries
   │
   ▼
Count Active Requests
   │
   ▼
Limit Reached?
 ┌──┴──┐
 │     │
Yes    No
 │      │
429   Record Request
 │      │
 └──────►
         ▼
      Continue
```

Redis automatically expires inactive keys using TTL, eliminating the need for background cleanup jobs.

---

## Why Sliding Windows?

Sliding-window rate limiting provides smoother behaviour than fixed windows.

For example:

```text
09:59:59
10:00:00
```

A fixed-window algorithm could allow both requests despite occurring one second apart.

Sliding windows evaluate requests over a continuously moving interval.

This prevents burst traffic around window boundaries while remaining computationally efficient.

---

# 13. Security Decisions

The authentication system intentionally adopts conservative security practices.

Every major design decision exists to reduce attack surface while preserving developer experience.

---

## OTPs Are Stored As Hashes

Relays never stores OTP values in plaintext.

Only cryptographic hashes are persisted.

Benefits:

- database compromise does not expose valid OTPs
- accidental logging cannot reveal OTPs
- administrators cannot retrieve OTPs

---

## Refresh Tokens Are Stored As Hashes

Refresh tokens function as long-lived credentials.

Compromising a refresh token effectively grants long-term access.

For this reason, refresh tokens are stored only as cryptographic hashes.

Even with database access, attackers cannot authenticate using stored session data.

---

## Access Tokens Remain Stateless

Access tokens are intentionally not persisted.

Benefits include:

- horizontal scalability
- simplified deployments
- no shared authentication cache
- reduced database load

Stateless access tokens are complemented by stateful refresh sessions.

---

## PostgreSQL Is The Source Of Truth

Authentication state is persisted in PostgreSQL.

Redis is never treated as durable authentication storage.

Reasons include:

- transactional guarantees
- durability
- auditing
- session revocation
- operational simplicity

Authentication remains correct even if Redis is restarted.

---

## One-Time OTP Consumption

Successful verification immediately consumes the OTP.

A consumed OTP cannot be reused.

This prevents replay attacks and guarantees that each verification code is valid for exactly one successful authentication event.

---

## Refresh Token Rotation

Every successful refresh invalidates the previous refresh token.

A completely new refresh token is generated and stored.

This significantly limits the usefulness of stolen refresh tokens and reduces replay opportunities.

---

## Generic Error Responses

Authentication endpoints intentionally avoid revealing unnecessary information.

Where appropriate, responses do not disclose whether:

- an account exists
- an email is registered
- authentication failed because of user lookup or credential validation

This reduces opportunities for user enumeration attacks.
