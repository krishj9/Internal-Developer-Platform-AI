# ADR-004: Argon2id Password Hashing and 60-Minute JWT Bearer Tokens

## Status
Accepted

## Context
For the POC phase, enterprise SSO / SAML integrations are out of scope. We require a robust, self-contained authentication mechanism that adheres strictly to modern cryptographic standards.

## Decision
We implement Argon2id password hashing (memory cost 65536 KiB, time cost 3, parallelism 4) and sign 60-minute JWT bearer tokens using a symmetric secret key stored securely in Google Secret Manager (`idp-jwt-signing-key`).

## Consequences
- High resistance against GPU/ASIC brute-force attacks.
- Stateless, standard bearer token validation on Cloud Run.
- Zero credential leakage in source control.
