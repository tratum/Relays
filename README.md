# Relays

Relays is an API-first Notification Delivery Service.

It allows applications to submit notification requests via HTTP APIs and delivers them asynchronously with reliable status tracking and failure handling.

Relays is designed to operate as a backend platform component and prioritizes correctness, durability, and explicit state management.

> **Current Scope:** Email Delivery only

---

## Target Users

- Backend engineers building internal services
- Small teams that need a simple notification backend
- Developers integrating asynchronous email delivery into their systems

Relays is not intended for end users or non-technical customers.

---

## Philosophy

- API-first
- Minimal abstractions
- Explicit state transitions
- Failures are first-class citizens