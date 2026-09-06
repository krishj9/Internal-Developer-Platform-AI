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

# 1. Dedicated Runtime Service Account for T3 Workload Isolation
resource "google_service_account" "agent_runtime" {
  account_id   = "sa-t3-${substr(replace(var.deployment_id, "-", ""), 0, 20)}"
  display_name = "IDP T3 Runtime SA for ${var.service_name}"
  project      = var.project_id
  description  = "Dedicated runtime identity for Cloud Run agent deployment ${var.deployment_id}"
}

# Scoped Vertex AI invocation permission for foundation model reasoning
resource "google_project_iam_member" "runtime_vertex_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.agent_runtime.email}"
}

# Scoped Logging permission for structured observability
resource "google_project_iam_member" "runtime_logging" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.agent_runtime.email}"
}

# 2. Governed Metadata & Labels
locals {
  governed_labels = merge(var.labels, {
    managed_by       = "idp-platform"
    template_id      = "t3-cloud-run-agent"
    template_version = "2-0-0"
    deployment_id    = var.deployment_id
    workspace        = var.workspace
    environment      = var.environment
    owner            = var.owner
  })
}

# 3. Cloud Run v2 Service Definition
resource "google_cloud_run_v2_service" "agent_service" {
  name     = "cr-${var.service_name}-${var.environment}"
  location = var.region
  project  = var.project_id
  labels   = local.governed_labels

  template {
    service_account                  = google_service_account.agent_runtime.email
    labels                           = local.governed_labels
    timeout                          = "${var.timeout_seconds}s"
    max_instance_request_concurrency = var.concurrency

    scaling {
      min_instance_count = 0
      max_instance_count = var.max_instances
    }

    containers {
      image = var.container_image

      resources {
        limits = {
          cpu    = var.cpu
          memory = var.memory
        }
      }

      env {
        name  = "AGENT_MODEL_NAME"
        value = var.model_name
      }
      env {
        name  = "DEPLOYMENT_ID"
        value = var.deployment_id
      }
      env {
        name  = "WORKSPACE"
        value = var.workspace
      }
      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }

      ports {
        container_port = 8080
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}
