output "jwt_signing_key_secret_id" {
  value       = google_secret_manager_secret.jwt_signing_key.secret_id
  description = "Secret ID for JWT signing key container"
}

output "github_dispatch_token_secret_id" {
  value       = google_secret_manager_secret.github_dispatch_token.secret_id
  description = "Secret ID for GitHub workflow dispatch token container"
}
