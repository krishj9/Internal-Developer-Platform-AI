resource "google_iam_workload_identity_pool" "github_pool" {
  workload_identity_pool_id = var.pool_id
  project                   = var.project_id
  display_name              = "IDP GitHub Actions Pool"
  description               = "WIF Pool for keyless GitHub Actions authentication"
  disabled                  = false
}

resource "google_iam_workload_identity_pool_provider" "github_provider" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github_pool.workload_identity_pool_id
  workload_identity_pool_provider_id = var.provider_id
  project                            = var.project_id
  display_name                       = "IDP GitHub Provider"
  description                        = "OIDC Provider for GitHub Actions"
  disabled                           = false

  attribute_mapping = {
    "google.subject"             = "assertion.sub"
    "attribute.actor"            = "assertion.actor"
    "attribute.repository"       = "assertion.repository"
    "attribute.repository_owner" = "assertion.repository_owner"
    "attribute.ref"              = "assertion.ref"
    "attribute.workflow"         = "assertion.workflow"
  }

  # Restrict token exchange strictly to the designated repository
  attribute_condition = "assertion.repository == '${var.github_repository}'"

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

# Bind pipeline service account impersonation to the specific repository principalSet
resource "google_service_account_iam_member" "wif_pipeline_impersonation" {
  service_account_id = "projects/${var.project_id}/serviceAccounts/${var.pipeline_sa_email}"
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github_pool.name}/attribute.repository/${var.github_repository}"
}
