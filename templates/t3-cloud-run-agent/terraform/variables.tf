variable "project_id" {
  type        = string
  description = "GCP Project ID"
}

variable "region" {
  type        = string
  default     = "us-central1"
  description = "GCP Region for Cloud Run deployment"
}

variable "deployment_id" {
  type        = string
  description = "Unique IDP deployment identifier (e.g. dep-abc12345)"
}

variable "service_name" {
  type        = string
  description = "Name of the Cloud Run agent service"
}

variable "container_image" {
  type        = string
  default     = "us-central1-docker.pkg.dev/idp-poc-dev/idp-images/t3-agent:v2.0.0"
  description = "Container image URI for Cloud Run service"
}

variable "model_name" {
  type        = string
  default     = "gemini-2.5-flash"
  description = "Vertex AI foundation model"
}

variable "cpu" {
  type        = string
  default     = "1"
  description = "CPU limits (e.g. 1, 2)"
}

variable "memory" {
  type        = string
  default     = "512Mi"
  description = "Memory limits (e.g. 512Mi, 1Gi, 2Gi)"
}

variable "max_instances" {
  type        = number
  default     = 2
  description = "Maximum instance count"
}

variable "timeout_seconds" {
  type        = number
  default     = 60
  description = "Request timeout in seconds"
}

variable "concurrency" {
  type        = number
  default     = 80
  description = "Concurrency per container instance"
}

variable "environment" {
  type        = string
  default     = "dev"
  description = "Environment identifier"
}

variable "workspace" {
  type        = string
  default     = "ws-dev"
  description = "IDP Workspace"
}

variable "owner" {
  type        = string
  default     = "platform-admin"
  description = "Owner of the deployment"
}

variable "labels" {
  type        = map(string)
  default     = {}
  description = "Governed platform labels"
}
