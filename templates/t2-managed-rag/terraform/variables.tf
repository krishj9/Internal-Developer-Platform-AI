variable "project_id" {
  type        = string
  description = "GCP Project ID"
}

variable "region" {
  type        = string
  default     = "us-central1"
  description = "GCP Region for Vertex AI RAG deployment"
}

variable "deployment_id" {
  type        = string
  description = "Unique IDP deployment identifier (e.g. dep-abc12345)"
}

variable "corpus_name" {
  type        = string
  description = "Logical identifier for the Vertex AI RAG corpus"
}

variable "embedding_model" {
  type        = string
  default     = "text-embedding-004"
  description = "Approved embedding model for vector index"
}

variable "chunk_size" {
  type        = number
  default     = 512
  description = "Token chunk size for document chunking"
}

variable "chunk_overlap" {
  type        = number
  default     = 100
  description = "Chunk overlap size in tokens"
}

variable "source_gcs_prefix" {
  type        = string
  default     = ""
  description = "Bounded GCS URI prefix containing documents to ingest"
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
