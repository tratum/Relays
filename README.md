# Relays

---

## Overview

Relays is an **API-first Notification Delivery Service** designed for backend systems that require reliable and asynchronous communication.

It allows applications to submit notification requests via HTTP APIs and delivers them asynchronously with robust status tracking, retry mechanisms, and failure handling.

Relays is built as a backend platform component with a strong focus on **correctness, durability, and explicit state management**.

> **Current Scope:** Email delivery only

---

## Target Users

Relays is intended for:

* Backend engineers building internal services and distributed systems
* Small teams needing a simple, reliable notification backend
* Developers integrating asynchronous email delivery into their applications

> This system is **not intended for end users or non-technical customers**.

---

## Philosophy

Relays follows a set of core design principles:

* **API-first**
  All functionality is exposed through clear and consistent HTTP APIs.

* **Minimal abstractions**
  Avoids unnecessary layers to maintain simplicity and predictability.

* **Explicit state transitions**
  Every notification moves through well-defined and observable states.

* **Failures as first-class citizens**
  Errors are expected, tracked, and handled systematically rather than hidden.

---

## Setup

### 1. Install `uv`

```bash
curl -Ls https://astral.sh/uv/install.sh | sh
```
### 2. Clone the Repository

```bash
git clone https://github.com/tratum/Relays.git
cd relays
```
### 3. Configure Environment

Create a `.env` file in the root directory:

```env
ENV=dev
VERSION=v1
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/relays
REDIS_URL=redis://localhost:6379/0
```
### 4. Install Dependencies

```bash
uv sync
```

### 5. Run the Application

Start the development server:
```bash
uv run uvicorn app.main:app --reload
```

### 6. Manage Dependencies

Add a dependency:

```bash
uv add <package_name>
```

Remove a dependency:

```bash
uv remove <package_name>
```

---
