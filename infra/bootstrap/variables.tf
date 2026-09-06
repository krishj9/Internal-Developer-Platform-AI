variable "project_id" {
  type        = string
  description = "GCP Project ID for IDP bootstrap"
}

variable "region" {
  type        = string
  default     = "us-central1"
  description = "Default GCP Region"
}

variable "environment" {
  type        = string
  default     = "dev"
  description = "Environment name (dev, staging, prod)"
}

variable "github_repository" {
  type        = string
  description = "GitHub repository for Actions WIF trust (e.g. 'org-name/repo-name')"
}

variable "state_bucket_name" {
  type        = string
  description = "Globally unique name for the Terraform state GCS bucket"
}

variable "firestore_location_id" {
  type        = string
  default     = "nam5"
  description = "Firestore database multi-region / location"
}

variable "firestore_database_id" {
  type        = string
  default     = "idp-db"
  description = "Firestore database ID (allows named databases when default is in Datastore mode)"
}

variable "labels" {
  type = map(string)
  default = {
    managed_by = "idp-platform"
    tier       = "bootstrap"
  }
  description = "Base labels applied to all resources"
}
