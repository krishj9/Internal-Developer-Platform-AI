resource "google_secret_manager_secret" "jwt_signing_key" {
  secret_id = "idp-jwt-signing-key"
  project   = var.project_id

  replication {
    auto {}
  }

  labels = merge(var.labels, {
    managed_by = "idp-platform"
    purpose    = "jwt-auth"
  })
}

resource "google_secret_manager_secret" "github_dispatch_token" {
  secret_id = "idp-github-dispatch-token"
  project   = var.project_id

  replication {
    auto {}
  }

  labels = merge(var.labels, {
    managed_by = "idp-platform"
    purpose    = "github-dispatch"
  })
}

# Resource-scoped secretAccessor IAM bindings for API runtime SA only
resource "google_secret_manager_secret_iam_member" "api_jwt_accessor" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.jwt_signing_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.api_runtime_sa_email}"
}

resource "google_secret_manager_secret_iam_member" "api_dispatch_accessor" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.github_dispatch_token.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.api_runtime_sa_email}"
}
