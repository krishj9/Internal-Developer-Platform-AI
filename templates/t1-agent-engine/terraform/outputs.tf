output "deployment_id" {
  value       = var.deployment_id
  description = "IDP deployment identifier"
}

output "agent_name" {
  value       = var.agent_name
  description = "Logical name of the agent"
}

output "runtime_sa_email" {
  value       = google_service_account.agent_runtime.email
  description = "Dedicated service account email for runtime invocation"
}

output "model_name" {
  value       = var.model_name
  description = "Configured foundation model"
}

output "region" {
  value       = var.region
  description = "GCP deployment region"
}

output "staging_bucket" {
  value       = google_storage_bucket.agent_artifacts.name
  description = "Dedicated GCS staging & artifact storage bucket with lifecycle TTL"
}

output "tool_secret_id" {
  value       = google_secret_manager_secret.agent_tool_secrets.secret_id
  description = "Dedicated Secret Manager secret container for agent tool credentials"
}

output "alert_policy_id" {
  value       = google_monitoring_alert_policy.agent_error_alert.name
  description = "Cloud Monitoring alert policy for agent error rate"
}

output "status" {
  value       = "PROVISIONED"
  description = "Provisioning status"
}
