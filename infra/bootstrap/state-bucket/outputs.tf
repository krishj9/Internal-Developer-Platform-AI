output "bucket_name" {
  value       = google_storage_bucket.state_bucket.name
  description = "The name of the GCS state bucket"
}

output "bucket_url" {
  value       = google_storage_bucket.state_bucket.url
  description = "The URL of the GCS state bucket"
}
