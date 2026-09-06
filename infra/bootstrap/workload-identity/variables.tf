variable "project_id" {
  type        = string
  description = "GCP Project ID"
}

variable "github_repository" {
  type        = string
  description = "GitHub repository in format 'org/repo' (e.g. 'my-org/idp-platform')"
}

variable "pipeline_sa_email" {
  type        = string
  description = "Pipeline service account email to bind for GitHub Actions WIF impersonation"
}

variable "pool_id" {
  type        = string
  default     = "idp-github-pool"
  description = "Workload Identity Pool ID"
}

variable "provider_id" {
  type        = string
  default     = "idp-github-provider"
  description = "Workload Identity Provider ID"
}
