# 1. API Runtime Service Account
resource "google_service_account" "api_runtime" {
  account_id   = "idp-api-runtime"
  display_name = "IDP API Runtime Service Account"
  project      = var.project_id
  description  = "Identity for FastAPI control plane running on Cloud Run"
}

# Grant Firestore data plane access to API runtime SA
resource "google_project_iam_member" "api_firestore_user" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.api_runtime.email}"
}

# Grant Cloud Logging write permissions to API runtime SA
resource "google_project_iam_member" "api_logging" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.api_runtime.email}"
}

# Grant Pub/Sub publisher permissions to API runtime SA
resource "google_project_iam_member" "api_pubsub" {
  project = var.project_id
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${google_service_account.api_runtime.email}"
}


# 2. T1 Development Pipeline Service Account
resource "google_service_account" "pipeline_t1_dev" {
  account_id   = "idp-pipeline-t1-dev"
  display_name = "IDP T1 Dev Pipeline Service Account"
  project      = var.project_id
  description  = "Identity for GitHub Actions WIF to provision/destroy T1 Agent Engine workloads"
}

# Grant bucket-scoped storage object admin on state bucket
resource "google_storage_bucket_iam_member" "pipeline_t1_state_access" {
  bucket = var.state_bucket_name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.pipeline_t1_dev.email}"
}

# Scoped Vertex AI user permissions for Agent Engine provisioning
resource "google_project_iam_member" "pipeline_t1_aiplatform" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.pipeline_t1_dev.email}"
}

# Logging writer for pipeline steps
resource "google_project_iam_member" "pipeline_t1_logging" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.pipeline_t1_dev.email}"
}
