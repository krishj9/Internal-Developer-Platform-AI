variable "project_id" {
  type        = string
  description = "GCP Project ID"
}

variable "region" {
  type        = string
  default     = "us-central1"
  description = "GCP Region for Agent Engine deployment"
}

variable "deployment_id" {
  type        = string
  description = "Unique IDP deployment identifier (e.g. dep-abc12345)"
}

variable "agent_name" {
  type        = string
  description = "Name of the agent"
}

variable "model_name" {
  type        = string
  default     = "gemini-2.5-flash"
  description = "Vertex AI foundation model"
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
