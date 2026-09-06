variable "project_id" {
  type        = string
  description = "GCP Project ID"
}

variable "api_runtime_sa_email" {
  type        = string
  description = "Email of the API runtime service account to grant secret accessor access"
}

variable "labels" {
  type        = map(string)
  default     = {}
  description = "Resource labels"
}
