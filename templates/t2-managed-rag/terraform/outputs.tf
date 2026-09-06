output "deployment_id" {
  value       = var.deployment_id
  description = "IDP deployment identifier"
}

output "corpus_name" {
  value       = var.corpus_name
  description = "Logical name of the Vertex AI RAG corpus"
}

output "corpus_resource_name" {
  value       = "projects/${var.project_id}/locations/${var.region}/ragCorpora/${var.corpus_name}"
  description = "GCP resource name for the Vertex AI RAG corpus"
}

output "embedding_model" {
  value       = var.embedding_model
  description = "Configured embedding model"
}

output "region" {
  value       = var.region
  description = "GCP deployment region"
}

output "runtime_sa_email" {
  value       = google_service_account.rag_runtime.email
  description = "Dedicated service account email for runtime invocation"
}

output "ingestion_status" {
  value       = "INITIALIZED"
  description = "Initial ingestion status"
}

output "status" {
  value       = "PROVISIONED"
  description = "Provisioning status"
}
