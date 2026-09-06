output "state_bucket_name" {
  value       = module.state_bucket.bucket_name
  description = "Terraform remote state and dead-letter bucket"
}

output "firestore_database_name" {
  value       = module.firestore.database_name
  description = "Firestore Native database name"
}

output "api_runtime_sa_email" {
  value       = module.service_accounts.api_runtime_sa_email
  description = "API runtime service account email"
}

output "pipeline_t1_dev_sa_email" {
  value       = module.service_accounts.pipeline_t1_dev_sa_email
  description = "T1 dev pipeline service account email"
}

output "workload_identity_provider_name" {
  value       = module.workload_identity.workload_identity_provider_name
  description = "Full resource name of the WIF Provider for GitHub Actions OIDC"
}

output "jwt_signing_key_secret_id" {
  value       = module.secret_manager.jwt_signing_key_secret_id
  description = "Secret Manager secret ID for JWT signing key"
}

output "github_dispatch_token_secret_id" {
  value       = module.secret_manager.github_dispatch_token_secret_id
  description = "Secret Manager secret ID for GitHub dispatch token"
}
