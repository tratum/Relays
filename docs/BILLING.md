# Relays Pricing Strategy

---

# 1. Purpose

This document defines the pricing, subscription, quota management, and usage enforcement strategy for Relays.

The objective is to establish a simple monetization model that:

- Is easy to understand for developers.
- Is simple to implement during MVP.
- Supports future scaling and additional notification channels.
- Minimizes operational complexity.
- Provides a clear upgrade path for growing customers.

This document covers:

- Pricing model
- Subscription plans
- Usage limits
- Rate limiting
- Quota enforcement
- Customer segmentation
- MVP and post-MVP scope

---

# 2. Product Context

Relays is a developer-focused notification infrastructure platform.

Current capabilities:

- Email delivery APIs
- Asynchronous processing
- Retry mechanisms
- Idempotency support
- Delivery tracking

Future capabilities may include:

- SMS
- Push Notifications
- WhatsApp
- Webhooks
- Additional communication channels

Relays is focused on transactional notifications and developer workflows.

Relays is not intended to compete with large-scale marketing email platforms.

---

# 3. Pricing Philosophy

The pricing model should remain simple.

The system should charge based on notification volume rather than API requests or infrastructure usage.

Key principles:

1. Predictable monthly pricing.
2. Simple billing calculations.
3. Easy plan comparison.
4. Minimal billing implementation effort.
5. Future support for usage-based overages.

---

# 4. Billing Unit

## Decision

Emails accepted for processing are the primary billing unit.

## Rationale

Charging per accepted email provides:

- Simple accounting
- Consistent measurement
- Easy quota tracking
- Provider-independent billing

## Not Supported

Relays will not charge based on:

- Number of API requests
- Number of batch submissions
- Successful deliveries only
- Retry attempts

These metrics increase complexity and create billing ambiguity.

---

# 5. Subscription Plans

## Free

Price:

$0/month

Included Usage:

- 1,000 emails/month

Features:

- Basic API access
- One API key
- Delivery logs
- Community support

Quota Policy:

- Hard quota enforcement

Target Users:

- Individual developers
- Students
- Portfolio projects
- Product evaluation

Launch Status:

- Available at MVP launch

---

## Standard

Price:

$10/month

Included Usage:

- 10,000 emails/month

Features:

- Up to 5 API keys
- 30-day log retention
- Higher throughput limits

Quota Policy:

- Soft quota enforcement

Target Users:

- Small production applications
- Indie SaaS founders

Launch Status:

- Available at MVP launch

---

## Pro

Price:

$25/month

Included Usage:

- 50,000 emails/month

Features:

- Up to 20 API keys
- Extended log retention
- Increased throughput limits

Quota Policy:

- Soft quota enforcement

Target Users:

- Growing startups
- SaaS businesses with increasing notification volume

Launch Status:

- Future release
- Not included in initial MVP launch

---

# 6. Rate Limiting Strategy

## Objectives

Rate limiting exists to:

- Protect platform stability
- Prevent abuse
- Prevent accidental traffic spikes
- Ensure fair resource allocation

## Enforcement Layer

Rate limits are enforced at:

- Account level
- API key level

## Limits

### Free

- 10 requests/second
- 300 requests/minute

### Standard

- 50 requests/second
- 3,000 requests/minute

### Pro

- 200 requests/second
- 12,000 requests/minute

## Implementation

Redis Token Bucket algorithm.

Reason:

- Low latency
- Industry-standard approach
- Easy horizontal scaling

---

# 7. Usage Enforcement

## Free Plan

Hard quota enforcement.

When quota is exhausted:

- Requests are rejected.
- API returns HTTP 429.

Reason:

- Prevent abuse.
- Encourage upgrades.
- Reduce operational cost.

---

## Paid Plans

Soft quota enforcement.

Example:

Standard Plan

- Included: 10,000 emails
- Grace Capacity: 12,000 emails

Workflow:

1. Warning at 80% usage.
2. Warning at 95% usage.
3. Grace usage enabled.
4. Temporary restriction after grace capacity is exhausted.

Reason:

- Better customer experience.
- Prevent accidental outages.

---

# 8. Fair Usage Policy

Relays reserves the right to restrict accounts that:

- Generate excessive retry traffic.
- Send spam or abusive content.
- Attempt to bypass rate limits.
- Create multiple accounts to avoid quotas.

The Fair Usage Policy exists to protect platform reliability for all users.

---

# 9. Customer Segments

## Primary Segment

Indie Developers

Common Use Cases:

- Authentication emails
- Password resets
- Contact forms
- User notifications

Expected Volume:

100–10,000 emails/month

---

## Secondary Segment

Early-Stage SaaS Companies

Common Use Cases:

- User onboarding
- Transactional notifications
- Operational alerts

Expected Volume:

10,000–100,000 emails/month

---

## Not Targeted During MVP

- Enterprise organizations
- Marketing email providers
- High-volume bulk senders
- Regulated industries requiring compliance guarantees

---

# 10. MVP Scope

The MVP will include:

- Accounts
- Subscription plans
- API keys
- Monthly usage tracking
- Rate limiting
- Quota enforcement

Launch Plans:

- Free
- Standard

Optional MVP Enhancements:

- Stripe subscription integration
- Basic usage dashboard

---

# 11. Out of Scope

The following capabilities are intentionally excluded from MVP:

- Overage billing
- Team management
- Role-based access control (RBAC)
- Multi-currency support
- Tax management
- Dedicated IPs
- Enterprise contracts
- SLA management
- Usage forecasting
- Custom pricing agreements

These features may be introduced after product-market validation.

---

# 12. Future Evolution

Potential future enhancements include:

## Usage-Based Billing

Additional usage charges beyond plan quotas.

Example:

- $1 per additional 1,000 emails

## Additional Channels

- SMS
- Push Notifications
- WhatsApp
- Webhooks

## Enterprise Features

- SSO
- RBAC
- Audit logs
- Dedicated infrastructure
- Custom limits

---

# 13. Required Data Model

## Account

Represents a customer workspace.

Fields:

- id
- name
- slug
- status
- plan_id
- created_at

---

## Plan

Defines pricing and limits.

Fields:

- id
- name
- monthly_price_cents
- monthly_quota
- rps_limit
- grace_quota
- overage_price_per_1000
- is_active

---

## Subscription

Represents billing state.

Fields:

- id
- account_id
- plan_id
- status
- current_period_start
- current_period_end
- renews_at

---

## Usage Counter

Tracks monthly consumption.

Fields:

- account_id
- billing_period
- emails_processed

---

## API Key

Authentication credential.

Fields:

- id
- account_id
- key_hash
- status
- created_at

---

# 14. Launch Recommendation

## Phase 1

- Accounts
- API Keys
- Usage Tracking
- Free Plan
- Standard Plan
- Hard & Soft Quotas

## Phase 2

- Stripe Integration
- Billing Portal
- Usage Dashboard

## Phase 3

- Pro Plan
- Analytics
- Team Support

## Phase 4

- SMS Support
- Push Notifications
- Multi-Channel Delivery
- Advanced Billing
- Enterprise Features

---

# 15. Final Decisions

Relays MVP will launch with:

## Free

- $0/month
- 1,000 emails/month

## Standard

- $10/month
- 10,000 emails/month

Future Plan:

## Pro

- $25/month
- 50,000 emails/month

Billing Model:

- Charge based on emails accepted for processing.

Usage Enforcement:

- Hard limits for Free accounts.
- Soft limits for paid accounts.

Rate Limiting:

- Redis-based token bucket implementation.

Advanced billing, enterprise features, usage-based overages, and multi-channel support are intentionally deferred until after initial customer validation.
