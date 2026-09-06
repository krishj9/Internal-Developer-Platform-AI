# T4 Governance & Operational Controls Template

Governed Model Armor guardrails, Cloud Monitoring alerts, and automated TTL lifecycle policies.

## Capabilities

- **Model Armor Guardrails**: Screening at Prompt, Tool Input, Retrieved Content, and Model Output points with `block`, `redact`, or `allow_with_audit` actions.
- **Cloud Monitoring**: Configures Alert Policies for workload health, error rate anomalies, and readiness failures.
- **Cost & Budget Controls**: Enforces template-level model constraints, monthly spend threshold alerts, and cost-center attribution.
- **TTL Lifecycle & Orphan Cleanup**: Default 7-day TTL for dev deployments with automated detection and cleanup.

## Lifecycle Operations

- **Create**: Provisions dedicated service account, IAM bindings, Cloud Monitoring alert policies, and registers Model Armor screening rules.
- **Readiness**: Validates guardrail filter evaluation and alert policy configuration.
- **Destroy**: Deletes alert policies, service accounts, and removes associated governance bindings.
