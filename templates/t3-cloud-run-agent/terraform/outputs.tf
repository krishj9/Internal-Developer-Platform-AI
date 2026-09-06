output "deployment_id" {
  value       = var.deployment_id
  description = "IDP deployment identifier"
}

output "service_name" {
  value       = var.service_name
  description = "Logical name of the Cloud Run agent service"
}

output "service_url" {
  value       = google_cloud_run_v2_service.agent_service.uri
  description = "HTTPS endpoint URI for the Cloud Run service"
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

output "status" {
  value       = "PROVISIONED"
  description = "Provisioning status"
}
