terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# 1. Dedicated Runtime Service Account for T1 Workload Isolation
resource "google_service_account" "agent_runtime" {
  account_id   = "sa-t1-${substr(replace(var.deployment_id, "-", ""), 0, 20)}"
  display_name = "IDP T1 Runtime SA for ${var.agent_name}"
  project      = var.project_id
  description  = "Dedicated runtime identity for Agent Engine deployment ${var.deployment_id}"
}

# Scoped Vertex AI invocation permission for the runtime SA
resource "google_project_iam_member" "runtime_vertex_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.agent_runtime.email}"
}

# Scoped Logging permission for runtime traces
resource "google_project_iam_member" "runtime_logging" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.agent_runtime.email}"
}

# 2. Governed Metadata & Labels
locals {
  clean_dep_id = lower(replace(var.deployment_id, "_", "-"))
  governed_labels = merge(var.labels, {
    managed_by       = "idp-platform"
    template_id      = "t1-agent-engine"
    template_version = "2-0-0"
    deployment_id    = var.deployment_id
    workspace        = var.workspace
    environment      = var.environment
    owner            = var.owner
  })
}

# 3. Dedicated Governed GCS Staging & Artifact Bucket
resource "google_storage_bucket" "agent_artifacts" {
  name                        = "idp-t1-${var.project_id}-${substr(local.clean_dep_id, 0, 20)}"
  location                    = var.region
  project                     = var.project_id
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = 7 # Automatically clean up staging artifacts after 7 days
    }
  }

  labels = local.governed_labels
}

# Grant objectAdmin on dedicated staging bucket to runtime SA
resource "google_storage_bucket_iam_member" "runtime_bucket_admin" {
  bucket = google_storage_bucket.agent_artifacts.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.agent_runtime.email}"
}

# 4. Dedicated Tool Secrets Container (Secret Manager)
resource "google_secret_manager_secret" "agent_tool_secrets" {
  secret_id = "idp-tools-${substr(replace(var.deployment_id, "-", ""), 0, 20)}"
  project   = var.project_id

  replication {
    auto {}
  }

  labels = local.governed_labels
}

# Grant secretAccessor only to agent runtime SA
resource "google_secret_manager_secret_iam_member" "runtime_secret_accessor" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.agent_tool_secrets.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.agent_runtime.email}"
}

# 5. Cloud Monitoring Alert Policy for Agent Execution & Errors
resource "google_monitoring_alert_policy" "agent_error_alert" {
  display_name = "IDP [${var.environment}] Agent Error Alert - ${var.agent_name}"
  project      = var.project_id
  combiner     = "OR"
  user_labels  = local.governed_labels

  conditions {
    display_name = "Agent Unhandled Error Rate > 5%"
    condition_threshold {
      filter          = "resource.type = \"aiplatform.googleapis.com/ReasoningEngine\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 5.0
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }
}
