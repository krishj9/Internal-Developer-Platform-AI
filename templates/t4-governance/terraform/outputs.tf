output "deployment_id" {
  value       = var.deployment_id
  description = "IDP deployment identifier"
}

output "policy_name" {
  value       = var.policy_name
  description = "Configured governance policy name"
}

output "model_armor_mode" {
  value       = var.model_armor_mode
  description = "Configured Model Armor action"
}

output "alert_policy_id" {
  value       = google_monitoring_alert_policy.high_error_rate.name
  description = "Cloud Monitoring alert policy resource name"
}

output "ttl_days" {
  value       = var.ttl_days
  description = "Configured TTL policy in days"
}

output "status" {
  value       = "PROVISIONED"
  description = "Provisioning status"
}
