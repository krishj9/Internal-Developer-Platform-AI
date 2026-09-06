variable "project_id" {
  type        = string
  description = "GCP Project ID"
}

variable "state_bucket_name" {
  type        = string
  description = "GCS State Bucket name to scope pipeline state access"
}

variable "environment" {
  type        = string
  default     = "dev"
  description = "Environment identifier"
}
