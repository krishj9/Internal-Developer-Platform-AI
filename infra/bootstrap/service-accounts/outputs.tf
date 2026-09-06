output "api_runtime_sa_email" {
  value       = google_service_account.api_runtime.email
  description = "Email of the API runtime service account"
}

output "api_runtime_sa_id" {
  value       = google_service_account.api_runtime.name
  description = "Resource name ID of the API runtime service account"
}

output "pipeline_t1_dev_sa_email" {
  value       = google_service_account.pipeline_t1_dev.email
  description = "Email of the T1 dev pipeline service account"
}

output "pipeline_t1_dev_sa_id" {
  value       = google_service_account.pipeline_t1_dev.name
  description = "Resource name ID of the T1 dev pipeline service account"
}
