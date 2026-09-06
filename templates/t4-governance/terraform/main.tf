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

# 1. Dedicated Runtime Service Account for Governance Operations
resource "google_service_account" "governance_sa" {
  account_id   = "sa-t4-${substr(replace(var.deployment_id, "-", ""), 0, 20)}"
  display_name = "IDP T4 Governance SA for ${var.policy_name}"
  project      = var.project_id
  description  = "Dedicated identity for Governance & Monitoring operations ${var.deployment_id}"
}

# Scoped Monitoring & Logging permissions
resource "google_project_iam_member" "governance_monitoring" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.governance_sa.email}"
}

resource "google_project_iam_member" "governance_logging" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.governance_sa.email}"
}

# 2. Governed Metadata & Labels
locals {
  governed_labels = merge(var.labels, {
    managed_by       = "idp-platform"
    template_id      = "t4-governance"
    template_version = "2-0-0"
    deployment_id    = var.deployment_id
    workspace        = var.workspace
    environment      = var.environment
    owner            = var.owner
  })
}

# 3. Cloud Monitoring Alert Policy for Workload Health & Error Rates
resource "google_monitoring_alert_policy" "high_error_rate" {
  display_name = "IDP [${var.environment}] High Error Rate Alert - ${var.policy_name}"
  project      = var.project_id
  combiner     = "OR"
  user_labels  = local.governed_labels

  conditions {
    display_name = "Workload 5xx Error Rate > 5%"
    condition_threshold {
      filter          = "resource.type = \"cloud_run_revision\" AND metric.type = \"run.googleapis.com/request_count\" AND metric.labels.response_code_class = \"5xx\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 5.0
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }

  documentation {
    content   = "High error rate detected for governed AI workload. Investigate application logs and readiness."
    mime_type = "text/markdown"
  }
}
