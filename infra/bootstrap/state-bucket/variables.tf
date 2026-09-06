variable "project_id" {
  type        = string
  description = "GCP Project ID"
}

variable "bucket_name" {
  type        = string
  description = "Name of the GCS bucket for Terraform state and dead-letter callbacks"
}

variable "location" {
  type        = string
  default     = "US"
  description = "GCS location"
}

variable "labels" {
  type        = map(string)
  default     = {}
  description = "Resource labels"
}
