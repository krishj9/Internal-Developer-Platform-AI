# ADR-006: Immutable Version-Pinned Templates and Pre-Activation Readiness Smoke Tests

## Status
Accepted

## Context
In agentic AI systems, successful infrastructure provisioning (e.g. creating a Cloud Run service or Vertex AI Agent Engine app) does not guarantee that the AI model or RAG corpus is operational, responsive, or authorized to invoke tools.

## Decision
All templates in `templates/` are immutable and tagged by release commit SHA. Workloads do not transition to `ACTIVE` until an automated readiness smoke test executes against the provisioned data plane (e.g. ADK agent query ping, RAG corpus retrieval verification, or HTTP healthz check).

## Consequences
- Prevents broken deployments from being registered as healthy.
- Guaranteed reproducibility of infrastructure releases across environments.
