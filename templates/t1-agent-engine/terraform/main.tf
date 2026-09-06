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
