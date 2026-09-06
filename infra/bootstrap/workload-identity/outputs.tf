output "workload_identity_pool_name" {
  value       = google_iam_workload_identity_pool.github_pool.name
  description = "The full resource name of the Workload Identity Pool"
}

output "workload_identity_provider_name" {
  value       = google_iam_workload_identity_pool_provider.github_provider.name
  description = "The full resource name of the Workload Identity Provider for GitHub Actions"
}
