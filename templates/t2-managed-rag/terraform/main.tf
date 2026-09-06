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

# 1. Dedicated Runtime Service Account for T2 Managed RAG Workload Isolation
resource "google_service_account" "rag_runtime" {
  account_id   = "sa-t2-${substr(replace(var.deployment_id, "-", ""), 0, 20)}"
  display_name = "IDP T2 Runtime SA for ${var.corpus_name}"
  project      = var.project_id
  description  = "Dedicated runtime identity for Vertex AI Managed RAG deployment ${var.deployment_id}"
}

# Scoped Vertex AI permission for embeddings and corpus operations
resource "google_project_iam_member" "runtime_vertex_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.rag_runtime.email}"
}

# Scoped GCS read permission for bounded document ingestion
resource "google_project_iam_member" "runtime_storage_viewer" {
  project = var.project_id
  role    = "roles/storage.objectViewer"
  member  = "serviceAccount:${google_service_account.rag_runtime.email}"
}

# Scoped Logging permission for observability
resource "google_project_iam_member" "runtime_logging" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.rag_runtime.email}"
}

# 2. Governed Metadata & Labels
locals {
  governed_labels = merge(var.labels, {
    managed_by       = "idp-platform"
    template_id      = "t2-managed-rag"
    template_version = "2-0-0"
    deployment_id    = var.deployment_id
    workspace        = var.workspace
    environment      = var.environment
    owner            = var.owner
  })
}
