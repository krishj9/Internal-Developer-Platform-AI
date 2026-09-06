# ADR-001: Bespoke Control Plane and React Portal over Backstage

## Status
Accepted

## Context
Backstage is a widely used developer portal framework. However, for an agentic AI POC, Backstage introduces heavy Node.js backend dependencies, plugin version pinning overhead, opinionated software template engines that do not natively support asynchronous WIF callbacks or granular Firestore state machines, and unnecessary tenancy complexity.

## Decision
We choose a lightweight, bespoke FastAPI control plane coupled with a tailored React frontend.

## Consequences
- Clean, auditable, asynchronous state machine tailored specifically for GCP Agentic AI workflows.
- Lightweight Cloud Run deployment with zero unnecessary background worker overhead.
- Direct alignment with OWASP password security, WIF OIDC token validation, and Model Armor guardrails.
