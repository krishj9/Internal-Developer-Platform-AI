variable "project_id" {
  type        = string
  description = "GCP Project ID"
}

variable "region" {
  type        = string
  default     = "us-central1"
  description = "GCP Region for Monitoring configuration"
}

variable "deployment_id" {
  type        = string
  description = "Unique IDP deployment identifier (e.g. dep-abc12345)"
}

variable "policy_name" {
  type        = string
  description = "Name of the governance policy"
}

variable "model_armor_mode" {
  type        = string
  default     = "block"
  description = "Model Armor filter action (block, redact, allow_with_audit)"
}

variable "monthly_budget_usd" {
  type        = number
  default     = 100
  description = "Monthly spend threshold in USD"
}

variable "ttl_days" {
  type        = number
  default     = 7
  description = "Time to live in days for development workloads"
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
