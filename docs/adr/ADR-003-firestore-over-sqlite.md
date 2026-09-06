# ADR-003: Firestore Native Mode over SQLite or Cloud SQL

## Status
Accepted

## Context
The IDP control plane requires a serverless, horizontally scalable, ACID-compliant database to track user profiles, templates, asynchronous request records, deployment locking, and append-only audit and callback ledgers.

## Decision
We choose Google Cloud Firestore Native Mode over SQLite (which cannot scale across stateless Cloud Run instances) and Cloud SQL (which introduces VPC peering overhead, connection pools, and high baseline costs for POC).

## Consequences
- Serverless pricing, native document model matching Pydantic schemas, and built-in atomic transaction support for deployment locks and idempotency keys.
