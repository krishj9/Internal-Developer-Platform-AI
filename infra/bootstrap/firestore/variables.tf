variable "project_id" {
  type        = string
  description = "GCP Project ID"
}

variable "location_id" {
  type        = string
  default     = "nam5"
  description = "Firestore database multi-region/location (e.g. nam5, us-central1)"
}

variable "database_id" {
  type        = string
  default     = "(default)"
  description = "Firestore database ID"
}
