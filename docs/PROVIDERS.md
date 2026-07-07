# Providers

---

# Purpose

This document describes the provider architecture used by Relays.

Providers are responsible for communicating with external notification delivery services while isolating provider-specific behavior from the rest of the notification engine.

The notification pipeline interacts with providers exclusively through a common interface and a standardized delivery result.

This allows new providers to be added without modifying notification workflows, retry logic, or worker execution.

---

# Current Status

Relays currently implements two email providers.

| Provider      | Purpose                                          |
| ------------- | ------------------------------------------------ |
| MailRelay     | Production email delivery                        |
| Fake Provider | Deterministic testing of the Notification Engine |

The provider architecture has been designed to support additional email providers in the future without requiring changes to the notification processing pipeline.

---

# Provider Architecture

The notification engine never communicates directly with external services.

Instead, workers delegate delivery to a provider selected through the Provider Registry.

```text
Notification Worker
        │
        ▼
Provider Registry
        │
        ▼
Selected Provider
        │
        ▼
External Provider
        │
        ▼
ProviderResult
        │
        ▼
Notification Worker
```

Each component owns a single responsibility.

The worker is responsible for notification processing.

The provider is responsible for external communication.

The registry is responsible for provider selection.

The worker then interprets the returned `ProviderResult` to determine the next notification state.

---

# Provider Responsibilities

Providers are responsible for interacting with external notification services.

Specifically, a provider is responsible for:

- Building provider-specific requests
- Communicating with external APIs
- Mapping provider responses
- Mapping provider-specific exceptions
- Classifying failures
- Returning a standardized `ProviderResult`

Providers intentionally do **not** perform any workflow decisions.

A provider never:

- Updates notification state
- Schedules retries
- Persists delivery attempts
- Writes to the database
- Enqueues notifications
- Decides notification lifecycle transitions

These responsibilities belong to the Notification Worker.

---

# Worker Responsibilities

Workers orchestrate notification delivery.

After loading a notification from PostgreSQL, the worker:

1. Selects the configured provider.
2. Executes notification delivery.
3. Records the delivery attempt.
4. Updates notification state.
5. Schedules retries when appropriate.

Workers treat every provider identically.

The worker has no knowledge of MailRelay-specific APIs or any future provider implementations.

This separation keeps notification processing provider-independent.

---

# Provider Interface

All email providers implement the same interface.

```python
class EmailProvider(Protocol):
    async def send(
        self,
        payload: EmailPayload,
    ) -> ProviderResult:
        ...
```

Regardless of the underlying provider, the Notification Worker invokes the same `send()` operation.

This allows providers to be replaced or extended without changing worker execution logic.

---

# Provider Registry

The Provider Registry is responsible for resolving notification providers.

Workers never instantiate providers directly.

Instead, they request a provider from the registry using the notification's configured provider.

```text
Notification
(provider)

        │
        ▼

Provider Registry

        │
        ▼

Provider Instance

        │
        ▼

send(payload)
```

The registry lazily creates provider instances and reuses them for subsequent requests.

This avoids repeatedly constructing provider clients while keeping provider selection centralized.

---

# ProviderResult

Providers communicate delivery outcomes using a common `ProviderResult`.

The Notification Worker relies exclusively on this object when determining how notification processing should continue.

A ProviderResult contains:

| Field                   | Purpose                                      |
| ----------------------- | -------------------------------------------- |
| `status`                | Delivery outcome                             |
| `provider`              | Provider that executed delivery              |
| `provider_message_id`   | Provider-generated identifier                |
| `provider_error_code`   | Provider-specific error code                 |
| `error_message`         | Human-readable failure description           |
| `raw_provider_response` | Provider response for debugging and auditing |

The worker never interprets provider-specific responses directly.

Instead, providers translate external responses into a standardized result understood by the notification engine.

---

# Delivery Flow

The Notification Worker interacts with providers through a well-defined execution flow.

```text
Load Notification
        │
        ▼
Select Provider
        │
        ▼
Provider.send()
        │
        ▼
External API
        │
        ▼
ProviderResult
        │
        ▼
Record Delivery Attempt
        │
        ▼
Update Notification State
        │
        ▼
Retry Engine (if required)
```

The provider is responsible only for communicating with the external service.

Everything that happens before or after `Provider.send()` belongs to the Notification Worker.

---

# Failure Classification

External providers expose many different HTTP status codes, exceptions, and response formats.

The rest of Relays should never need to understand provider-specific behaviour.

Instead, every provider maps provider-specific failures into one of three standardized outcomes.

| ProviderResult Status | Meaning                                         | Worker Behaviour              |
| --------------------- | ----------------------------------------------- | ----------------------------- |
| `SUCCESS`             | Delivery completed successfully                 | Mark notification as `sent`   |
| `TEMPORARY_FAILURE`   | Failure is expected to succeed if retried later | Schedule retry                |
| `PERMANENT_FAILURE`   | Retry will not change the outcome               | Mark notification as `failed` |

This mapping is entirely the responsibility of the provider implementation.

The Notification Worker must never inspect HTTP status codes, provider-specific exceptions, or external response formats.

---

## Examples

| Provider Response      | ProviderResult      |
| ---------------------- | ------------------- |
| HTTP 200               | `SUCCESS`           |
| HTTP 429               | `TEMPORARY_FAILURE` |
| HTTP 503               | `TEMPORARY_FAILURE` |
| Connection Timeout     | `TEMPORARY_FAILURE` |
| Invalid Recipient      | `PERMANENT_FAILURE` |
| Authentication Failure | `PERMANENT_FAILURE` |

Different providers may expose different response formats, but all providers must ultimately produce one of the three standardized outcomes.

---

# MailRelay Provider

The MailRelay Provider is the production email provider currently used by Relays.

Its responsibilities include:

- Building MailRelay request payloads
- Communicating with the MailRelay REST API
- Translating MailRelay responses
- Mapping MailRelay exceptions
- Returning a `ProviderResult`

The MailRelay Provider does not interact with:

- PostgreSQL
- Redis
- Celery
- Notification state
- Retry scheduling

Those responsibilities remain outside the provider implementation.

---

# Fake Provider

The Fake Provider exists exclusively for testing the Notification Engine.

Unlike production providers, it never communicates with an external service.

Instead, delivery outcomes are controlled through notification metadata.

Example:

```json
{
  "testing": {
    "sequence": ["temporary_failure", "temporary_failure", "success"]
  }
}
```

Each execution consumes the next value in the sequence based on the notification's current `attempt_count`.

This allows deterministic testing of:

- successful delivery
- temporary failures
- permanent failures
- retry scheduling
- retry exhaustion
- worker behaviour

without relying on external email providers.

The Fake Provider should never be enabled in production environments.

---

# Implementing a New Provider

Adding a new provider should require changes only within the provider layer.

The recommended implementation process is:

## Step 1

Create a new provider package.

Example:

```text
providers/
    email/
        ses/
        sendgrid/
        resend/
        smtp/
```

Each provider should encapsulate all provider-specific code.

---

## Step 2

Create request and response models.

Provider-specific payloads should never leak outside the provider package.

These models are responsible only for representing the external API.

---

## Step 3

Implement the client.

The client should contain only the HTTP communication logic.

Its responsibilities include:

- authentication
- request execution
- response parsing

The client should not contain workflow decisions.

---

## Step 4

Implement the provider.

Every provider must implement the `EmailProvider` interface.

The provider is responsible for:

- validating unsupported features
- building provider requests
- calling the client
- translating responses
- classifying failures
- returning `ProviderResult`

---

## Step 5

Register the provider.

Register the provider inside the Provider Registry.

The Notification Worker should never instantiate providers directly.

---

## Step 6

Add provider configuration.

Any provider-specific configuration should remain isolated from the notification workflow.

Examples include:

- API keys
- endpoints
- sender identities
- regions

---

## Step 7

Test the provider.

Provider tests should verify:

- successful delivery
- temporary failures
- permanent failures
- response mapping
- exception mapping

The provider should be fully validated before being integrated into production workflows.

---

# Provider Development Checklist

When implementing a new provider, verify the following:

- [ ] Create provider package.
- [ ] Create request models.
- [ ] Create response models.
- [ ] Implement provider client.
- [ ] Implement `EmailProvider`.
- [ ] Map provider responses.
- [ ] Map provider exceptions.
- [ ] Return `ProviderResult`.
- [ ] Register provider.
- [ ] Add provider configuration.
- [ ] Add automated tests.
- [ ] Update provider documentation.

---

# Common Mistakes

The provider layer should remain isolated from notification workflow logic.

Avoid the following:

- Updating notification state.
- Scheduling retries.
- Writing to PostgreSQL.
- Enqueuing Celery tasks.
- Calling Redis directly.
- Returning raw HTTP responses to workers.
- Raising provider-specific exceptions outside the provider package.

Instead, providers should:

- Remain stateless.
- Hide external APIs.
- Classify delivery outcomes.
- Return a standardized `ProviderResult`.

---

# Design Decisions

## Why a Provider Interface?

A common interface allows workers to interact with every provider identically.

Adding a new provider therefore does not require changes to notification processing.

---

## Why a Provider Registry?

Centralizing provider construction avoids scattering provider initialization logic throughout the application.

The registry also makes it possible to lazily initialize and reuse provider instances.

---

## Why ProviderResult?

Every provider exposes different response formats.

`ProviderResult` provides a stable contract between providers and the notification engine.

Workers never depend on provider-specific APIs.

---

## Why Providers Do Not Update Notification State?

Notification state belongs to the Notification Engine.

Keeping state transitions outside providers ensures consistent behaviour across all delivery providers.

---

## Why Failure Classification Lives Inside Providers?

Only providers understand provider-specific APIs.

Allowing workers to classify provider failures would tightly couple the notification engine to individual providers and make adding new providers significantly more difficult.

---

# Future Providers

The provider architecture has been designed to support additional providers without changing the Notification Worker.

Potential future providers include:

- Amazon SES
- SendGrid
- Resend
- SMTP
- Mailgun
- Twilio (SMS)
- Generic Webhooks

Each new provider should integrate by implementing the existing provider interface and registering itself with the Provider Registry.

---

# Summary

Providers isolate external delivery services from the rest of the notification engine.

The Notification Worker interacts only with the Provider interface and `ProviderResult`, allowing delivery workflows, retry behaviour, and notification state management to remain completely provider-independent.

A correctly implemented provider should require changes only within the provider layer. If implementing a new provider requires modifications to notification workflows, retry logic, or worker execution, the provider abstraction should be re-evaluated.
