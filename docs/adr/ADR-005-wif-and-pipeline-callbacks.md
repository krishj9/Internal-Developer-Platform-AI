# ADR-005: Workload Identity Federation (WIF) and Parameter-Bound Pipeline Callbacks

## Status
Accepted

## Context
Deploying infrastructure via CI/CD traditionally risked secret leakage through long-lived service account JSON keys. Furthermore, asynchronous pipeline state updates require strict authenticity verification to prevent spoofing.

## Decision
All GitHub Actions runners authenticate to GCP via OIDC tokens exchanged with a Workload Identity Pool Provider. All pipeline callbacks to the control plane present a Google OIDC ID token matching the pipeline service account identity, accompanied by monotonic sequence counters and SHA-256 payload digests.

## Consequences
- Zero service account JSON keys exist anywhere in the platform.
- Rejection of out-of-order, stale, or forged execution callbacks.
